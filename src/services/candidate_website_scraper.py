# SPDX-FileCopyrightText: 2025 chatvote
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""
Service to scrape candidate campaign websites for RAG indexing.

This service:
1. Fetches the main page and relevant subpages of candidate websites
2. Extracts text content using BeautifulSoup
3. Returns structured content ready for indexing
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from src.models.candidate import Candidate

logger = logging.getLogger(__name__)

# Configuration
REQUEST_TIMEOUT = 60  # seconds (increased for slow sites)
MAX_PAGES_PER_CANDIDATE = 10
RATE_LIMIT_DELAY = 1.0  # seconds between requests to same domain
MAX_RETRIES = 3  # number of retries for failed requests

# Keywords to identify relevant subpages (French and English)
RELEVANT_PAGE_KEYWORDS = [
    "programme",
    "projet",
    "propositions",
    "engagements",
    "mesures",
    "actions",
    "priorites",
    "priorities",
    "vision",
    "about",
    "a-propos",
    "qui-suis-je",
    "biographie",
    "parcours",
    "actualites",
    "news",
    "blog",
]

# Tags to exclude from content extraction
EXCLUDED_TAGS = [
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "noscript",
]


@dataclass
class ScrapedPage:
    """Represents a scraped page from a candidate's website."""

    url: str
    title: str
    content: str
    page_type: str  # "main", "programme", "about", etc.


@dataclass
class ScrapedWebsite:
    """Represents the scraped content from a candidate's entire website."""

    candidate_id: str
    website_url: str
    pages: List[ScrapedPage] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def total_content_length(self) -> int:
        """Return total length of all scraped content."""
        return sum(len(page.content) for page in self.pages)

    @property
    def is_successful(self) -> bool:
        """Return True if at least one page was scraped successfully."""
        return len(self.pages) > 0


class CandidateWebsiteScraper:
    """Scraper for candidate campaign websites."""

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._visited_urls: Set[str] = set()

    async def _fetch_page(
        self, session: aiohttp.ClientSession, url: str, retry_count: int = 0
    ) -> Optional[str]:
        """Fetch a single page and return its HTML content with retry logic."""
        # Use realistic browser headers to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        try:
            async with session.get(
                url, headers=headers, allow_redirects=True
            ) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None

                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type.lower():
                    logger.debug(f"Skipping non-HTML content at {url}")
                    return None

                return await response.text()

        except asyncio.TimeoutError:
            if retry_count < MAX_RETRIES:
                wait_time = (retry_count + 1) * 2  # Exponential backoff
                logger.warning(
                    f"Timeout fetching {url}, retrying in {wait_time}s "
                    f"(attempt {retry_count + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(wait_time)
                return await self._fetch_page(session, url, retry_count + 1)
            logger.warning(f"Timeout fetching {url} after {MAX_RETRIES} retries")
            return None

        except aiohttp.ClientError as e:
            if retry_count < MAX_RETRIES:
                wait_time = (retry_count + 1) * 2
                logger.warning(
                    f"Client error fetching {url}: {e}, retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                return await self._fetch_page(session, url, retry_count + 1)
            logger.warning(f"Client error fetching {url}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    def _extract_text_content(self, html: str) -> tuple[str, str]:
        """
        Extract clean text content and title from HTML.

        Returns:
            Tuple of (title, content)
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Remove unwanted tags
        for tag in soup.find_all(EXCLUDED_TAGS):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(
            string=lambda text: isinstance(text, type(soup.Comment))
        ):
            comment.extract()

        # Try to find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"content|main", re.I))
            or soup.find(class_=re.compile(r"content|main", re.I))
            or soup.body
        )

        if main_content is None:
            main_content = soup

        # Extract text and clean it
        text = main_content.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        # Remove very short content (likely navigation only)
        if len(text) < 100:
            return title, ""

        return title, text

    def _find_relevant_links(self, html: str, base_url: str) -> List[tuple[str, str]]:
        """
        Find relevant subpage links in HTML content.

        Returns:
            List of tuples (url, page_type)
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []
        base_domain = urlparse(base_url).netloc

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")

            # Skip empty, javascript, and anchor-only links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Build absolute URL
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Skip external links and non-http(s) schemes
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc != base_domain:
                continue

            # Skip already visited URLs
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if normalized_url in self._visited_urls:
                continue

            # Check if link text or URL contains relevant keywords
            link_text = anchor.get_text(strip=True).lower()
            url_path = parsed.path.lower()

            for keyword in RELEVANT_PAGE_KEYWORDS:
                if keyword in link_text or keyword in url_path:
                    links.append((normalized_url, keyword))
                    break

        return links

    def _categorize_page_type(self, url: str, title: str) -> str:
        """Determine the type of page based on URL and title."""
        url_lower = url.lower()
        title_lower = title.lower()

        if any(
            kw in url_lower or kw in title_lower
            for kw in ["programme", "projet", "propositions"]
        ):
            return "programme"
        if any(
            kw in url_lower or kw in title_lower
            for kw in ["about", "a-propos", "biographie", "parcours"]
        ):
            return "about"
        if any(
            kw in url_lower or kw in title_lower
            for kw in ["actualites", "news", "blog"]
        ):
            return "news"
        if any(
            kw in url_lower or kw in title_lower
            for kw in ["engagements", "mesures", "actions"]
        ):
            return "engagements"

        return "other"

    async def scrape_candidate_website(self, candidate: Candidate) -> ScrapedWebsite:
        """
        Scrape a candidate's website and extract relevant content.

        Args:
            candidate: The candidate whose website to scrape

        Returns:
            ScrapedWebsite with all scraped pages
        """
        result = ScrapedWebsite(
            candidate_id=candidate.candidate_id,
            website_url=candidate.website_url or "",
        )

        if not candidate.website_url:
            result.error = "No website URL defined"
            return result

        self._visited_urls.clear()
        pages_to_scrape: List[tuple[str, str]] = [(candidate.website_url, "main")]

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            scraped_count = 0

            while pages_to_scrape and scraped_count < MAX_PAGES_PER_CANDIDATE:
                url, page_type = pages_to_scrape.pop(0)

                # Skip if already visited
                parsed_url = urlparse(url)
                normalized_url = (
                    f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                )
                if normalized_url in self._visited_urls:
                    continue

                self._visited_urls.add(normalized_url)

                # Fetch page
                html = await self._fetch_page(session, url)
                if html is None:
                    if page_type == "main":
                        result.error = f"Failed to fetch main page: {url}"
                    continue

                # Extract content
                title, content = self._extract_text_content(html)

                if content:
                    actual_page_type = (
                        page_type
                        if page_type == "main"
                        else self._categorize_page_type(url, title)
                    )
                    result.pages.append(
                        ScrapedPage(
                            url=url,
                            title=title,
                            content=content,
                            page_type=actual_page_type,
                        )
                    )
                    scraped_count += 1
                    logger.debug(
                        f"Scraped {actual_page_type} page for {candidate.full_name}: {url} ({len(content)} chars)"
                    )

                # Find more relevant pages (only from main page)
                if page_type == "main":
                    relevant_links = self._find_relevant_links(html, url)
                    for link_url, link_type in relevant_links:
                        if link_url not in [p[0] for p in pages_to_scrape]:
                            pages_to_scrape.append((link_url, link_type))

                # Rate limiting
                await asyncio.sleep(RATE_LIMIT_DELAY)

        if not result.pages and not result.error:
            result.error = "No content could be extracted"

        return result

    async def scrape_multiple_candidates(
        self, candidates: List[Candidate], max_concurrent: int = 3
    ) -> List[ScrapedWebsite]:
        """
        Scrape websites for multiple candidates.

        Args:
            candidates: List of candidates to scrape
            max_concurrent: Maximum concurrent scraping operations

        Returns:
            List of ScrapedWebsite results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def scrape_with_semaphore(candidate: Candidate) -> ScrapedWebsite:
            async with semaphore:
                logger.info(f"Starting scrape for {candidate.full_name}")
                result = await self.scrape_candidate_website(candidate)
                if result.is_successful:
                    logger.info(
                        f"Scraped {len(result.pages)} pages for {candidate.full_name} "
                        f"({result.total_content_length} chars total)"
                    )
                else:
                    logger.warning(
                        f"Failed to scrape {candidate.full_name}: {result.error}"
                    )
                return result

        # Filter candidates with website URLs
        candidates_with_websites = [c for c in candidates if c.website_url]
        logger.info(
            f"Scraping {len(candidates_with_websites)} candidates with website URLs "
            f"(out of {len(candidates)} total)"
        )

        tasks = [scrape_with_semaphore(c) for c in candidates_with_websites]
        results = await asyncio.gather(*tasks)

        successful = sum(1 for r in results if r.is_successful)
        logger.info(f"Scraping complete: {successful}/{len(results)} successful")

        return list(results)


# Convenience function for simple usage
async def scrape_candidate(candidate: Candidate) -> ScrapedWebsite:
    """Scrape a single candidate's website."""
    scraper = CandidateWebsiteScraper()
    return await scraper.scrape_candidate_website(candidate)


async def scrape_candidates(
    candidates: List[Candidate], max_concurrent: int = 3
) -> List[ScrapedWebsite]:
    """Scrape multiple candidates' websites."""
    scraper = CandidateWebsiteScraper()
    return await scraper.scrape_multiple_candidates(candidates, max_concurrent)
