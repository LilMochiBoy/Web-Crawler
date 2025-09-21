#!/usr/bin/env python3
"""
Check database sessions
"""

import sqlite3
import datetime

db_path = "downloaded_pages/crawler_data.db"

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("All sessions in database:")
        print("=" * 60)
        cursor.execute("""
            SELECT id, start_url, status, pages_crawled, max_pages, started_at 
            FROM crawl_sessions 
            ORDER BY id DESC
        """)
        
        sessions = cursor.fetchall()
        for session in sessions:
            session_id, start_url, status, pages_crawled, max_pages, started_at = session
            if started_at:
                started_time = datetime.datetime.fromtimestamp(started_at).strftime("%Y-%m-%d %H:%M:%S")
            else:
                started_time = "Unknown"
            
            print(f"Session {session_id}:")
            print(f"  URL: {start_url or 'Not recorded'}")
            print(f"  Status: {status}")
            print(f"  Progress: {pages_crawled}/{max_pages}")
            print(f"  Started: {started_time}")
            print()
            
        print("\nQueue state for interrupted sessions:")
        print("=" * 60)
        cursor.execute("""
            SELECT qs.session_id, qs.url, qs.depth, cs.status
            FROM queue_state qs
            JOIN crawl_sessions cs ON qs.session_id = cs.id
            WHERE cs.status = 'interrupted'
            LIMIT 10
        """)
        
        queue_data = cursor.fetchall()
        if queue_data:
            for item in queue_data:
                session_id, url, depth, status = item
                print(f"Session {session_id} (status: {status}): {url} (depth: {depth})")
        else:
            print("No queue data found for interrupted sessions")

except Exception as e:
    print(f"Error: {e}")