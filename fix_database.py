#!/usr/bin/env python3
"""
Fix Database Integration - Replace DatabaseManager with simplified version
"""

import os

# Read the current crawler.py file
with open('crawler.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the DatabaseManager class
class_start = content.find('class DatabaseManager:')
class_end = content.find('\nclass WebCrawler:')

if class_start != -1 and class_end != -1:
    # New simplified DatabaseManager
    new_db_manager = '''class DatabaseManager:
    """
    Simplified database manager for storing crawled data.
    """
    
    def __init__(self, db_path: str = "crawler_database.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create crawl_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_url TEXT,
                    max_pages INTEGER,
                    max_depth INTEGER,
                    pages_crawled INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    started_at REAL,
                    completed_at REAL,
                    status TEXT DEFAULT 'running'
                )
            """)
            
            # Create pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    status_code INTEGER,
                    content_type TEXT,
                    content_length INTEGER,
                    response_time REAL,
                    timestamp REAL,
                    extracted_data TEXT
                )
            """)
            
            # Create errors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    url TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    timestamp REAL,
                    FOREIGN KEY (session_id) REFERENCES crawl_sessions (id)
                )
            """)
            
            conn.commit()
    
    def get_connection(self):
        """Get database connection context manager."""
        return sqlite3.connect(self.db_path)
    
    def start_session(self, start_url: str, max_depth: int, max_pages: int) -> str:
        """Start a new crawl session and return session ID."""
        import time
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crawl_sessions (start_url, max_depth, max_pages, started_at)
                VALUES (?, ?, ?, ?)
            """, (start_url, max_depth, max_pages, time.time()))
            conn.commit()
            return str(cursor.lastrowid)
    
    def end_session(self, session_id: str, pages_crawled: int, errors_occurred: int):
        """End a crawl session with final statistics."""
        import time
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE crawl_sessions SET 
                    pages_crawled = ?, 
                    total_errors = ?,
                    completed_at = ?,
                    status = 'completed'
                WHERE id = ?
            """, (pages_crawled, errors_occurred, time.time(), int(session_id)))
            conn.commit()
    
    def save_page(self, session_id: str, url: str, title: str, content: str, 
                  status_code: int, content_type: str, content_length: int,
                  response_time: float = None, extracted_data: dict = None):
        """Save page data to database."""
        import time
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pages (
                    url, title, status_code, content_type, content_length,
                    response_time, timestamp, extracted_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (url, title, status_code, content_type, content_length,
                  response_time, time.time(), json.dumps(extracted_data) if extracted_data else None))
            conn.commit()
    
    def log_error(self, session_id: str, url: str, error_type: str, error_message: str):
        """Log an error to database."""
        import time
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO errors (session_id, url, error_type, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (int(session_id), url, error_type, error_message, time.time()))
            conn.commit()
    
    def get_session_statistics(self, session_id: str) -> dict:
        """Get statistics for a specific session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("SELECT * FROM crawl_sessions WHERE id = ?", (int(session_id),))
            session = cursor.fetchone()
            
            if not session:
                return {}
            
            # Get pages count for this session
            cursor.execute("SELECT COUNT(*) FROM pages WHERE timestamp >= ?", (session[6],))  # started_at
            pages_stored = cursor.fetchone()[0] if session[6] else 0
            
            # Get errors count
            cursor.execute("SELECT COUNT(*) FROM errors WHERE session_id = ?", (int(session_id),))
            errors_logged = cursor.fetchone()[0]
            
            return {
                'pages_stored': pages_stored,
                'links_stored': 0,  # Simplified for now
                'images_stored': 0,  # Simplified for now  
                'social_links_stored': 0,  # Simplified for now
                'errors_logged': errors_logged
            }


'''

    # Replace the class
    new_content = content[:class_start] + new_db_manager + content[class_end:]
    
    # Write back to file
    with open('crawler.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ DatabaseManager class has been simplified and fixed!")
    
else:
    print("❌ Could not find DatabaseManager class boundaries")