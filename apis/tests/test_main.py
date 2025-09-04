import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import main_app
from requests import HTTPError

client = TestClient(main_app)

# --- Test root endpoint ---
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Combined API Server"}

# --- Test /summarize endpoint ---
@pytest.mark.asyncio
@patch("news_summary.news_summary_api.extract_article_text", return_value="Some article text")
@patch("news_summary.news_summary_api.load_summarizer", return_value=("mock_tokenizer", "mock_model"))
@patch("news_summary.news_summary_api.generate_summary", new_callable=AsyncMock)
def test_summarize_success(mock_generate, mock_loader, mock_extract):
    mock_generate.return_value = "Short summary"
    response = client.post("/news/summarize", json={"url": "http://example.com/article"})
    
    assert response.status_code == 200
    assert response.json() == {
        "url": "http://example.com/article",
        "summary": "Short summary"
    }

@pytest.mark.asyncio
@patch("news_summary.news_summary_api.extract_article_text", return_value=None)
def test_summarize_extract_fail(mock_extract):
    response = client.post("/news/summarize", json={"url": "http://example.com/article"})
    assert response.status_code == 200
    assert response.json() == {"error": "Failed to extract article text"}

@pytest.mark.asyncio
@patch("news_summary.news_summary_api.extract_article_text", side_effect=Exception("Something went wrong"))
def test_summarize_exception(mock_extract):
    response = client.post("/news/summarize", json={"url": "http://example.com/article"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Something went wrong"

# --- Test /tweets endpoint ---
@pytest.mark.asyncio
@patch("tweet_fetch.get_tweets_api.load_client")
@patch("tweet_fetch.get_tweets_api.process_tweets", new_callable=AsyncMock)
def test_tweets_success(mock_process, mock_client):
    mock_process.return_value = {
        "cleaned_tweets": ["tweet1", "tweet2"],
        "raw_stats": {"likes": 10, "replies": 2, "retweets": 1},
        "summary": "Summary of tweets"
    }
    response = client.post("/twitter/tweets", json={"title": "Python", "max_tweets": 2})
    
    assert response.status_code == 200
    assert response.json()["cleaned_tweets"] == ["tweet1", "tweet2"]


