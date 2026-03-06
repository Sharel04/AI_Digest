"""Tools module: LLM, Search, Content Extractor."""

import json
import logging
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re

from config import LLMConfig, SearchConfig


logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = requests.Session()
        
    def generate(self, prompt: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
                if self.config.provider == "groq":
                    return self._call_groq(prompt)
                elif self.config.provider == "together":
                    return self._call_together(prompt)
                elif self.config.provider == "huggingface":
                    return self._call_huggingface(prompt)
                else:
                    raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
                    
    def _call_groq(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        response = self.session.post(f"{self.config.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _call_together(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        response = self.session.post(f"{self.config.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _call_huggingface(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": self.config.max_tokens, "temperature": self.config.temperature, "return_full_text": False}
        }
        response = self.session.post(f"{self.config.base_url}/{self.config.model_name}", headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return result.get("generated_text", "")


class SearchClient:
    def __init__(self, config: SearchConfig):
        self.config = config
        self.session = requests.Session()
        
    def search(self, query: str, max_retries: int = 3) -> List[Dict[str, Any]]:
        for attempt in range(max_retries):
            try:
                if self.config.provider == "tavily":
                    return self._search_tavily(query)
                elif self.config.provider == "serper":
                    return self._search_serper(query)
                else:
                    raise ValueError(f"Unsupported search provider: {self.config.provider}")
            except Exception as e:
                logger.warning(f"Search attempt {attempt + 1} failed for query '{query}': {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return []
                    
    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        response = self.session.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": self.config.api_key, "query": query, "search_depth": "advanced", "max_results": self.config.max_results},
            timeout=30
        )
        response.raise_for_status()
        return [{"title": r.get("title", ""), "snippet": r.get("content", ""), "url": r.get("url", "")} for r in response.json().get("results", [])]
    
    def _search_serper(self, query: str) -> List[Dict[str, Any]]:
        response = self.session.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": self.config.api_key, "Content-Type": "application/json"},
            json={"q": query, "num": self.config.max_results},
            timeout=30
        )
        response.raise_for_status()
        return [{"title": r.get("title", ""), "snippet": r.get("snippet", ""), "url": r.get("link", "")} for r in response.json().get("organic", [])]


class ContentExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        
    def extract(self, url: str, max_retries: int = 2) -> Optional[str]:
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile("content|article|post"))
                text = article.get_text(separator="\n", strip=True) if article else soup.get_text(separator="\n", strip=True)
                return re.sub(r'\n\s*\n+', '\n\n', text)[:10000]
            except Exception as e:
                logger.warning(f"Content extraction attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None


def parse_json_response(response: str):
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()
    return json.loads(response)
