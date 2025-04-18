import os
import fitz  # PyMuPDF
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from openai import OpenAI
from dotenv import load_dotenv
from prompts import prompts
import tempfile

# Load environment variables
load_dotenv()

app = FastAPI()

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# OpenAI client setup
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Config
EMBEDDING_MODEL = "text-embedding-3-small"
COMPLETION_MODEL = "gpt-4o-mini" 
CHUNK_SIZE = 500  # tokens-ish
CHUNK_OVERLAP = 50

# Global variable to store the current PDF path
current_pdf_path = None

# --- Step 1: PDF Parsing with fitz ---
def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = "\n\n".join([page.get_text() for page in doc])
    doc.close()
    return full_text

# --- Step 2: Chunking logic with overlap ---
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# --- Step 3: Embed chunks ---
def get_embeddings(texts):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [np.array(e.embedding) for e in response.data]

# --- Step 4: Rank chunks by similarity to question ---
def rank_chunks_by_question(chunks, question, top_n=5):
    question_embedding = get_embeddings([question])[0]
    chunk_embeddings = get_embeddings(chunks)

    similarities = [np.dot(chunk_emb, question_embedding) /
                    (np.linalg.norm(chunk_emb) * np.linalg.norm(question_embedding))
                    for chunk_emb in chunk_embeddings]

    top_indices = np.argsort(similarities)[::-1][:top_n]
    return [chunks[i] for i in top_indices]

# --- Step 5: Ask OpenAI with top chunks ---
def ask_openai(question, context):
    prompt = f"""You are a helpful analyst. Based on the context below, answer the question accurately.

Context:
{context}

Question: {question}
Answer:"""
    response = client.chat.completions.create(
        model=COMPLETION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# --- Analysis function ---
def analyze_document(pdf_path, question):
    steps = []
    
    steps.append("📄 Extracting text from PDF...")
    text = extract_pdf_text(pdf_path)
    
    steps.append("✂️ Chunking text...")
    chunks = chunk_text(text)

    steps.append("🧠 Retrieving relevant chunks with embeddings...")
    top_chunks = rank_chunks_by_question(chunks, question, top_n=4)

    steps.append("🤖 Asking OpenAI...")
    combined_context = "\n\n".join(top_chunks)
    answer = ask_openai(question, combined_context)

    return {
        "steps": steps,
        "answer": answer
    }

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "prompts": prompts})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global current_pdf_path
    
    # Create a temporary file to store the uploaded PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file_path = temp_file.name
    
    # Write uploaded file to temp file
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())
    
    current_pdf_path = temp_file_path
    return {"filename": file.filename, "status": "File uploaded successfully"}

@app.post("/analyze")
async def analyze(prompt_key: str = Form(...), custom_query: str = Form(None)):
    global current_pdf_path
    
    if not current_pdf_path:
        return {"error": "No document uploaded yet"}
    
    # Use custom query if provided, otherwise use predefined prompt
    if custom_query and custom_query.strip():
        question = custom_query.strip()
    else:
        if prompt_key not in prompts:
            return {"error": "Invalid prompt key"}
        question = prompts[prompt_key]
    
    # Extract text from PDF
    text = extract_pdf_text(current_pdf_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Get top chunks
    top_chunks = rank_chunks_by_question(chunks, question, top_n=4)
    
    # Get answer from OpenAI
    combined_context = "\n\n".join(top_chunks)
    answer = ask_openai(question, combined_context)
    
    # Return only the answer, no steps
    return {"answer": answer}

@app.post("/analyze_custom")
async def analyze_custom(custom_query: str = Form(...)):
    global current_pdf_path
    
    if not current_pdf_path:
        return {"error": "No document uploaded yet"}
    
    if not custom_query or not custom_query.strip():
        return {"error": "Custom query cannot be empty"}
    
    # Extract text from PDF
    text = extract_pdf_text(current_pdf_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Get top chunks
    top_chunks = rank_chunks_by_question(chunks, custom_query, top_n=4)
    
    # Get answer from OpenAI
    combined_context = "\n\n".join(top_chunks)
    answer = ask_openai(custom_query, combined_context)
    
    # Return only the answer
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)