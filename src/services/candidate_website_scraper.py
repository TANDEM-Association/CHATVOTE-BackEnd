# SPDX-FileCopyrightText: 2025 chatvote
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""
Robust scraper for candidate campaign websites using Playwright.

This service uses a real headless browser to:
1. Render JavaScript and dynamic content
2. Scroll through pages to trigger lazy loading
3. Navigate internal links to find relevant content
4. Handle modern websites with parallax, animations, etc.
5. Download and extract text from PDF files (tracts, programs, etc.)
"""

import asyncio
import io
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    TimeoutError as PlaywrightTimeout,
)
from pypdf import PdfReader

from src.models.candidate import Candidate

logger = logging.getLogger(__name__)

# Configuration
PAGE_TIMEOUT = 60000  # ms - timeout for page load
SCROLL_DELAY = 500  # ms - delay between scroll steps
MAX_PAGES_PER_CANDIDATE = 15
MAX_PDFS_PER_CANDIDATE = 10
RATE_LIMIT_DELAY = 1.0  # seconds between requests to same domain
PDF_MAX_SIZE = 10 * 1024 * 1024  # 10 MB max for PDFs

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
    "securite",
    "security",
    "environnement",
    "economie",
    "education",
    "sante",
    "logement",
    "transport",
    "culture",
]

# Tags to exclude from content extraction
EXCLUDED_TAGS = [
    "script",
    "style",
    "nav",
    "footer",
    "noscript",
    "svg",
    "iframe",
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
    """Robust scraper using Playwright for JavaScript-heavy websites."""

    def __init__(self):
        self._visited_urls: Set[str] = set()
        self._browser: Optional[Browser] = None

    async def _get_browser(self, playwright) -> Browser:
        """Get or create a browser instance with retry logic."""
        if self._browser is None:
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    self._browser = await playwright.chromium.launch(
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-accelerated-2d-canvas",
                            "--disable-gpu",
                            "--single-process",  # More stable in containers
                            "--no-zygote",  # Prevents fork issues
                            "--window-size=1920,1080",
                        ],
                    )
                    return self._browser
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Browser launch attempt {attempt + 1}/{max_retries} failed: {e}"
                    )
                    await asyncio.sleep(1)  # Wait before retry

            if last_error is not None:
                raise last_error

        return self._browser

    async def _close_browser(self):
        """Close the browser instance safely."""
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as e:
                logger.debug(f"Error closing browser (safe to ignore): {e}")
            finally:
                self._browser = None

    async def _scroll_page(self, page: Page) -> None:
        """Scroll through the entire page to trigger lazy loading."""
        try:
            # Get page height
            scroll_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")

            current_position = 0
            while current_position < scroll_height:
                # Scroll down by viewport height
                current_position += viewport_height
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                await page.wait_for_timeout(SCROLL_DELAY)

                # Check if new content loaded (page height might increase)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > scroll_height:
                    scroll_height = new_height

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(300)

        except Exception as e:
            logger.debug(f"Error during scroll: {e}")

    async def _dismiss_popups(self, page: Page) -> None:
        """Try to dismiss common popups (cookies, newsletters, etc.)."""
        popup_selectors = [
            # Cookie consent buttons
            "button:has-text('Accepter')",
            "button:has-text('Accept')",
            "button:has-text('J\\'accepte')",
            "button:has-text('OK')",
            "button:has-text('Continuer')",
            "[id*='cookie'] button",
            "[class*='cookie'] button",
            "[id*='consent'] button",
            "[class*='consent'] button",
            # Close buttons
            "button[aria-label='Close']",
            "button[aria-label='Fermer']",
            ".close-button",
            ".dismiss",
        ]

        for selector in popup_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=500):
                    await button.click()
                    await page.wait_for_timeout(300)
                    break
            except Exception:
                continue

    async def _extract_content(self, page: Page) -> tuple[str, str]:
        """
        Extract clean text content and title from the rendered page.

        Returns:
            Tuple of (title, content)
        """
        # Get the fully rendered HTML
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Remove unwanted tags
        for tag in soup.find_all(EXCLUDED_TAGS):
            tag.decompose()

        # Remove hidden elements
        for hidden in soup.find_all(style=re.compile(r"display:\s*none", re.I)):
            hidden.decompose()

        # Try to find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"content|main", re.I))
            or soup.find(class_=re.compile(r"content|main|page", re.I))
            or soup.body
        )

        if main_content is None:
            return title, ""

        # Extract text with proper spacing
        text_parts = []
        for element in main_content.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "span", "div"]
        ):
            text = element.get_text(strip=True)
            if text and len(text) > 10:  # Skip very short texts
                text_parts.append(text)

        # Join and clean up
        content = "\n".join(text_parts)
        # Remove excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)

        return title, content.strip()

    async def _find_relevant_links(
        self, page: Page, base_url: str
    ) -> List[tuple[str, str]]:
        """
        Find relevant internal links on the page.

        Returns:
            List of (url, page_type) tuples
        """
        links = []
        base_domain = urlparse(base_url).netloc

        try:
            # Get all links
            anchors = await page.query_selector_all("a[href]")

            for anchor in anchors:
                try:
                    href = await anchor.get_attribute("href")
                    if href is None:
                        continue

                    # Get link text for categorization
                    text = (await anchor.inner_text()).lower().strip()

                    # Build absolute URL
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)

                    # Skip external links, anchors, and non-http
                    if parsed.netloc != base_domain:
                        continue
                    if not parsed.scheme.startswith("http"):
                        continue

                    # Normalize URL (remove fragment)
                    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        normalized += f"?{parsed.query}"

                    # Skip already visited
                    if normalized in self._visited_urls:
                        continue

                    # Check if relevant
                    url_lower = normalized.lower()
                    for keyword in RELEVANT_PAGE_KEYWORDS:
                        if keyword in url_lower or keyword in text:
                            page_type = keyword
                            links.append((normalized, page_type))
                            break

                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error finding links: {e}")

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for url, ptype in links:
            if url not in seen:
                seen.add(url)
                unique_links.append((url, ptype))

        return unique_links[:MAX_PAGES_PER_CANDIDATE]

    async def _find_pdf_links(self, page: Page, base_url: str) -> List[tuple[str, str]]:
        """
        Find PDF links on the page.

        Returns:
            List of (url, title) tuples
        """
        pdf_links = []
        base_domain = urlparse(base_url).netloc

        try:
            # Get all links that point to PDFs
            anchors = await page.query_selector_all("a[href]")

            for anchor in anchors:
                try:
                    href = await anchor.get_attribute("href")
                    if href is None:
                        continue

                    # Check if it's a PDF link
                    if not href.lower().endswith(".pdf"):
                        continue

                    # Get link text as title
                    text = (await anchor.inner_text()).strip()
                    if not text:
                        # Try to get title from nearby elements
                        text = href.split("/")[-1].replace(".pdf", "").replace("_", " ")

                    # Build absolute URL
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)

                    # Allow same domain or common CDN domains
                    if parsed.netloc != base_domain and "wp-content" not in full_url:
                        # Skip external PDFs unless they're WordPress uploads
                        continue

                    if not parsed.scheme.startswith("http"):
                        continue

                    # Skip already visited
                    if full_url in self._visited_urls:
                        continue

                    pdf_links.append((full_url, text))

                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error finding PDF links: {e}")

        # Remove duplicates
        seen = set()
        unique_pdfs = []
        for url, title in pdf_links:
            if url not in seen:
                seen.add(url)
                unique_pdfs.append((url, title))

        return unique_pdfs[:MAX_PDFS_PER_CANDIDATE]

    async def _download_and_extract_pdf(
        self, url: str, title: str
    ) -> Optional[ScrapedPage]:
        """
        Download a PDF and extract its text content.

        Returns:
            ScrapedPage with PDF content, or None if extraction failed
        """
        try:
            logger.debug(f"Downloading PDF: {url}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Failed to download PDF {url}: HTTP {response.status}"
                        )
                        return None

                    # Check content type
                    content_type = response.headers.get("Content-Type", "")
                    if "pdf" not in content_type.lower() and not url.lower().endswith(
                        ".pdf"
                    ):
                        logger.debug(f"Not a PDF: {url}")
                        return None

                    # Check size
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > PDF_MAX_SIZE:
                        logger.warning(f"PDF too large ({content_length} bytes): {url}")
                        return None

                    pdf_bytes = await response.read()

            # Extract text from PDF
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.debug(f"Error extracting page {page_num} from PDF: {e}")

            content = "\n\n".join(text_parts)

            # Clean up content
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = re.sub(r" {2,}", " ", content)
            content = content.strip()

            if len(content) < 50:
                logger.debug(f"PDF has too little content: {url}")
                return None

            logger.info(f"Extracted {len(content)} chars from PDF: {title}")

            return ScrapedPage(
                url=url,
                title=f"[PDF] {title}",
                content=content,
                page_type="pdf",
            )

        except Exception as e:
            logger.warning(f"Error extracting PDF {url}: {e}")
            return None

    async def _scrape_page(
        self, page: Page, url: str, page_type: str
    ) -> Optional[ScrapedPage]:
        """Scrape a single page with full JavaScript rendering."""
        try:
            logger.debug(f"Scraping page: {url}")

            # Navigate to page
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=PAGE_TIMEOUT,
            )

            if response is None or response.status >= 400:
                logger.warning(
                    f"Failed to load {url}: HTTP {response.status if response else 'None'}"
                )
                return None

            # Dismiss any popups
            await self._dismiss_popups(page)

            # Wait for content to be ready
            await page.wait_for_load_state("domcontentloaded")

            # Scroll through the page to trigger lazy loading
            await self._scroll_page(page)

            # Wait a bit for any final content
            await page.wait_for_timeout(1000)

            # Extract content
            title, content = await self._extract_content(page)

            if len(content) < 100:  # Skip pages with very little content
                logger.debug(
                    f"Skipping {url}: too little content ({len(content)} chars)"
                )
                return None

            return ScrapedPage(
                url=url,
                title=title,
                content=content,
                page_type=page_type,
            )

        except PlaywrightTimeout:
            logger.warning(f"Timeout loading {url}")
            return None
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
            return None

    async def scrape_candidate_website(self, candidate: Candidate) -> ScrapedWebsite:
        """
        Scrape a candidate's entire website using Playwright.

        This method:
        1. Opens the main page in a headless browser
        2. Scrolls to load all dynamic content
        3. Extracts text content
        4. Finds and downloads PDF files (tracts, programs, etc.)
        5. Finds and follows relevant internal links
        6. Repeats for subpages
        """
        result = ScrapedWebsite(
            candidate_id=candidate.candidate_id,
            website_url=candidate.website_url or "",
        )

        if not candidate.website_url:
            result.error = "No website URL provided"
            return result

        self._visited_urls.clear()
        all_pdf_links: List[tuple[str, str]] = []

        async with async_playwright() as playwright:
            try:
                browser = await self._get_browser(playwright)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="fr-FR",
                )

                page = await context.new_page()

                # Scrape main page
                main_url = candidate.website_url
                self._visited_urls.add(main_url)

                main_page = await self._scrape_page(page, main_url, "main")
                if main_page:
                    result.pages.append(main_page)
                    logger.info(
                        f"Scraped main page for {candidate.full_name}: "
                        f"{len(main_page.content)} chars"
                    )
                else:
                    result.error = f"Failed to scrape main page: {main_url}"
                    await context.close()
                    return result

                # Find PDF links on main page
                pdf_links = await self._find_pdf_links(page, main_url)
                all_pdf_links.extend(pdf_links)
                logger.debug(f"Found {len(pdf_links)} PDF links on main page")

                # Find and scrape relevant subpages
                links_to_scrape = await self._find_relevant_links(page, main_url)
                logger.debug(f"Found {len(links_to_scrape)} relevant links to scrape")

                for link_url, page_type in links_to_scrape:
                    if len(result.pages) >= MAX_PAGES_PER_CANDIDATE:
                        break

                    if link_url in self._visited_urls:
                        continue

                    self._visited_urls.add(link_url)

                    # Rate limiting
                    await asyncio.sleep(RATE_LIMIT_DELAY)

                    scraped = await self._scrape_page(page, link_url, page_type)
                    if scraped:
                        result.pages.append(scraped)
                        logger.debug(
                            f"Scraped {page_type} page: {len(scraped.content)} chars"
                        )

                        # Find PDF links on subpages too
                        pdf_links = await self._find_pdf_links(page, link_url)
                        all_pdf_links.extend(pdf_links)

                await context.close()

                # Download and extract PDFs (outside browser context)
                if all_pdf_links:
                    # Remove duplicate PDFs
                    seen_pdfs = set()
                    unique_pdfs = []
                    for url, title in all_pdf_links:
                        if url not in seen_pdfs and url not in self._visited_urls:
                            seen_pdfs.add(url)
                            unique_pdfs.append((url, title))

                    logger.info(f"Downloading {len(unique_pdfs)} PDF files...")

                    for pdf_url, pdf_title in unique_pdfs[:MAX_PDFS_PER_CANDIDATE]:
                        self._visited_urls.add(pdf_url)
                        pdf_page = await self._download_and_extract_pdf(
                            pdf_url, pdf_title
                        )
                        if pdf_page:
                            result.pages.append(pdf_page)

            except (BrokenPipeError, ConnectionResetError, ConnectionError) as e:
                # Browser process crashed - this is recoverable
                logger.warning(
                    f"Browser connection lost for {candidate.full_name}: {e}. "
                    "This can happen with resource-intensive sites."
                )
                result.error = f"Browser connection lost: {e}"

            except Exception as e:
                logger.error(f"Error scraping website for {candidate.full_name}: {e}")
                result.error = str(e)

            finally:
                try:
                    await self._close_browser()
                except Exception:
                    # Ignore cleanup errors - browser may already be dead
                    self._browser = None

        logger.info(
            f"Completed scraping for {candidate.full_name}: "
            f"{len(result.pages)} pages, {result.total_content_length} total chars"
        )

        return result

    async def scrape_multiple_candidates(
        self, candidates: List[Candidate], max_concurrent: int = 1
    ) -> List[ScrapedWebsite]:
        """
        Scrape multiple candidate websites with limited concurrency.

        Note: Playwright browsers are resource-intensive, so we limit concurrency.
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(candidate: Candidate) -> ScrapedWebsite:
            async with semaphore:
                scraper = CandidateWebsiteScraper()
                return await scraper.scrape_candidate_website(candidate)

        tasks = [scrape_with_semaphore(c) for c in candidates if c.website_url]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to ScrapedWebsite with errors
        final_results: list[ScrapedWebsite] = []
        candidates_with_website = [c for c in candidates if c.website_url]
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                candidate = candidates_with_website[i]
                final_results.append(
                    ScrapedWebsite(
                        candidate_id=candidate.candidate_id,
                        website_url=candidate.website_url or "",
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results
