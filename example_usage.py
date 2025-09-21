#!/usr/bin/env python3
"""
Example usage of the WebCrawler class
"""

from crawler import WebCrawler

def example_usage():
    """Example of how to use the WebCrawler programmatically."""
    
    # Create a crawler instance with custom settings
    crawler = WebCrawler(
        max_depth=1,
        delay=1.0,
        max_pages=5,
        output_dir="example_downloads",
        allowed_domains=["httpbin.org"],  # Only crawl httpbin.org
        user_agent="Example-Crawler/1.0"
    )
    
    # Start crawling
    print("Starting example crawl...")
    crawler.crawl("https://httpbin.org")
    print(f"Example crawl completed. Downloaded {crawler.downloaded_pages} pages.")


if __name__ == "__main__":
    example_usage()