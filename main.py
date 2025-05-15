import os
import subprocess
import tempfile
import numpy as np
import fitz  # PyMuPDF
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from prompts import prompts
import uvicorn
from fastapi import Query
from typing import List
from playwright.async_api import async_playwright

from fastapi import FastAPI, Query
import subprocess
import json



# --- Load environment variables ---
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

# --- Initialize FastAPI app ---
app = FastAPI()

# --- Set up directories ---
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# --- Mount static files directory for CSS, JS, etc. ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- OpenAI client setup ---
client = OpenAI(api_key=openai_key)

# --- Config ---
EMBEDDING_MODEL = "text-embedding-3-small"
COMPLETION_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 250
CHUNK_OVERLAP = 50

# --- Global PDF path tracker ---
current_pdf_path = None

# --- PDF Text Extraction ---
def extract_pdf_text(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        full_text = "\n\n".join([page.get_text() for page in doc])
        doc.close()
        if full_text.strip():
            return full_text
        raise ValueError("No text found in PDF.")
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

# --- Chunking Text ---
def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# --- Generate Embeddings ---
def get_embeddings(texts):
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [np.array(e.embedding) for e in response.data]

# --- Rank Chunks ---
def rank_chunks_by_question(chunks, question, top_n=5):
    question_embedding = get_embeddings([question])[0]
    chunk_embeddings = get_embeddings(chunks)
    similarities = [
        np.dot(chunk_emb, question_embedding) / 
        (np.linalg.norm(chunk_emb) * np.linalg.norm(question_embedding))
        for chunk_emb in chunk_embeddings
    ]
    top_indices = np.argsort(similarities)[::-1][:top_n]
    return [chunks[i] for i in top_indices]

# --- Clean LaTeX (optional post-processing) ---
def clean_latex(text):
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

# --- Query OpenAI ---
def ask_openai(question: str, context: str) -> str:
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
    return clean_latex(response.choices[0].message.content.strip())

# --- Analyze Document Pipeline ---
def analyze_document(pdf_path: str, question: str):
    steps = ["📄 Extracting text from PDF..."]
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

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "prompts": prompts})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global current_pdf_path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(temp_file.name, "wb") as f:
        f.write(await file.read())
    current_pdf_path = temp_file.name
    return {"filename": file.filename, "status": "File uploaded successfully"}

@app.post("/analyze")
async def analyze(prompt_key: str = Form(...), custom_query: str = Form(None)):
    global current_pdf_path
    if not current_pdf_path:
        return {"error": "No document uploaded yet"}

    question = custom_query.strip() if custom_query else prompts.get(prompt_key)
    if not question:
        return {"error": "Invalid or missing query"}

    text = extract_pdf_text(current_pdf_path)
    chunks = chunk_text(text)
    top_chunks = rank_chunks_by_question(chunks, question, top_n=4)
    answer = ask_openai(question, "\n\n".join(top_chunks))
    return {"answer": answer}

@app.post("/analyze_custom")
async def analyze_custom(custom_query: str = Form(...)):
    global current_pdf_path
    if not current_pdf_path:
        return {"error": "No document uploaded yet"}
    if not custom_query.strip():
        return {"error": "Custom query cannot be empty"}

    text = extract_pdf_text(current_pdf_path)
    chunks = chunk_text(text)
    top_chunks = rank_chunks_by_question(chunks, custom_query, top_n=4)
    answer = ask_openai(custom_query, "\n\n".join(top_chunks))
    return {"answer": answer}


@app.get("/scrape_nse")
async def scrape_nse(tickers: str = Query(..., description="Comma separated tickers")):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if not ticker_list:
        return JSONResponse(status_code=400, content={"error": "No valid tickers provided"})

    # Run Node.js scraper script with tickers as args
    try:
        result = subprocess.run(
            ["node", "scrape_nse.js", *ticker_list],
            capture_output=True,
            text=True,
            check=True,
            # cwd="path/to/your/js/script"  # Adjust this to your JS script folder
        )
        data = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": f"Scraper failed: {e.stderr}"})
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "Failed to parse scraper output"})


# # --- Run App ---
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


