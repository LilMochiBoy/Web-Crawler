#!/usr/bin/env python3
"""
Database Search Enhancement
Adds full-text search capabilities to the crawler database.
"""

import sqlite3
import json
from pathlib import Path
import logging

class SearchDatabase:
    """Enhanced database manager with full-text search capabilities."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_search_tables()
    
    def setup_search_tables(self):
        """Setup full-text search tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable FTS5 if not already enabled
            try:
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='pages_fts'")
                if not cursor.fetchone():
                    # Create FTS5 virtual table for content search
                    cursor.execute("""
                        CREATE VIRTUAL TABLE pages_fts USING fts5(
                            url,
                            title,
                            content,
                            domain,
                            tokenize='porter'
                        )
                    """)
                    
                    # Populate FTS table with existing data
                    cursor.execute("""
                        INSERT INTO pages_fts (url, title, content, domain)
                        SELECT 
                            url,
                            COALESCE(title, ''),
                            COALESCE(json_extract(extracted_data, '$.text_content'), ''),
                            CASE 
                                WHEN url LIKE 'http://%' THEN 
                                    CASE 
                                        WHEN instr(substr(url, 8), '/') = 0 THEN substr(url, 8)
                                        ELSE substr(url, 8, instr(substr(url, 8), '/') - 1)
                                    END
                                WHEN url LIKE 'https://%' THEN 
                                    CASE 
                                        WHEN instr(substr(url, 9), '/') = 0 THEN substr(url, 9)
                                        ELSE substr(url, 9, instr(substr(url, 9), '/') - 1)
                                    END
                                ELSE url
                            END as domain
                        FROM pages 
                        WHERE extracted_data IS NOT NULL
                    """)
                    
                    print("✅ Full-text search index created and populated")
                
            except sqlite3.OperationalError as e:
                if "no such module: fts5" in str(e):
                    print("⚠️  FTS5 not available, falling back to LIKE queries")
                    self.fts_available = False
                else:
                    raise
            else:
                self.fts_available = True
                
            # Create indexes for faster filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_timestamp ON pages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_content_type ON pages(content_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_status_code ON pages(status_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_content_length ON pages(content_length)")
            
            conn.commit()
    
    def search_content(self, query: str, filters: dict = None, limit: int = 100, offset: int = 0):
        """
        Search through crawled content with advanced filters.
        
        Args:
            query: Search query text
            filters: Dictionary of filters (domain, date_range, content_type, etc.)
            limit: Maximum results to return
            offset: Results offset for pagination
            
        Returns:
            Dictionary with results and metadata
        """
        filters = filters or {}
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build search query based on FTS availability
            if self.fts_available and query.strip():
                return self._search_with_fts(cursor, query, filters, limit, offset)
            else:
                return self._search_with_like(cursor, query, filters, limit, offset)
    
    def _search_with_fts(self, cursor, query: str, filters: dict, limit: int, offset: int):
        """Search using FTS5 full-text search."""
        # Simple FTS search first
        fts_query = """
            SELECT 
                fts.url,
                fts.title,
                fts.content,
                fts.domain
            FROM pages_fts fts
            WHERE fts MATCH ?
        """
        
        # Get page data and join with FTS results
        base_query = """
            SELECT 
                p.url,
                p.title,
                p.status_code,
                p.content_type,
                p.content_length,
                p.response_time,
                p.timestamp,
                p.extracted_data,
                0 as rank,
                CASE 
                    WHEN p.url LIKE 'http://%' THEN 
                        CASE 
                            WHEN instr(substr(p.url, 8), '/') = 0 THEN substr(p.url, 8)
                            ELSE substr(p.url, 8, instr(substr(p.url, 8), '/') - 1)
                        END
                    WHEN p.url LIKE 'https://%' THEN 
                        CASE 
                            WHEN instr(substr(p.url, 9), '/') = 0 THEN substr(p.url, 9)
                            ELSE substr(p.url, 9, instr(substr(p.url, 9), '/') - 1)
                        END
                    ELSE p.url
                END as domain
            FROM pages p
            WHERE p.url IN (
                SELECT url FROM pages_fts WHERE pages_fts MATCH ?
            )
        """
        
        params = [query]
        where_clauses = []
        
        # Add filters
        if filters.get('domains'):
            domain_placeholders = ','.join('?' * len(filters['domains']))
            where_clauses.append(f"domain IN ({domain_placeholders})")
            params.extend(filters['domains'])
        
        if filters.get('date_from'):
            where_clauses.append("p.timestamp >= ?")
            params.append(filters['date_from'])
            
        if filters.get('date_to'):
            where_clauses.append("p.timestamp <= ?")
            params.append(filters['date_to'])
        
        if filters.get('content_types'):
            type_placeholders = ','.join('?' * len(filters['content_types']))
            where_clauses.append(f"p.content_type IN ({type_placeholders})")
            params.extend(filters['content_types'])
        
        if filters.get('min_length'):
            where_clauses.append("p.content_length >= ?")
            params.append(filters['min_length'])
            
        if filters.get('max_length'):
            where_clauses.append("p.content_length <= ?")
            params.append(filters['max_length'])
        
        # Add WHERE clauses
        if where_clauses:
            base_query += " AND " + " AND ".join(where_clauses)
        
        # Add ordering and pagination
        base_query += " ORDER BY p.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute search
        cursor.execute(base_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Get total count for pagination - simplified
        count_query = """
            SELECT COUNT(*)
            FROM pages p
            WHERE p.url IN (
                SELECT url FROM pages_fts WHERE pages_fts MATCH ?
            )
        """
        count_params = [query]
        
        # Add filters for count query
        filter_clauses = []
        if filters.get('domains'):
            domain_placeholders = ','.join('?' * len(filters['domains']))
            filter_clauses.append(f"CASE WHEN p.url LIKE 'http://%' THEN CASE WHEN instr(substr(p.url, 8), '/') = 0 THEN substr(p.url, 8) ELSE substr(p.url, 8, instr(substr(p.url, 8), '/') - 1) END WHEN p.url LIKE 'https://%' THEN CASE WHEN instr(substr(p.url, 9), '/') = 0 THEN substr(p.url, 9) ELSE substr(p.url, 9, instr(substr(p.url, 9), '/') - 1) END ELSE p.url END IN ({domain_placeholders})")
            count_params.extend(filters['domains'])
        
        if filters.get('date_from'):
            filter_clauses.append("p.timestamp >= ?")
            count_params.append(filters['date_from'])
            
        if filters.get('date_to'):
            filter_clauses.append("p.timestamp <= ?")
            count_params.append(filters['date_to'])
        
        if filters.get('content_types'):
            type_placeholders = ','.join('?' * len(filters['content_types']))
            filter_clauses.append(f"p.content_type IN ({type_placeholders})")
            count_params.extend(filters['content_types'])
        
        if filters.get('min_length'):
            filter_clauses.append("p.content_length >= ?")
            count_params.append(filters['min_length'])
            
        if filters.get('max_length'):
            filter_clauses.append("p.content_length <= ?")
            count_params.append(filters['max_length'])
        
        if filter_clauses:
            count_query += " AND " + " AND ".join(filter_clauses)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        return {
            'results': results,
            'total_count': total_count,
            'query': query,
            'filters': filters,
            'has_next': offset + limit < total_count,
            'has_prev': offset > 0
        }
    
    def _search_with_like(self, cursor, query: str, filters: dict, limit: int, offset: int):
        """Fallback search using LIKE queries."""
        base_query = """
            SELECT 
                p.url,
                p.title,
                p.status_code,
                p.content_type,
                p.content_length,
                p.response_time,
                p.timestamp,
                p.extracted_data,
                0 as rank,
                CASE 
                    WHEN p.url LIKE 'http://%' THEN 
                        CASE 
                            WHEN instr(substr(p.url, 8), '/') = 0 THEN substr(p.url, 8)
                            ELSE substr(p.url, 8, instr(substr(p.url, 8), '/') - 1)
                        END
                    WHEN p.url LIKE 'https://%' THEN 
                        CASE 
                            WHEN instr(substr(p.url, 9), '/') = 0 THEN substr(p.url, 9)
                            ELSE substr(p.url, 9, instr(substr(p.url, 9), '/') - 1)
                        END
                    ELSE p.url
                END as domain
            FROM pages p
            WHERE 1=1
        """
        
        params = []
        where_clauses = []
        
        # Add search query
        if query.strip():
            search_terms = query.strip().split()
            search_conditions = []
            for term in search_terms:
                search_conditions.append(
                    "(p.title LIKE ? OR json_extract(p.extracted_data, '$.text_content') LIKE ? OR p.url LIKE ?)"
                )
                like_term = f"%{term}%"
                params.extend([like_term, like_term, like_term])
            
            if search_conditions:
                where_clauses.append("(" + " AND ".join(search_conditions) + ")")
        
        # Add filters (same as FTS version)
        if filters.get('domains'):
            domain_placeholders = ','.join('?' * len(filters['domains']))
            where_clauses.append(f"domain IN ({domain_placeholders})")
            params.extend(filters['domains'])
        
        if filters.get('date_from'):
            where_clauses.append("p.timestamp >= ?")
            params.append(filters['date_from'])
            
        if filters.get('date_to'):
            where_clauses.append("p.timestamp <= ?")
            params.append(filters['date_to'])
        
        if filters.get('content_types'):
            type_placeholders = ','.join('?' * len(filters['content_types']))
            where_clauses.append(f"p.content_type IN ({type_placeholders})")
            params.extend(filters['content_types'])
        
        if filters.get('min_length'):
            where_clauses.append("p.content_length >= ?")
            params.append(filters['min_length'])
            
        if filters.get('max_length'):
            where_clauses.append("p.content_length <= ?")
            params.append(filters['max_length'])
        
        # Add WHERE clauses
        if where_clauses:
            base_query += " AND " + " AND ".join(where_clauses)
        
        # Add ordering and pagination
        base_query += " ORDER BY p.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute search
        cursor.execute(base_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = base_query.replace(
            "SELECT p.url, p.title, p.status_code, p.content_type, p.content_length, p.response_time, p.timestamp, p.extracted_data, 0 as rank, CASE WHEN p.url LIKE 'http://%' THEN CASE WHEN instr(substr(p.url, 8), '/') = 0 THEN substr(p.url, 8) ELSE substr(p.url, 8, instr(substr(p.url, 8), '/') - 1) END WHEN p.url LIKE 'https://%' THEN CASE WHEN instr(substr(p.url, 9), '/') = 0 THEN substr(p.url, 9) ELSE substr(p.url, 9, instr(substr(p.url, 9), '/') - 1) END ELSE p.url END as domain",
            "SELECT COUNT(*)"
        ).replace(" ORDER BY p.timestamp DESC LIMIT ? OFFSET ?", "")
        
        cursor.execute(count_query, params[:-2])
        total_count = cursor.fetchone()[0]
        
        return {
            'results': results,
            'total_count': total_count,
            'query': query,
            'filters': filters,
            'has_next': offset + limit < total_count,
            'has_prev': offset > 0
        }
    
    def get_search_suggestions(self, query_prefix: str, limit: int = 10):
        """Get search suggestions based on existing content."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get popular terms from titles and domains
            cursor.execute("""
                SELECT DISTINCT 
                    CASE 
                        WHEN title LIKE ? THEN title
                        WHEN url LIKE ? THEN 
                            CASE 
                                WHEN url LIKE 'http://%' THEN substr(url, 8, instr(substr(url, 8), '/') - 1)
                                WHEN url LIKE 'https://%' THEN substr(url, 9, instr(substr(url, 9), '/') - 1)
                                ELSE url
                            END
                        ELSE NULL
                    END as suggestion
                FROM pages 
                WHERE suggestion IS NOT NULL
                ORDER BY suggestion
                LIMIT ?
            """, [f"%{query_prefix}%", f"%{query_prefix}%", limit])
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_filter_options(self):
        """Get available filter options from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get unique domains
            cursor.execute("""
                SELECT DISTINCT 
                    CASE 
                        WHEN p.url LIKE 'http://%' THEN 
                            CASE 
                                WHEN instr(substr(p.url, 8), '/') = 0 THEN substr(p.url, 8)
                                ELSE substr(p.url, 8, instr(substr(p.url, 8), '/') - 1)
                            END
                        WHEN p.url LIKE 'https://%' THEN 
                            CASE 
                                WHEN instr(substr(p.url, 9), '/') = 0 THEN substr(p.url, 9)
                                ELSE substr(p.url, 9, instr(substr(p.url, 9), '/') - 1)
                            END
                        ELSE p.url
                    END as domain
                FROM pages 
                WHERE domain IS NOT NULL
                ORDER BY domain
            """)
            domains = [row[0] for row in cursor.fetchall()]
            
            # Get unique content types
            cursor.execute("""
                SELECT DISTINCT content_type
                FROM pages 
                WHERE content_type IS NOT NULL
                ORDER BY content_type
            """)
            content_types = [row[0] for row in cursor.fetchall()]
            
            # Get date range
            cursor.execute("""
                SELECT 
                    MIN(timestamp) as min_date,
                    MAX(timestamp) as max_date,
                    COUNT(*) as total_pages
                FROM pages
            """)
            date_info = cursor.fetchone()
            
            return {
                'domains': domains,
                'content_types': content_types,
                'date_range': {
                    'min_date': date_info[0] if date_info[0] else 0,
                    'max_date': date_info[1] if date_info[1] else 0,
                    'total_pages': date_info[2] if date_info[2] else 0
                }
            }
    
    def add_page_to_search_index(self, url: str, title: str, content: str, domain: str):
        """Add a single page to the search index (for new crawls)."""
        if not self.fts_available:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO pages_fts (url, title, content, domain)
                    VALUES (?, ?, ?, ?)
                """, (url, title or '', content or '', domain))
                conn.commit()
            except sqlite3.Error as e:
                logging.warning(f"Failed to add page to search index: {e}")


def initialize_search_database(db_path: str = None):
    """Initialize search functionality for existing database."""
    if not db_path:
        # Find the database
        possible_paths = [
            Path("downloaded_pages/crawler_data.db"),
            Path("crawler_data.db"),
            Path("downloaded_pages/crawler_database.db")
        ]
        
        for path in possible_paths:
            if path.exists():
                db_path = str(path)
                break
        else:
            print("❌ No database found. Run a crawl first.")
            return None
    
    print(f"🔍 Setting up search functionality for {db_path}")
    search_db = SearchDatabase(db_path)
    print("✅ Search functionality ready!")
    return search_db


if __name__ == "__main__":
    # Test search functionality
    search_db = initialize_search_database()
    if search_db:
        print("\n🧪 Testing search...")
        results = search_db.search_content("python", limit=5)
        print(f"Found {results['total_count']} results for 'python'")
        for result in results['results'][:3]:
            print(f"  - {result['title']} ({result['domain']})")