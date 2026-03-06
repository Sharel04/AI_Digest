# AI Digest Agent

Monthly AI/ML digest newsletter – generates curated summaries and emails them.

## Setup

1. Clone the repo
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys

## Required Secrets (GitHub Actions)

- `LLM_API_KEY` – Groq API key
- `SEARCH_API_KEY` – Tavily API key  
- `SENDER_EMAIL`, `SENDER_PASSWORD` – Gmail (app password)
- `RECIPIENT_EMAIL` – Recipient address

## Run

- **Local:** `python main.py`
- **GitHub:** Runs automatically on the 1st of each month, or trigger manually via Actions
