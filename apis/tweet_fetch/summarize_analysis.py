from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from pathlib import Path
from tqdm import tqdm

SUMMARY_MODEL_DIR = Path("models/summarizer_model")
# summary_model_name = "facebook/bart-large-cnn"  # Or try "google/flan-t5-base" for prompt-flexible
summary_model_name = "t5-base" # Or try "google/flan-t5-base" for prompt-flexible
def load_summarization_model():
    if SUMMARY_MODEL_DIR.exists():
        tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL_DIR)
        model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARY_MODEL_DIR)
    else:
        tokenizer = AutoTokenizer.from_pretrained(summary_model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(summary_model_name)
        SUMMARY_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        tokenizer.save_pretrained(SUMMARY_MODEL_DIR)
        model.save_pretrained(SUMMARY_MODEL_DIR)
    model.eval()
    return tokenizer, model

summarizer_tokenizer, summarizer_model = load_summarization_model()


def summarize_tweets(tweets, headline):
    # Take a sample subset (e.g., first 5 tweets)
    sample_tweets = tweets
    tweet_text_block = "\n".join(f"- {t}" for t in sample_tweets)

    # Prompt directly
    prompt = f"""
    You are a social media analyst.
    You will summarize the public's reaction based on a collection of tweets.
Headline: {headline}
TThese are public tweets discussing a news event.h
Sample Tweets:
{tweet_text_block}

Write an engaging and insightful paragraph summarizing how people are reacting emotionally and intellectually to this news. Mention overall sentiment, common themes, and any polarizing opinions.
"""

    print("📝 Generating summary...")
    inputs = summarizer_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        outputs = summarizer_model.generate(**inputs, max_new_tokens=150,do_sample=True, temperature=0.9, top_p=0.95)
        summary = summarizer_tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("✅ Summary generated.")
    # print(f"Summary: {summary}")    
    return summary.strip()
