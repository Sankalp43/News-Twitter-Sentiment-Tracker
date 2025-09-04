# news_summary_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from newspaper import Article
from pathlib import Path
from typing import Tuple
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import asyncio
from tqdm import tqdm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()
SUMMARY_MODEL_NAME = "t5-base"
SUMMARY_MODEL_DIR = Path("models/summarizer_model")


def load_summarizer(model_name: str = SUMMARY_MODEL_NAME, model_dir: Path = SUMMARY_MODEL_DIR) -> Tuple:
    """Load or download the tokenizer and model for summarization."""
    logging.info(f"Loading summarizer model from {model_dir} or downloading {model_name} if not available...")

    if model_dir.exists():
        logging.info(f"Model directory {model_dir} found. Loading model from disk.")

        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
    else:
        logging.info(f"Model directory {model_dir} not found. Downloading model {model_name}.")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model_dir.mkdir(parents=True, exist_ok=True)
        tokenizer.save_pretrained(model_dir)
        model.save_pretrained(model_dir)
        logging.info(f"Model {model_name} downloaded and saved to {model_dir}.")

    model.eval()
    logging.info(f"Model {model_name} is ready for summarization.")

    return tokenizer, model

def extract_article_text(url: str) -> str:
    """Extract the main body text from a news article URL."""
    logging.info(f"Extracting article text from URL: {url}")

    article = Article(url)
    article.download()
    article.parse()
    return article.text.strip()


def summarize_text(text: str, tokenizer, model, max_input_length: int = 1024, max_output_length: int = 150) -> str:
    """Summarize a given text using the provided tokenizer and model."""
    logging.info(f"Starting summarization of extracted text. Text length: {len(text)} characters.")

    input_text = f"summarize: {text}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_input_length)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_output_length,
            do_sample=True,
            temperature=0.9,
            top_p=0.95
        )
    summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    logging.info(f"Summarization completed. Summary length: {len(summary)} characters.")

    return summary.strip()

class SummaryRequest(BaseModel):
    url: str

@app.post("/summarize")
async def summarize_article(request: SummaryRequest):
    """Endpoint to summarize a news article given its URL."""
    logging.info(f"Received request to summarize article at URL: {request.url}")
    try:
        text = extract_article_text(request.url)
        if not text:
            logging.error(f"Failed to extract text from {request.url}")
            return {"error": "Failed to extract article text"}
        tokenizer, model = load_summarizer()
        summary = await generate_summary(text , tokenizer, model)
        
        logging.info(f"Summary generated for {request.url}")
        return {"url": request.url, "summary": summary}
        
    except Exception as e:
        logging.error(f"Error summarizing {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_summary(text: str , tokenizer, model):
    """Async wrapper for summary generation"""
    logging.info(f"Offloading summarization to a background thread...")
    return await asyncio.to_thread(
        summarize_text, 
        text=text,
        tokenizer=tokenizer,
        model=model,
        max_input_length=1024,
        max_output_length=150
    )

# Keep existing utility functions (load_summarizer, extract_article_text, summarize_text)
