#!/usr/bin/env python3
"""
Quick test script for resume functionality
"""

import os
import sys
import time
import sqlite3
from pathlib import Path

# Add the crawler directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import our crawler components
from crawler import DatabaseManager, WebCrawler

def test_resume_functionality():
    """Test the resume functionality manually."""
    print("Testing Resume Functionality")
    print("=" * 50)
    
    # Initialize database manager
    db_path = "downloaded_pages/test_crawler_data.db"
    os.makedirs("downloaded_pages", exist_ok=True)
    db_manager = DatabaseManager(db_path)
    
    # Create a test session
    print("1. Creating test session...")
    session_id = db_manager.start_session(
        start_url="https://example.com",
        max_depth=2,
        max_pages=10,
        config_data={'test': True}
    )
    print(f"   Created session: {session_id}")
    
    # Add some test URLs to queue state
    print("2. Adding test URLs to queue state...")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        test_urls = [
            ("https://example.com/page1", 1),
            ("https://example.com/page2", 1),
            ("https://example.com/page3", 2)
        ]
        for url, depth in test_urls:
            cursor.execute("""
                INSERT INTO queue_state (session_id, url, depth, status)
                VALUES (?, ?, ?, 'pending')
            """, (int(session_id), url, depth))
        conn.commit()
    
    # Add visited URLs
    print("3. Simulating visited URLs...")
    visited_urls = {"https://example.com", "https://example.com/about"}
    db_manager.save_crawl_state(session_id, test_urls, visited_urls)
    
    # Mark session as interrupted
    print("4. Marking session as interrupted...")
    db_manager.mark_session_interrupted(session_id)
    
    # Test list incomplete sessions
    print("5. Testing list incomplete sessions...")
    sessions = db_manager.get_incomplete_sessions()
    print(f"   Found {len(sessions)} incomplete sessions")
    
    # Test load resume state
    print("6. Testing load resume state...")
    resume_data = db_manager.load_crawl_state(session_id)
    if resume_data:
        print("   ✅ Resume data loaded successfully")
        print(f"   - Session ID: {resume_data['session_data']['id']}")
        print(f"   - Start URL: {resume_data['session_data']['start_url']}")
        print(f"   - Visited URLs: {len(resume_data['visited_urls'])}")
        print(f"   - Pending URLs: {len(resume_data['pending_urls'])}")
    else:
        print("   ❌ Failed to load resume data")
    
    print("\n7. Testing crawler initialization with resume...")
    try:
        crawler = WebCrawler(
            max_pages=10,
            output_dir="downloaded_pages",
            resume_session=session_id,
            use_database=True
        )
        print("   ✅ Crawler initialized with resume session")
        print(f"   - Downloaded pages: {crawler.downloaded_pages}")
        print(f"   - Visited URLs: {len(crawler.visited_urls)}")
        print(f"   - Queue size: {crawler.crawl_queue.qsize()}")
    except Exception as e:
        print(f"   ❌ Failed to initialize crawler with resume: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_resume_functionality()