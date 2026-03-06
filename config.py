"""Configuration from environment variables."""

import os
from typing import Literal
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()


@dataclass
class LLMConfig:
    provider: Literal["together", "groq", "huggingface"]
    api_key: str
    model_name: str
    base_url: str
    max_tokens: int = 2048
    temperature: float = 0.7


@dataclass
class SearchConfig:
    provider: Literal["tavily", "serper"]
    api_key: str
    max_results: int = 10


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_email: str
    use_tls: bool = True


@dataclass
class StorageConfig:
    memory_file: str = "storage/memory.json"


class Config:
    def __init__(self):
        self.llm = self._load_llm_config()
        self.search = self._load_search_config()
        self.email = self._load_email_config()
        self.storage = StorageConfig(memory_file=os.getenv("MEMORY_FILE", "storage/memory.json"))
        
    def _load_llm_config(self) -> LLMConfig:
        provider = os.getenv("LLM_PROVIDER", "groq").lower()
        models = {"together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "groq": "llama-3.3-70b-versatile", "huggingface": "meta-llama/Meta-Llama-3-70B-Instruct"}
        urls = {"together": "https://api.together.xyz/v1", "groq": "https://api.groq.com/openai/v1", "huggingface": "https://api-inference.huggingface.co/models"}
        return LLMConfig(provider=provider, api_key=os.getenv("LLM_API_KEY", ""), model_name=os.getenv("LLM_MODEL", models.get(provider, "")), base_url=urls.get(provider, ""), max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")), temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")))
    
    def _load_search_config(self) -> SearchConfig:
        provider = os.getenv("SEARCH_PROVIDER", "tavily").lower()
        return SearchConfig(provider=provider, api_key=os.getenv("SEARCH_API_KEY", ""), max_results=int(os.getenv("SEARCH_MAX_RESULTS", "10")))
    
    def _load_email_config(self) -> EmailConfig:
        return EmailConfig(smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"), smtp_port=int(os.getenv("SMTP_PORT", "587")), sender_email=os.getenv("SENDER_EMAIL", ""), sender_password=os.getenv("SENDER_PASSWORD", ""), recipient_email=os.getenv("RECIPIENT_EMAIL", ""), use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true")
    
    def validate(self) -> None:
        errors = []
        if not self.llm.api_key: errors.append("LLM_API_KEY")
        if not self.search.api_key: errors.append("SEARCH_API_KEY")
        if not self.email.sender_email: errors.append("SENDER_EMAIL")
        if not self.email.sender_password: errors.append("SENDER_PASSWORD")
        if not self.email.recipient_email: errors.append("RECIPIENT_EMAIL")
        if errors:
            raise ValueError(f"Missing: {', '.join(errors)}")
