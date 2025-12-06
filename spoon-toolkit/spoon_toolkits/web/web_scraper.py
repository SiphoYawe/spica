import logging
from typing import Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify
from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SpoonAI-WebScraper/1.0; +https://github.com/XSpoonAi/spoon-toolkits)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class WebScraperTool(BaseTool):
    """
    Fetch and clean web pages for LLM consumption.

    Example:
        scraper = WebScraperTool()
        result = await scraper.execute("https://example.com", format="markdown")
    """

    name: str = "web_scraper"
    description: str = "Fetch a web page, strip scripts/styles/ads, and return markdown/html/text. Gracefully reports paywalls (402)."
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Target URL to fetch."},
            "format": {
                "type": "string",
                "enum": ["markdown", "html", "text"],
                "description": "Output format; defaults to markdown.",
                "default": "markdown",
            },
            "smart_mode": {
                "type": "boolean",
                "description": "If true, truncate oversized pages to ~100k tokens to save context.",
                "default": True,
            },
        },
        "required": ["url"],
    }

    url: Optional[str] = Field(default=None)
    format: str = Field(default="markdown")
    smart_mode: bool = Field(default=True)

    async def execute(self, url: Optional[str] = None, format: str = "markdown", smart_mode: Optional[bool] = None) -> ToolResult:
        target_url = url or self.url
        if not target_url:
            return ToolResult(error="url is required")

        output_format = (format or self.format or "markdown").lower()
        if output_format not in {"markdown", "html", "text"}:
            return ToolResult(error="format must be one of: markdown, html, text")

        use_smart = self.smart_mode if smart_mode is None else smart_mode

        try:
            async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=20.0) as client:
                response = await client.get(target_url)
        except Exception as exc:
            logger.warning(f"WebScraperTool request failed for {target_url}: {exc}")
            return ToolResult(error=f"Request failed: {exc}")

        if response.status_code == 402:
            payment_headers = self._extract_payment_headers(response.headers)
            message = f"Access Denied (402). Payment Required. Headers: {payment_headers}"
            return ToolResult(output=message)

        if response.status_code >= 400:
            snippet = response.text[:200].replace("\n", " ")
            return ToolResult(error=f"Request failed with status {response.status_code}: {snippet}")

        cleaned_html = self._clean_html(response.text)
        if output_format == "html":
            content = cleaned_html
        elif output_format == "text":
            content = self._html_to_text(cleaned_html)
        else:
            content = self._html_to_markdown(cleaned_html)

        content, truncated = self._apply_smart_truncate(content) if use_smart else (content, False)
        if truncated:
            content = f"{content}\n\n[truncated for length]"

        return ToolResult(output=content)

    def _extract_payment_headers(self, headers: httpx.Headers) -> Dict[str, str]:
        target_keys = {"www-authenticate", "x-payment", "x-payment-required", "payment-required", "paywall", "payment"}
        payment_info = {k: v for k, v in headers.items() if k.lower() in target_keys}
        if not payment_info:
            payment_info = {k: v for k, v in headers.items() if "pay" in k.lower() or "auth" in k.lower()}
        return payment_info

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()

        ad_keywords = ("ad", "ads", "advert", "sponsor", "promo", "banner")

        def is_ad(tag) -> bool:
            if not tag.attrs:
                return False
            tokens = " ".join([tag.get("id", "")] + [cls for cls in (tag.get("class") or [])]).lower()
            return any(word in tokens for word in ad_keywords)

        for tag in soup.find_all(is_ad):
            tag.decompose()

        return str(soup)

    def _html_to_markdown(self, html: str) -> str:
        markdown = markdownify(html, heading_style="ATX")
        return markdown.strip()

    def _html_to_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        return text

    def _apply_smart_truncate(self, content: str, max_tokens: int = 100_000) -> Tuple[str, bool]:
        tokens = content.split()
        if len(tokens) <= max_tokens:
            return content, False

        truncated_content = " ".join(tokens[:max_tokens])
        return truncated_content, True
