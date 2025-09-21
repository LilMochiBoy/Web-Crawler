#!/usr/bin/env python3
"""
Web Crawler Program
A comprehensive web crawler to download webpages with proper rate limiting,
URL validation, and file organization.
"""

import requests
import os
import time
import re
import argparse
import logging
import yaml
import json
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from collections import deque
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
from typing import Set, Dict, Optional, List, Any
from tqdm import tqdm
from datetime import datetime


class ContentExtractor:
    """
    Extracts structured data from web pages.
    """
    
    def __init__(self):
        self.common_content_selectors = {
            'article': ['article', '.article', '.post', '.content', '.main-content'],
            'navigation': ['nav', '.nav', '.navigation', '.menu'],
            'sidebar': ['.sidebar', '.aside', 'aside'],
            'footer': ['footer', '.footer'],
            'header': ['header', '.header']
        }
    
    def extract_page_data(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract comprehensive data from a webpage.
        
        Args:
            html_content: Raw HTML content
            url: Page URL
            
        Returns:
            Dictionary containing extracted data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Basic page information
        data = {
            'url': url,
            'extracted_at': datetime.now().isoformat(),
            'title': self._extract_title(soup),
            'description': self._extract_description(soup),
            'keywords': self._extract_keywords(soup),
            'language': self._extract_language(soup),
            'author': self._extract_author(soup),
            'publication_date': self._extract_publication_date(soup),
            
            # Content analysis
            'word_count': self._count_words(soup),
            'paragraph_count': len(soup.find_all('p')),
            'heading_structure': self._extract_headings(soup),
            'text_content': self._extract_clean_text(soup),
            
            # Links and media
            'internal_links': self._extract_links(soup, url, internal=True),
            'external_links': self._extract_links(soup, url, internal=False),
            'images': self._extract_images(soup, url),
            'social_media_links': self._extract_social_links(soup),
            
            # Technical details
            'page_size_bytes': len(html_content),
            'meta_tags': self._extract_meta_tags(soup),
            'structured_data': self._extract_structured_data(soup),
            
            # Content categorization
            'content_sections': self._identify_content_sections(soup),
        }
        
        return data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        if soup.title:
            return soup.title.get_text().strip()
        
        # Fallback to h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
            
        return "No title found"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags."""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            return text[:200] + "..." if len(text) > 200 else text
            
        return "No description found"
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags."""
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            return [k.strip() for k in keywords_meta['content'].split(',')]
        return []
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract page language."""
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']
        return "unknown"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information."""
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
        
        # Try common author selectors
        author_selectors = ['.author', '.byline', '[rel="author"]', '.writer']
        for selector in author_selectors:
            author = soup.select_one(selector)
            if author:
                return author.get_text().strip()
        
        return "Unknown"
    
    def _extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date."""
        # Try various date meta tags
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="publish-date"]',
            'time[datetime]',
            '.date',
            '.publish-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_value = date_elem.get('content') or date_elem.get('datetime') or date_elem.get_text()
                if date_value:
                    return date_value.strip()
        
        return None
    
    def _count_words(self, soup: BeautifulSoup) -> int:
        """Count words in the main content."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        words = text.split()
        return len([word for word in words if word.strip()])
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract heading structure."""
        headings = {}
        for level in range(1, 7):  # h1 to h6
            tag_name = f'h{level}'
            heading_tags = soup.find_all(tag_name)
            if heading_tags:
                headings[tag_name] = [h.get_text().strip() for h in heading_tags]
        return headings
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        # Try to find main content
        main_content = (soup.find('main') or 
                       soup.find('article') or 
                       soup.find('.content') or 
                       soup.find('#content') or
                       soup.find('body'))
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length for storage
        return text[:5000] + "..." if len(text) > 5000 else text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str, internal: bool = True) -> List[Dict[str, str]]:
        """Extract internal or external links."""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            link_domain = urlparse(full_url).netloc
            
            is_internal = link_domain == base_domain or not link_domain
            
            if is_internal == internal:
                links.append({
                    'url': full_url,
                    'text': link.get_text().strip(),
                    'title': link.get('title', '')
                })
        
        return links[:50]  # Limit to prevent huge data
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image information."""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                images.append({
                    'url': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                })
        
        return images[:20]  # Limit to prevent huge data
    
    def _extract_social_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract social media links."""
        social_domains = ['facebook.com', 'twitter.com', 'x.com', 'linkedin.com', 
                         'instagram.com', 'youtube.com', 'github.com']
        social_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(domain in href for domain in social_domains):
                social_links.append(href)
        
        return list(set(social_links))  # Remove duplicates
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all meta tags."""
        meta_tags = {}
        
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_tags[name] = content
        
        return meta_tags
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract JSON-LD structured data."""
        structured_data = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return structured_data
    
    def _identify_content_sections(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Identify different content sections."""
        sections = {}
        
        for section_name, selectors in self.common_content_selectors.items():
            count = 0
            for selector in selectors:
                count += len(soup.select(selector))
            sections[section_name] = count
        
        return sections


class WebCrawler:
    """
    A web crawler that downloads webpages with proper etiquette and organization.
    """
    
    def __init__(self, 
                 max_depth: int = 2,
                 delay: float = 1.0,
                 max_pages: int = 50,
                 output_dir: str = "downloaded_pages",
                 allowed_domains: Optional[List[str]] = None,
                 user_agent: str = "WebCrawler-Bot/1.0"):
        """
        Initialize the web crawler.
        
        Args:
            max_depth: Maximum crawling depth
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to download
            output_dir: Directory to save downloaded pages
            allowed_domains: List of allowed domains (None means all domains)
            user_agent: User agent string for requests
        """
        self.max_depth = max_depth
        self.delay = delay
        self.max_pages = max_pages
        self.output_dir = Path(output_dir)
        self.allowed_domains = set(allowed_domains) if allowed_domains else None
        self.user_agent = user_agent
        
        # Initialize tracking sets and queues
        self.visited_urls: Set[str] = set()
        self.downloaded_pages = 0
        self.crawl_queue = deque()  # [(url, depth)]
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        # Initialize content extractor
        self.content_extractor = ContentExtractor()
        
        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_urls_found': 0,
            'pages_downloaded': 0,
            'pages_skipped': 0,
            'errors': {
                'timeout': 0,
                'connection': 0,
                'http_errors': 0,
                'other': 0
            },
            'domains_crawled': set(),
            'total_bytes_downloaded': 0,
            'avg_response_time': 0,
            'response_times': [],
            'content_extracted': 0,  # New stat for extracted content
        }
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Setup session with headers and improved connection settings
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configure adapter for better connection handling
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _setup_logging(self):
        """Setup logging configuration with Unicode support."""
        # Configure logging with UTF-8 encoding for Windows compatibility
        log_file = self.output_dir / 'crawler.log'
        
        # Create handlers
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler()
        
        # Set format (remove emojis for Windows console compatibility)
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()  # Clear any existing handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and ensuring consistent format.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL string
        """
        parsed = urlparse(url.strip())
        # Remove fragment and ensure lowercase domain
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid for crawling.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid for crawling
        """
        try:
            parsed = urlparse(url)
            
            # Check if URL has valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check if domain is allowed
            if self.allowed_domains:
                domain = parsed.netloc.lower()
                if not any(domain == allowed or domain.endswith('.' + allowed) 
                          for allowed in self.allowed_domains):
                    return False
            
            # Enhanced file extension filtering
            path_lower = parsed.path.lower()
            
            # Media files
            media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 
                               '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
                               '.wav', '.flac', '.ogg', '.m4a', '.aac'}
            
            # Document files  
            doc_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                             '.rtf', '.odt', '.ods', '.odp'}
            
            # Archive files
            archive_extensions = {'.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz'}
            
            # Code and data files
            code_extensions = {'.css', '.js', '.json', '.xml', '.ico', '.woff', '.woff2',
                              '.ttf', '.eot', '.map', '.min.js', '.min.css'}
            
            skip_extensions = media_extensions | doc_extensions | archive_extensions | code_extensions
            
            if any(path_lower.endswith(ext) for ext in skip_extensions):
                self.logger.debug(f"Skipping file with blocked extension: {url}")
                return False
            
            # Skip URLs with query parameters that look like search or dynamic content
            if parsed.query:
                skip_params = ['search', 'q', 'query', 'id', 'page', 'offset', 'limit', 
                              'sort', 'filter', 'ajax', 'json', 'xml', 'api']
                query_lower = parsed.query.lower()
                if any(param in query_lower for param in skip_params):
                    self.logger.debug(f"Skipping URL with dynamic parameters: {url}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def _can_fetch(self, url: str) -> bool:
        """
        Check if we can fetch the URL according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed to fetch
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check cache first
            if base_url not in self.robots_cache:
                robots_url = urljoin(base_url, '/robots.txt')
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                try:
                    rp.read()
                    self.robots_cache[base_url] = rp
                except Exception:
                    # If robots.txt can't be read, assume we can fetch
                    self.robots_cache[base_url] = None
            
            robots_parser = self.robots_cache[base_url]
            if robots_parser is None:
                return True
                
            return robots_parser.can_fetch(self.user_agent, url)
            
        except Exception:
            return True
    
    def _fetch_page(self, url: str) -> Optional[requests.Response]:
        """
        Fetch a single webpage with detailed error logging.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response object or None if failed
        """
        try:
            self.logger.info(f"Fetching: {url}")
            
            # Add delay between requests
            time.sleep(self.delay)
            
            response = self.session.get(
                url, 
                timeout=(10, 30),  # (connect timeout, read timeout)
                allow_redirects=True,
                stream=False  # Don't stream for small pages
            )
            
            # Detailed status code handling
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    self.logger.debug(f"[SUCCESS] Successfully fetched HTML: {url} ({len(response.content)} bytes)")
                    return response
                else:
                    self.logger.info(f"[WARNING] Skipping non-HTML content: {content_type} for {url}")
                    return None
            elif response.status_code == 404:
                self.logger.warning(f"[404] Page not found: {url}")
            elif response.status_code == 403:
                self.logger.warning(f"[403] Access forbidden: {url}")
            elif response.status_code == 429:
                self.logger.warning(f"[429] Rate limited: {url} - Consider increasing delay")
            elif response.status_code >= 500:
                self.logger.warning(f"[SERVER] Server error ({response.status_code}): {url}")
            else:
                self.logger.warning(f"[HTTP] HTTP {response.status_code} for {url}")
                
        except requests.exceptions.Timeout:
            self.logger.error(f"[TIMEOUT] Timeout error for {url} (>30s)")
            self._update_stats('error', error_type='timeout')
        except requests.exceptions.ConnectionError:
            self.logger.error(f"[CONNECTION] Connection error for {url} - Check internet connection")
            self._update_stats('error', error_type='connection')
        except requests.exceptions.TooManyRedirects:
            self.logger.error(f"[REDIRECT] Too many redirects for {url}")
            self._update_stats('error', error_type='http_errors')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[ERROR] Request error for {url}: {type(e).__name__}: {e}")
            self._update_stats('error', error_type='http_errors')
        except Exception as e:
            self.logger.error(f"[UNEXPECTED] Unexpected error for {url}: {type(e).__name__}: {e}")
            self._update_stats('error', error_type='other')
        
        return None
    
    def _save_page(self, url: str, response: requests.Response) -> bool:
        """
        Save webpage to file.
        
        Args:
            url: Original URL
            response: Response object containing the page
            
        Returns:
            True if saved successfully
        """
        try:
            # Create safe filename from URL
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path.strip('/')
            
            # Create domain directory
            domain_dir = self.output_dir / domain
            domain_dir.mkdir(exist_ok=True)
            
            # Generate filename
            if not path or path == '/':
                filename = "index.html"
            else:
                # Replace path separators and clean filename
                filename = re.sub(r'[<>:"/\\|?*]', '_', path)
                if not filename.endswith('.html'):
                    filename += '.html'
            
            filepath = domain_dir / filename
            
            # Handle duplicate filenames
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name, ext = original_filepath.stem, original_filepath.suffix
                filepath = original_filepath.parent / f"{name}_{counter}{ext}"
                counter += 1
            
            # Save HTML content
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(response.text)
            
            # Extract structured data from the page
            try:
                extracted_data = self.content_extractor.extract_page_data(response.text, url)
                
                # Save extracted data as JSON
                json_file = filepath.with_suffix('.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2, ensure_ascii=False)
                
                self.stats['content_extracted'] += 1
                self.logger.info(f"Extracted data: {json_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to extract content from {url}: {e}")
            
            # Save metadata
            metadata_file = filepath.with_suffix('.meta')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Content-Type: {response.headers.get('content-type', 'N/A')}\n")
                f.write(f"Content-Length: {len(response.content)}\n")
                f.write(f"Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.logger.info(f"Saved: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving {url}: {e}")
            return False
    
    def _extract_links(self, url: str, html_content: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            url: Base URL for resolving relative links
            html_content: HTML content to parse
            
        Returns:
            List of absolute URLs
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            links = []
            
            # Extract links from <a> tags
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if href:
                    absolute_url = urljoin(url, href)
                    normalized_url = self._normalize_url(absolute_url)
                    if self._is_valid_url(normalized_url):
                        links.append(normalized_url)
            
            return links
            
        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    def crawl(self, start_url: str):
        """
        Start crawling from the given URL.
        
        Args:
            start_url: URL to start crawling from
        """
        start_url = self._normalize_url(start_url)
        
        if not self._is_valid_url(start_url):
            self.logger.error(f"Invalid start URL: {start_url}")
            return
        
        self.logger.info(f"Starting crawl from: {start_url}")
        self.crawl_queue.append((start_url, 0))
        
        # Start timing
        self.stats['start_time'] = time.time()
        
        # Initialize progress bar
        progress_bar = tqdm(total=self.max_pages, desc="[DOWNLOAD] Downloading", unit="pages")
        
        while self.crawl_queue and self.downloaded_pages < self.max_pages:
            current_url, depth = self.crawl_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Skip if depth exceeded
            if depth > self.max_depth:
                continue
            
            # Check robots.txt
            if not self._can_fetch(current_url):
                self.logger.info(f"Robots.txt disallows: {current_url}")
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            # Fetch the page
            start_time = time.time()
            response = self._fetch_page(current_url)
            if response is None:
                continue
            
            response_time = time.time() - start_time
            
            # Save the page
            if self._save_page(current_url, response):
                self.downloaded_pages += 1
                self._update_stats('page_downloaded', current_url, response_time, len(response.content))
                
                # Update progress bar
                progress_bar.update(1)
                progress_bar.set_postfix({
                    'Domain': urlparse(current_url).netloc[:20],
                    'Queue': len(self.crawl_queue),
                    'Speed': f"{self.stats.get('avg_response_time', 0):.1f}s"
                })
                
                # Extract links for further crawling if not at max depth
                if depth < self.max_depth:
                    links = self._extract_links(current_url, response.text)
                    self._update_stats('url_found') # Will be called len(links) times
                    for _ in links:
                        self.stats['total_urls_found'] += 1
                    for link in links:
                        if link not in self.visited_urls:
                            self.crawl_queue.append((link, depth + 1))
            else:
                self._update_stats('page_skipped')
        
        # Close progress bar
        progress_bar.close()
        
        self.logger.info(f"Crawling completed. Downloaded {self.downloaded_pages} pages.")
        
        # Record end time and display final statistics
        self.stats['end_time'] = time.time()
        self._display_final_statistics()
    
    def _update_stats(self, action: str, url: str = None, response_time: float = None, 
                     bytes_downloaded: int = None, error_type: str = None):
        """Update crawling statistics."""
        if action == 'url_found':
            self.stats['total_urls_found'] += 1
        elif action == 'page_downloaded':
            self.stats['pages_downloaded'] += 1
            if url:
                domain = urlparse(url).netloc
                self.stats['domains_crawled'].add(domain)
            if bytes_downloaded:
                self.stats['total_bytes_downloaded'] += bytes_downloaded
            if response_time:
                self.stats['response_times'].append(response_time)
                self.stats['avg_response_time'] = sum(self.stats['response_times']) / len(self.stats['response_times'])
        elif action == 'page_skipped':
            self.stats['pages_skipped'] += 1
        elif action == 'error':
            if error_type in self.stats['errors']:
                self.stats['errors'][error_type] += 1
            else:
                self.stats['errors']['other'] += 1
    
    def _display_final_statistics(self):
        """Display comprehensive crawling statistics."""
        if not self.stats['start_time'] or not self.stats['end_time']:
            return
            
        duration = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info("=" * 50)
        self.logger.info("[STATISTICS] CRAWLING STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"[DURATION] Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        self.logger.info(f"[URLS] URLs Found: {self.stats['total_urls_found']}")
        self.logger.info(f"[DOWNLOADED] Pages Downloaded: {self.stats['pages_downloaded']}")
        self.logger.info(f"[EXTRACTED] Content Extracted: {self.stats['content_extracted']}")
        self.logger.info(f"[SKIPPED] Pages Skipped: {self.stats['pages_skipped']}")
        self.logger.info(f"[DOMAINS] Domains Crawled: {len(self.stats['domains_crawled'])}")
        
        if self.stats['total_bytes_downloaded'] > 0:
            mb_downloaded = self.stats['total_bytes_downloaded'] / (1024 * 1024)
            self.logger.info(f"[DATA] Data Downloaded: {mb_downloaded:.2f} MB")
        
        if self.stats['response_times']:
            self.logger.info(f"[RESPONSE] Average Response Time: {self.stats['avg_response_time']:.2f}s")
            self.logger.info(f"[RATE] Pages/minute: {(self.stats['pages_downloaded'] / (duration/60)):.1f}")
        
        # Error summary
        total_errors = sum(self.stats['errors'].values())
        if total_errors > 0:
            self.logger.info(f"[ERRORS] Total Errors: {total_errors}")
            for error_type, count in self.stats['errors'].items():
                if count > 0:
                    self.logger.info(f"   └── {error_type}: {count}")
        
        # Success rate
        total_attempts = self.stats['pages_downloaded'] + self.stats['pages_skipped'] + total_errors
        if total_attempts > 0:
            success_rate = (self.stats['pages_downloaded'] / total_attempts) * 100
            self.logger.info(f"[SUCCESS] Success Rate: {success_rate:.1f}%")
        
        self.logger.info("=" * 50)


def load_config(config_file: str = "crawler_config.yaml") -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dictionary with configuration settings
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"[CONFIG] Loaded configuration from {config_file}")
                return config
        else:
            print(f"⚠️  Configuration file {config_file} not found, using defaults")
            return {}
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return {}


def config_to_args(config: Dict) -> Dict:
    """Convert YAML config to crawler arguments."""
    args = {}
    
    # Basic crawler settings
    if 'crawler' in config:
        crawler_config = config['crawler']
        if 'max_depth' in crawler_config:
            args['max_depth'] = crawler_config['max_depth']
        if 'delay' in crawler_config:
            args['delay'] = crawler_config['delay']
        if 'max_pages' in crawler_config:
            args['max_pages'] = crawler_config['max_pages']
        if 'user_agent' in crawler_config:
            args['user_agent'] = crawler_config['user_agent']
    
    # Output settings
    if 'output' in config:
        output_config = config['output']
        if 'directory' in output_config:
            args['output_dir'] = output_config['directory']
    
    # Filter settings  
    if 'filters' in config:
        filter_config = config['filters']
        if 'allowed_domains' in filter_config and filter_config['allowed_domains']:
            args['allowed_domains'] = filter_config['allowed_domains']
    
    return args


def main():
    """Main function to handle command line arguments and start crawling."""
    parser = argparse.ArgumentParser(description="Web Crawler to download webpages")
    parser.add_argument("url", help="Starting URL to crawl")
    parser.add_argument("--config", default="crawler_config.yaml", help="Configuration file (default: crawler_config.yaml)")
    parser.add_argument("--max-depth", type=int, help="Maximum crawling depth (overrides config)")
    parser.add_argument("--delay", type=float, help="Delay between requests in seconds (overrides config)")
    parser.add_argument("--max-pages", type=int, help="Maximum number of pages to download (overrides config)")
    parser.add_argument("--output-dir", help="Output directory (overrides config)")
    parser.add_argument("--allowed-domains", nargs='+', help="List of allowed domains (overrides config)")
    parser.add_argument("--user-agent", help="User agent string (overrides config)")
    
    args = parser.parse_args()
    
    # Load configuration file
    config = load_config(args.config)
    config_args = config_to_args(config)
    
    # Command line arguments override config file
    crawler_args = {
        'max_depth': args.max_depth or config_args.get('max_depth', 2),
        'delay': args.delay or config_args.get('delay', 1.0),
        'max_pages': args.max_pages or config_args.get('max_pages', 50),
        'output_dir': args.output_dir or config_args.get('output_dir', "downloaded_pages"),
        'allowed_domains': args.allowed_domains or config_args.get('allowed_domains'),
        'user_agent': args.user_agent or config_args.get('user_agent', "WebCrawler-Bot/1.0")
    }
    
    print("[CRAWLER] Web Crawler Starting...")
    print(f"[SETTINGS] depth={crawler_args['max_depth']}, pages={crawler_args['max_pages']}, delay={crawler_args['delay']}s")
    
    # Create and configure crawler
    crawler = WebCrawler(**crawler_args)
    
    # Start crawling
    try:
        crawler.crawl(args.url)
    except KeyboardInterrupt:
        print("\n⏸️  Crawling interrupted by user.")
        print(f"📊 Downloaded {crawler.downloaded_pages} pages before interruption.")
        if hasattr(crawler, 'stats') and crawler.stats.get('start_time'):
            crawler.stats['end_time'] = time.time()
            crawler._display_final_statistics()


if __name__ == "__main__":
    main()
