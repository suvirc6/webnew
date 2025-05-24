import os
import tempfile
from typing import List, Dict
import re
import numpy as np

import fitz  # PyMuPDF
import markdown
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI

from prompts import prompts  # Your prompts dictionary

# --- Load environment variables ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = "financials"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}

openai_key = os.getenv("OPENAI_KEY")

# --- Initialize FastAPI app ---
app = FastAPI()
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- OpenAI client ---
client = OpenAI(api_key=openai_key)

# --- Config ---
COMPLETION_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K_CHUNKS = 5

# --- Store multiple uploaded files paths ---
uploaded_pdf_paths: List[str] = []

# --- Enhanced utility functions ---
def markdown_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables"])

def extract_pdf_text(pdf_path: str) -> List[Dict]:
    """Extracts text from each page along with page number and source. No OCR."""
    try:
        doc = fitz.open(pdf_path)
        pages_text = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages_text.append({
                "page_number": page_num + 1,
                "text": text.strip()
            })
        doc.close()
        return pages_text
    except Exception as e:
        print(f"Error extracting PDF text from {pdf_path}: {e}")
        return []

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.,;:!?()-]', ' ', text)
    return text.strip()

def create_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        chunk_info = {
            'text': clean_text(chunk_text),
            'start_word': i,
            'end_word': min(i + chunk_size, len(words)),
            'word_count': len(chunk_words),
            'chunk_id': len(chunks)
        }
        if len(chunk_text.strip()) > 50:
            chunks.append(chunk_info)
    return chunks



def get_embedding(text: str) -> np.ndarray:
    """Get OpenAI embedding for a text chunk"""
    try:
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"Embedding error: {e}")
        return np.zeros(1536)  # Fallback for embedding dimension

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two 1D numpy vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

def get_top_relevant_chunks(chunks: List[Dict], query: str, top_k: int = TOP_K_CHUNKS) -> List[Dict]:
    """Get top K most relevant chunks using OpenAI embeddings + cosine similarity"""
    if not chunks or not query:
        return []

    try:
        query_embedding = get_embedding(query)

        for chunk in chunks:
            if "embedding" not in chunk:
                chunk["embedding"] = get_embedding(chunk["text"])

        similarities = [cosine_similarity([query_embedding], [chunk["embedding"]])[0][0] for chunk in chunks]

        for i, sim in enumerate(similarities):
            chunks[i]["similarity_score"] = float(sim)

        top_chunks = sorted(chunks, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
        return top_chunks

    except Exception as e:
        print(f"Error computing embedding-based similarity: {e}")
        return chunks[:top_k]


def clean_latex(text: str) -> str:
    return (
        text.replace("\\[", "")
            .replace("\\]", "")
            .replace("\\(", "")
            .replace("\\)", "")
            .replace("$$", "")
            .replace("\\text{", "")
            .replace("}", "")
            .strip()
    )

def ask_openai_with_chunks(question: str, relevant_chunks: List[Dict], file_names: List[str]) -> str:
    """Enhanced OpenAI query with chunk-based context"""
    
    # Prepare context from top chunks
# Prepare context from top chunks
    context_parts = []
    for chunk in relevant_chunks[:TOP_K_CHUNKS]:
        doc = chunk.get("source", "UnknownDoc")
        page = chunk.get("page_number", "?")
        context_parts.append(
            f"[Source: {doc}, Page: {page}, Relevance: {chunk.get('similarity_score', 0):.3f}]\n{chunk['text']}\n"
        )
    
    context = "\n".join(context_parts)
    
    # Create file information
    file_info = f"Documents analyzed: {', '.join(file_names)}" if file_names else "Multiple documents"
    
    prompt = f"""You are a comprehensive financial and business analyst. You have access to content from multiple documents and need to provide a thorough analysis.

{file_info}

IMPORTANT INSTRUCTIONS:
1. Analyze information from ALL provided chunks
2. Look for patterns, comparisons, and insights across different sections
3. If comparing multiple companies, clearly distinguish between them
4. Provide specific examples and data points from the documents
5. Create a comprehensive summary that synthesizes information from all sources

Context (Top {len(relevant_chunks)} most relevant sections):
{context}

Question: {question}

Please provide a detailed analysis that:
- Uses information from multiple document sections
- Identifies key insights and patterns
- Provides specific data points and examples
- Offers comparative analysis if multiple entities are discussed
- Concludes with a comprehensive summary

Answer:"""

    response = client.chat.completions.create(
        model=COMPLETION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,  # Increased for comprehensive answers
    )
    
    raw_answer = clean_latex(response.choices[0].message.content.strip())
    
    # Convert markdown tables to html if detected
    if "|" in raw_answer and "-" in raw_answer:
        return markdown_to_html(raw_answer)
    return raw_answer

import concurrent.futures

def analyze_documents_enhanced(pdf_paths: List[str], question: str, file_names: List[str] = None):
    steps = ["📄 Extracting text from all PDFs..."]
    
    # Extract text from all documents
    all_documents_text = []
    for i, path in enumerate(pdf_paths):
        pages = extract_pdf_text(path)
        all_documents_text.append({
            'pages': pages,
            'source': f"Document_{i+1}",
            'path': path
        })

    # Step 1: Create chunks concurrently
    all_chunks = []

    def process_page(page, source):
        page_chunks = create_chunks(page["text"])
        for chunk in page_chunks:
            chunk["page_number"] = page["page_number"]
            chunk["source"] = source
        return page_chunks

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for doc in all_documents_text:
            source = doc["source"]
            for page in doc["pages"]:
                futures.append(executor.submit(process_page, page, source))
        for future in concurrent.futures.as_completed(futures):
            page_chunks = future.result()
            all_chunks.extend(page_chunks)

    steps.append(f"🧠 Calculating embeddings for {len(all_chunks)} chunks...")

    # Step 2: Compute embeddings concurrently for all chunks
    def embed_chunk(chunk):
        chunk["embedding"] = get_embedding(chunk["text"])
        return chunk

    with concurrent.futures.ThreadPoolExecutor() as executor:
        embed_futures = [executor.submit(embed_chunk, chunk) for chunk in all_chunks]
        # Wait for all to complete and collect results in the same order as all_chunks
        all_chunks = [f.result() for f in concurrent.futures.as_completed(embed_futures)]

    steps.append(f"🔍 Finding top {TOP_K_CHUNKS} most relevant chunks from {len(all_chunks)} total chunks...")

    # Step 3: Get most relevant chunks based on query embedding and chunk embeddings
    try:
        query_embedding = get_embedding(question)
        # Compute similarity for each chunk (embedding must exist now)
        for chunk in all_chunks:
            chunk["similarity_score"] = float(cosine_similarity([query_embedding], [chunk["embedding"]])[0][0])
        relevant_chunks = sorted(all_chunks, key=lambda x: x["similarity_score"], reverse=True)[:TOP_K_CHUNKS]
    except Exception as e:
        print(f"Error computing similarity: {e}")
        relevant_chunks = all_chunks[:TOP_K_CHUNKS]

    steps.append("🤖 Generating comprehensive analysis...")

    answer = ask_openai_with_chunks(question, relevant_chunks, file_names or [])

    chunk_info = f"📊 Analysis based on {len(relevant_chunks)} most relevant sections"
    if relevant_chunks:
        avg_similarity = sum(chunk.get('similarity_score', 0) for chunk in relevant_chunks) / len(relevant_chunks)
        chunk_info += f" (avg relevance: {avg_similarity:.3f})"
    steps.append(chunk_info)

    return {
        "steps": steps,
        "answer": answer,
        "chunks_used": len(relevant_chunks),
        "total_chunks": len(all_chunks)
    }

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "prompts": prompts})

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    # Clear old uploaded files paths and delete temp files if needed
    for old_path in uploaded_pdf_paths:
        try:
            os.unlink(old_path)
        except Exception:
            pass
    uploaded_pdf_paths.clear()

    # Save new uploaded files to temp files
    file_names = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(status_code=400, content={"error": f"Invalid file type: {file.filename}"})
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        content = await file.read()
        with open(temp_file.name, "wb") as f:
            f.write(content)
        uploaded_pdf_paths.append(temp_file.name)
        file_names.append(file.filename)

    return {
        "filenames": file_names, 
        "status": "Files uploaded successfully",
        "file_count": len(files)
    }

@app.post("/analyze")
async def analyze(prompt_key: str = Form(...), custom_query: str = Form(None)):
    if not uploaded_pdf_paths:
        return JSONResponse(status_code=400, content={"error": "No documents uploaded yet"})

    question = custom_query.strip() if custom_query else prompts.get(prompt_key)
    if not question:
        return JSONResponse(status_code=400, content={"error": "Invalid or missing query"})

    # Get file names for context (simplified version)
    file_names = [f"Document_{i+1}" for i in range(len(uploaded_pdf_paths))]
    
    result = analyze_documents_enhanced(uploaded_pdf_paths, question, file_names)
    return {
        "answer": result["answer"], 
        "steps": result["steps"],
        "chunks_info": {
            "chunks_used": result["chunks_used"],
            "total_chunks": result["total_chunks"]
        }
    }

@app.post("/analyze_custom")
async def analyze_custom(custom_query: str = Form(...)):
    if not uploaded_pdf_paths:
        return JSONResponse(status_code=400, content={"error": "No documents uploaded yet"})
    if not custom_query.strip():
        return JSONResponse(status_code=400, content={"error": "Custom query cannot be empty"})

    # Get file names for context
    file_names = [f"Document_{i+1}" for i in range(len(uploaded_pdf_paths))]
    
    result = analyze_documents_enhanced(uploaded_pdf_paths, custom_query.strip(), file_names)
    return {
        "answer": result["answer"], 
        "steps": result["steps"],
        "chunks_info": {
            "chunks_used": result["chunks_used"],
            "total_chunks": result["total_chunks"]
        }
    }

@app.get("/scrape_nse")
async def scrape_nse(tickers: str = Query(..., description="Comma separated tickers")):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return JSONResponse(status_code=400, content={"error": "No valid tickers provided"})

    in_clause = ",".join(ticker_list)
    supabase_query_url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?ticker=in.({in_clause})"

    response = requests.get(supabase_query_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch from Supabase", "details": response.text},
        )

# --- Additional utility endpoint ---
@app.get("/chunk_stats")
async def get_chunk_statistics(query: str = Query(..., description="Query to rank relevance")):
    """Get statistics about uploaded documents and top relevant chunks"""
    if not uploaded_pdf_paths:
        return JSONResponse(status_code=400, content={"error": "No documents uploaded yet"})
    
    # Step 1: Extract and chunk all documents
    all_chunks = []
    for i, path in enumerate(uploaded_pdf_paths):
        doc_text = extract_pdf_text(path)
        doc_chunks = create_chunks(doc_text)
        for chunk in doc_chunks:
            chunk['source'] = f"Document_{i+1}"
        all_chunks.extend(doc_chunks)

    # Step 2: Compute top-K relevant chunks
    top_chunks = get_top_relevant_chunks(all_chunks, query, TOP_K_CHUNKS)

    if not top_chunks:
        return JSONResponse(status_code=500, content={"error": "Failed to compute top chunks"})

    return {
        "total_documents": len(uploaded_pdf_paths),
        "total_chunks": len(all_chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "top_k_chunks": TOP_K_CHUNKS,
        "first_top_chunk": {
            "chunk_id": top_chunks[0]["chunk_id"],
            "similarity_score": top_chunks[0]["similarity_score"],
            "source": top_chunks[0]["source"],
            "text": top_chunks[0]["text"][:500]  # Preview first 500 chars
        },
        "last_top_chunk": {
            "chunk_id": top_chunks[-1]["chunk_id"],
            "similarity_score": top_chunks[-1]["similarity_score"],
            "source": top_chunks[-1]["source"],
            "text": top_chunks[-1]["text"][:500]
        }
    }
