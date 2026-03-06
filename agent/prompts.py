"""Prompt templates for the AI Digest Agent."""

from typing import List, Dict, Any


def get_query_generation_prompt() -> str:
    return """You are an AI research assistant. Generate 8-10 diverse search queries to find the latest and most important updates in:
- Data Science
- Machine Learning
- Artificial Intelligence
- Large Language Models (LLMs)
- AI startups and funding

Focus on: recent breakthroughs, new tools, industry news, funding rounds, technical innovations.

Return ONLY a JSON array of search query strings. Example: ["query 1", "query 2"]
Do not include any other text."""


def get_relevance_ranking_prompt(search_results: List[Dict[str, Any]]) -> str:
    results_text = "\n\n".join([
        f"ID: {i}\nTitle: {r.get('title', 'N/A')}\nSnippet: {r.get('snippet', 'N/A')}\nURL: {r.get('url', 'N/A')}"
        for i, r in enumerate(search_results)
    ])
    return f"""Rank these search results by relevance for ML/AI professionals. Criteria: recency, impact, quality.

Search Results:
{results_text}

Return ONLY a JSON array of IDs in ranked order (top 15). Example: [5, 2, 8, 1, 10]
Do not include any other text."""


def get_summarization_prompt(article_content: str, title: str, url: str) -> str:
    return f"""Summarize this article for ML/AI professionals.

Title: {title}
URL: {url}
Content: {article_content[:5000]}

Return ONLY a JSON object:
{{"title": "improved title", "summary": "3-4 sentences", "why_it_matters": "1-2 sentences", "category": "Research|Tooling|Industry|Funding", "url": "{url}"}}
Do not include any other text."""


def get_deduplication_prompt(current_item: Dict[str, Any], previous_items: List[Dict[str, Any]]) -> str:
    previous_text = "\n\n".join([f"Title: {i.get('title')}\nSummary: {i.get('summary')}" for i in previous_items])
    return f"""Is this item a duplicate or too similar to any previous item?

Current: Title: {current_item.get('title')}\nSummary: {current_item.get('summary')}

Previous items:
{previous_text}

Return ONLY: {{"is_duplicate": true/false, "reason": "brief explanation"}}
Do not include any other text."""


def get_final_selection_prompt(ranked_items: List[Dict[str, Any]], target_count: int = 5) -> str:
    items_text = "\n\n".join([
        f"ID: {i}\nTitle: {item.get('title')}\nCategory: {item.get('category')}\nSummary: {item.get('summary')}"
        for i, item in enumerate(ranked_items)
    ])
    return f"""Select the top {target_count} items for a monthly AI/ML digest. Prefer diverse categories.

Available:
{items_text}

Return ONLY a JSON array of IDs. Example: [2, 5, 1, 8, 3]
Do not include any other text."""
