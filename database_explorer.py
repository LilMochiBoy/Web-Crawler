#!/usr/bin/env python3
"""
Database Explorer for Web Crawler

This tool helps you explore and analyze the crawler database.
"""

import sqlite3
import argparse
import json
from pathlib import Path
from datetime import datetime


def connect_database(db_path: str):
    """Connect to the crawler database."""
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None


def list_sessions(conn):
    """List all crawling sessions."""
    cursor = conn.execute("""
        SELECT id, start_url, started_at, completed_at, max_depth, max_pages, 
               pages_crawled, total_errors
        FROM crawl_sessions 
        ORDER BY started_at DESC
    """)
    
    sessions = cursor.fetchall()
    
    if not sessions:
        print("No crawling sessions found.")
        return
    
    print("\n[SESSIONS] CRAWLING SESSIONS")
    print("=" * 80)
    for session in sessions:
        start_time = datetime.fromtimestamp(session['started_at']).strftime("%Y-%m-%d %H:%M:%S") if session['started_at'] else "Unknown"
        end_time = "In Progress"
        if session['completed_at']:
            end_time = datetime.fromtimestamp(session['completed_at']).strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Session ID: {session['id']}")
        print(f"Start URL: {session['start_url']}")
        print(f"Start Time: {start_time}")
        print(f"End Time: {end_time}")
        print(f"Settings: depth={session['max_depth']}, max_pages={session['max_pages']}")
        print(f"Results: pages={session['pages_crawled'] or 0}, errors={session['total_errors'] or 0}")
        print("-" * 80)


def show_session_details(conn, session_id):
    """Show detailed information about a specific session."""
    # Session info
    cursor = conn.execute("""
        SELECT * FROM crawl_sessions WHERE session_id = ?
    """, (session_id,))
    session = cursor.fetchone()
    
    if not session:
        print(f"❌ Session {session_id} not found.")
        return
    
    print(f"\n📊 SESSION {session_id} DETAILS")
    print("=" * 60)
    
    start_time = datetime.fromtimestamp(session['start_time']).strftime("%Y-%m-%d %H:%M:%S")
    end_time = "In Progress"
    if session['end_time']:
        end_time = datetime.fromtimestamp(session['end_time']).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Start URL: {session['start_url']}")
    print(f"Start Time: {start_time}")
    print(f"End Time: {end_time}")
    print(f"Max Depth: {session['max_depth']}")
    print(f"Max Pages: {session['max_pages']}")
    print(f"Pages Crawled: {session['pages_crawled'] or 0}")
    print(f"Errors: {session['errors_occurred'] or 0}")
    
    # Pages statistics
    cursor = conn.execute("""
        SELECT COUNT(*) as total, 
               AVG(response_time) as avg_response_time,
               SUM(content_length) as total_bytes
        FROM pages WHERE session_id = ?
    """, (session_id,))
    
    stats = cursor.fetchone()
    if stats['total'] > 0:
        print(f"\n📄 PAGES STATISTICS")
        print(f"Total Pages: {stats['total']}")
        print(f"Average Response Time: {stats['avg_response_time']:.2f}s")
        print(f"Total Bytes: {stats['total_bytes']:,} bytes ({stats['total_bytes']/(1024*1024):.2f} MB)")
    
    # Domain breakdown
    cursor = conn.execute("""
        SELECT 
            SUBSTR(url, 1, INSTR(url, '/', 8) - 1) as domain,
            COUNT(*) as page_count
        FROM pages 
        WHERE session_id = ? 
        GROUP BY domain
        ORDER BY page_count DESC
    """, (session_id,))
    
    domains = cursor.fetchall()
    if domains:
        print(f"\n🌐 DOMAINS CRAWLED")
        for domain in domains[:10]:  # Show top 10
            print(f"  {domain['domain']}: {domain['page_count']} pages")
    
    # Recent errors
    cursor = conn.execute("""
        SELECT url, error_type, error_message, timestamp
        FROM errors 
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 5
    """, (session_id,))
    
    errors = cursor.fetchall()
    if errors:
        print(f"\n❌ RECENT ERRORS")
        for error in errors:
            timestamp = datetime.fromtimestamp(error['timestamp']).strftime("%H:%M:%S")
            print(f"  [{timestamp}] {error['error_type']}: {error['url']}")
            if error['error_message']:
                print(f"    └─ {error['error_message'][:100]}")


def export_session_data(conn, session_id, output_file):
    """Export session data to JSON."""
    try:
        # Get session info
        cursor = conn.execute("SELECT * FROM crawl_sessions WHERE session_id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            print(f"❌ Session {session_id} not found.")
            return
        
        # Get all pages
        cursor = conn.execute("""
            SELECT url, title, status_code, content_type, content_length, 
                   response_time, timestamp, extracted_data
            FROM pages WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        pages = cursor.fetchall()
        
        # Get all errors
        cursor = conn.execute("""
            SELECT url, error_type, error_message, timestamp
            FROM errors WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        errors = cursor.fetchall()
        
        # Build export data
        export_data = {
            'session_info': dict(session),
            'pages': [dict(row) for row in pages],
            'errors': [dict(row) for row in errors],
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Convert extracted_data JSON strings back to objects
        for page in export_data['pages']:
            if page['extracted_data']:
                try:
                    page['extracted_data'] = json.loads(page['extracted_data'])
                except:
                    pass  # Keep as string if parsing fails
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Session {session_id} data exported to: {output_file}")
        print(f"   📄 Pages: {len(export_data['pages'])}")
        print(f"   ❌ Errors: {len(export_data['errors'])}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


def query_pages(conn, session_id=None, domain=None, limit=10):
    """Query pages with optional filters."""
    sql = "SELECT url, title, status_code, content_type, timestamp FROM pages"
    params = []
    conditions = []
    
    if session_id:
        conditions.append("session_id = ?")
        params.append(session_id)
    
    if domain:
        conditions.append("url LIKE ?")
        params.append(f"%{domain}%")
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += f" ORDER BY timestamp DESC LIMIT {limit}"
    
    cursor = conn.execute(sql, params)
    pages = cursor.fetchall()
    
    if not pages:
        print("📭 No pages found matching criteria.")
        return
    
    print(f"\n📄 PAGES ({len(pages)} results)")
    print("=" * 80)
    for page in pages:
        timestamp = datetime.fromtimestamp(page['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        title = page['title'][:50] + "..." if len(page['title']) > 50 else page['title']
        print(f"[{timestamp}] {page['status_code']} - {title}")
        print(f"   URL: {page['url']}")
        print(f"   Type: {page['content_type']}")
        print("-" * 40)


def main():
    """Main function for database explorer."""
    parser = argparse.ArgumentParser(description="Explore Web Crawler Database")
    parser.add_argument("--db", default="downloaded_pages/crawler_data.db", 
                       help="Database file path")
    parser.add_argument("--sessions", action="store_true", 
                       help="List all crawling sessions")
    parser.add_argument("--session", type=str, 
                       help="Show details for specific session")
    parser.add_argument("--export", type=str, 
                       help="Export session data to JSON file")
    parser.add_argument("--pages", action="store_true", 
                       help="Query pages")
    parser.add_argument("--domain", type=str, 
                       help="Filter by domain")
    parser.add_argument("--limit", type=int, default=10, 
                       help="Limit number of results")
    
    args = parser.parse_args()
    
    # Connect to database
    conn = connect_database(args.db)
    if not conn:
        return
    
    try:
        if args.sessions:
            list_sessions(conn)
        elif args.session:
            if args.export:
                export_session_data(conn, args.session, args.export)
            else:
                show_session_details(conn, args.session)
        elif args.pages:
            query_pages(conn, domain=args.domain, limit=args.limit)
        else:
            # Default: show recent sessions
            list_sessions(conn)
            
    finally:
        conn.close()


if __name__ == "__main__":
    main()