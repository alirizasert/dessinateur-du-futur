﻿from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any
from urllib import parse, request

from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase

WEB_SEARCH_SPEC = ToolSpec(
    name="web_search",
    description="Web search with search/open/find actions",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["search", "open_page", "find_in_page"]},
            "query": {"type": "string"},
            "url": {"type": "string"},
            "pattern": {"type": "string"},
            "max_results": {"type": "integer"},
            "max_chars": {"type": "integer"},
        },
        "required": ["action"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "page": {"type": "object"},
            "matches": {"type": "array"},
        },
    },
)


class _DDGParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_result_link = False
        self._in_snippet = False
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] = {}
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and "result__a" in (attrs_dict.get("class") or ""):
            self._in_result_link = True
            self._current = {"url": attrs_dict.get("href") or "", "title": "", "snippet": ""}
            self._buffer = []
        if tag == "a" and "result__snippet" in (attrs_dict.get("class") or ""):
            self._in_snippet = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_result_link:
            self._current["title"] = html.unescape("".join(self._buffer)).strip()
            self._buffer = []
            self._in_result_link = False
            if self._current.get("url"):
                self.results.append(self._current)
        if tag == "a" and self._in_snippet:
            snippet = html.unescape("".join(self._buffer)).strip()
            if self.results:
                self.results[-1]["snippet"] = snippet
            self._buffer = []
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        if self._in_result_link or self._in_snippet:
            self._buffer.append(data)


class WebSearchTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return WEB_SEARCH_SPEC

    def run(self, **kwargs: Any):
        action = kwargs.get("action")
        if action == "search":
            query = kwargs.get("query") or ""
            if not query:
                raise ValueError("query is required")
            max_results = int(kwargs.get("max_results") or 5)
            return {"results": self._search(query, max_results)}
        if action == "open_page":
            url = kwargs.get("url") or ""
            if not url:
                raise ValueError("url is required")
            max_chars = int(kwargs.get("max_chars") or 4000)
            return {"page": self._open_page(url, max_chars)}
        if action == "find_in_page":
            url = kwargs.get("url") or ""
            pattern = kwargs.get("pattern") or ""
            if not url or not pattern:
                raise ValueError("url and pattern are required")
            max_results = int(kwargs.get("max_results") or 20)
            return {"matches": self._find_in_page(url, pattern, max_results)}
        raise ValueError(f"unknown action: {action}")

    def _fetch(self, url: str) -> str:
        req = request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CADx/0.1)"
            },
        )
        with request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _search(self, query: str, max_results: int) -> list[dict[str, str]]:
        url = "https://duckduckgo.com/html/?" + parse.urlencode({"q": query})
        html_text = self._fetch(url)
        parser = _DDGParser()
        parser.feed(html_text)
        results = []
        for item in parser.results:
            if not item.get("title"):
                continue
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            })
            if len(results) >= max_results:
                break
        return results

    def _open_page(self, url: str, max_chars: int) -> dict[str, str]:
        raw = self._fetch(url)
        title = ""
        match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        if match:
            title = html.unescape(match.group(1)).strip()
        text = self._strip_html(raw)
        if len(text) > max_chars:
            text = text[:max_chars] + f"...(截断,共{len(text)}字符)"
        return {"url": url, "title": title, "content": text}

    def _find_in_page(self, url: str, pattern: str, max_results: int) -> list[str]:
        raw = self._fetch(url)
        text = self._strip_html(raw)
        lines = text.splitlines()
        regex = re.compile(pattern, re.IGNORECASE)
        matches: list[str] = []
        for line in lines:
            if regex.search(line):
                matches.append(line.strip())
                if len(matches) >= max_results:
                    break
        return matches

    def _strip_html(self, text: str) -> str:
        text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

