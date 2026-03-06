"""
Agentic workflow module for the AI Digest Agent.

Orchestrates the multi-step process of:
1. Query generation
2. Web search
3. Content extraction
4. Relevance ranking
5. Deduplication
6. Summarization
7. Final selection
"""

import logging
from typing import List, Dict, Any, Optional
import time

from config import Config
from agent.tools import LLMClient, SearchClient, ContentExtractor, parse_json_response
from agent.prompts import (
    get_query_generation_prompt,
    get_relevance_ranking_prompt,
    get_summarization_prompt,
    get_deduplication_prompt,
    get_final_selection_prompt
)
from storage.memory import MemoryStore


logger = logging.getLogger(__name__)


class DigestWorkflow:
    """Orchestrates the agentic workflow for generating AI/ML digests."""
    
    def __init__(self, config: Config):
        self.llm_client = LLMClient(config.llm)
        self.search_client = SearchClient(config.search)
        self.content_extractor = ContentExtractor()
        self.memory_store = MemoryStore(config.storage.memory_file)
        
    def run(self, target_items: int = 5) -> List[Dict[str, Any]]:
        """Execute the complete workflow to generate digest items."""
        logger.info("Starting digest generation workflow")
        
        queries = self._generate_queries()
        logger.info(f"Generated {len(queries)} search queries")
        
        search_results = self._execute_searches(queries)
        logger.info(f"Collected {len(search_results)} total search results")
        
        if not search_results:
            logger.error("No search results found, cannot continue")
            return []
        
        ranked_results = self._rank_results(search_results)
        logger.info(f"Ranked top {len(ranked_results)} results")
        
        past_urls = self.memory_store.get_past_urls()
        filtered_results = self._filter_past_urls(ranked_results, past_urls)
        logger.info(f"Filtered to {len(filtered_results)} results after removing past URLs")
        
        if not filtered_results:
            logger.warning("No new results after filtering, using ranked results")
            filtered_results = ranked_results[:15]
        
        summarized_items = self._summarize_results(filtered_results[:15])
        logger.info(f"Successfully summarized {len(summarized_items)} items")
        
        if not summarized_items:
            logger.error("No summarized items, cannot continue")
            return []
        
        past_items = self.memory_store.get_recent_past_items(months=3)
        deduplicated_items = self._deduplicate_items(summarized_items, past_items)
        logger.info(f"After deduplication: {len(deduplicated_items)} unique items")
        
        if len(deduplicated_items) < target_items:
            logger.warning(f"Only {len(deduplicated_items)} items available, less than target {target_items}")
            final_items = deduplicated_items
        else:
            final_items = self._select_final_items(deduplicated_items, target_items)
        
        logger.info(f"Selected {len(final_items)} final items for digest")
        return final_items
        
    def _generate_queries(self) -> List[str]:
        try:
            prompt = get_query_generation_prompt()
            response = self.llm_client.generate(prompt)
            queries = parse_json_response(response)
            if not isinstance(queries, list):
                return self._get_fallback_queries()
            return queries
        except Exception as e:
            logger.error(f"Failed to generate queries: {e}")
            return self._get_fallback_queries()
            
    def _get_fallback_queries(self) -> List[str]:
        return [
            "latest AI research papers 2026",
            "new machine learning frameworks tools",
            "LLM breakthrough developments",
            "AI startup funding news",
            "data science best practices 2026",
            "artificial intelligence industry news",
            "deep learning innovations",
            "MLOps tools and platforms"
        ]
        
    def _execute_searches(self, queries: List[str]) -> List[Dict[str, Any]]:
        all_results = []
        seen_urls = set()
        for i, query in enumerate(queries):
            logger.info(f"Searching: {query} ({i+1}/{len(queries)})")
            results = self.search_client.search(query)
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    all_results.append(result)
                    seen_urls.add(url)
            time.sleep(0.5)
        return all_results
        
    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(results) <= 15:
            return results
        try:
            prompt = get_relevance_ranking_prompt(results)
            response = self.llm_client.generate(prompt)
            ranked_ids = parse_json_response(response)
            if not isinstance(ranked_ids, list):
                return results[:15]
            ranked_results = []
            for idx in ranked_ids:
                if isinstance(idx, int) and 0 <= idx < len(results):
                    ranked_results.append(results[idx])
            return ranked_results[:15]
        except Exception as e:
            logger.error(f"Failed to rank results: {e}")
            return results[:15]
            
    def _filter_past_urls(self, results: List[Dict[str, Any]], past_urls: set) -> List[Dict[str, Any]]:
        return [r for r in results if r.get("url", "") not in past_urls]
        
    def _summarize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        summarized_items = []
        for i, result in enumerate(results):
            logger.info(f"Summarizing item {i+1}/{len(results)}: {result.get('title', 'N/A')}")
            url = result.get("url", "")
            title = result.get("title", "")
            content = self.content_extractor.extract(url)
            if not content:
                content = result.get("snippet", "")
            if not content:
                continue
            try:
                prompt = get_summarization_prompt(content, title, url)
                response = self.llm_client.generate(prompt)
                summary_data = parse_json_response(response)
                if isinstance(summary_data, dict):
                    summarized_items.append(summary_data)
            except Exception as e:
                logger.error(f"Failed to summarize {url}: {e}")
                continue
            time.sleep(0.3)
        return summarized_items
        
    def _deduplicate_items(self, items: List[Dict[str, Any]], past_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not past_items:
            return items
        deduplicated = []
        for item in items:
            try:
                prompt = get_deduplication_prompt(item, past_items)
                response = self.llm_client.generate(prompt)
                result = parse_json_response(response)
                if not result.get("is_duplicate", False):
                    deduplicated.append(item)
            except Exception:
                deduplicated.append(item)
            time.sleep(0.3)
        return deduplicated
        
    def _select_final_items(self, items: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        try:
            prompt = get_final_selection_prompt(items, target_count)
            response = self.llm_client.generate(prompt)
            selected_ids = parse_json_response(response)
            if not isinstance(selected_ids, list):
                return items[:target_count]
            final_items = []
            for idx in selected_ids:
                if isinstance(idx, int) and 0 <= idx < len(items):
                    final_items.append(items[idx])
            return final_items[:target_count]
        except Exception as e:
            logger.error(f"Failed to select final items: {e}")
            return items[:target_count]
