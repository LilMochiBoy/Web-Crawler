#!/usr/bin/env python3
"""
Web UI for the Web Crawler
Provides a Flask-based web interface for managing and monitoring crawls
"""

import os
import sys
import json
import sqlite3
import threading
import subprocess
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("Warning: Flask-SocketIO not available. Real-time updates disabled.")
    SocketIO = None
    emit = None
    SOCKETIO_AVAILABLE = False
import queue
from pathlib import Path

# Import our existing crawler components
from crawler import WebCrawler
from data_exporter import DataExporter
from search_database import SearchDatabase
# Note: database_explorer is a script, not a class, so we don't import it here

class CrawlerWebUI:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'web-crawler-secret-key-2025'
        
        if SOCKETIO_AVAILABLE:
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        else:
            self.socketio = None
        
        # Active crawlers management
        self.active_crawls = {}
        self.crawl_threads = {}
        
        # Database path
        self.db_path = os.path.join('downloaded_pages', 'crawler_data.db')
        
        # Initialize search database
        self.search_db = None
        if os.path.exists(self.db_path):
            try:
                self.search_db = SearchDatabase(self.db_path)
            except Exception as e:
                print(f"Warning: Could not initialize search functionality: {e}")
        
        self.setup_routes()
        if SOCKETIO_AVAILABLE:
            self.setup_socketio()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard"""
            stats = self.get_dashboard_stats()
            recent_crawls = self.get_recent_crawls()
            return render_template('dashboard.html', stats=stats, recent_crawls=recent_crawls)
        
        @self.app.route('/start_crawl', methods=['POST'])
        def start_crawl():
            """Start a new crawl"""
            try:
                url = request.form.get('url', '').strip()
                max_pages = int(request.form.get('max_pages', 100))
                workers = int(request.form.get('workers', 3))
                delay = float(request.form.get('delay', 1.0))
                
                if not url:
                    flash('URL is required', 'error')
                    return redirect(url_for('dashboard'))
                
                # Generate crawl ID
                crawl_id = f"web_crawl_{int(time.time())}"
                
                # Start crawler in background thread
                thread = threading.Thread(
                    target=self.run_crawl_background,
                    args=(crawl_id, url, max_pages, workers, delay)
                )
                thread.daemon = True
                thread.start()
                
                self.crawl_threads[crawl_id] = thread
                
                flash(f'Crawl started: {url}', 'success')
                return redirect(url_for('monitor', crawl_id=crawl_id))
                
            except Exception as e:
                flash(f'Error starting crawl: {str(e)}', 'error')
                return redirect(url_for('dashboard'))
        
        @self.app.route('/monitor/<crawl_id>')
        def monitor(crawl_id):
            """Monitor active crawl"""
            if crawl_id not in self.active_crawls:
                flash('Crawl not found', 'error')
                return redirect(url_for('dashboard'))
            
            crawl_info = self.active_crawls[crawl_id]
            return render_template('monitor.html', crawl_id=crawl_id, crawl_info=crawl_info)
        
        @self.app.route('/stop_crawl/<crawl_id>', methods=['POST'])
        def stop_crawl(crawl_id):
            """Stop an active crawl"""
            if crawl_id in self.active_crawls:
                self.active_crawls[crawl_id]['status'] = 'stopping'
                # The crawler will check this status and stop
                flash('Crawl stopping...', 'info')
            return redirect(url_for('dashboard'))
        
        @self.app.route('/results')
        def results():
            """Browse crawl results"""
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            session_filter = request.args.get('session', '')
            domain_filter = request.args.get('domain', '')
            
            results = self.get_paginated_results(page, per_page, session_filter, domain_filter)
            sessions = self.get_available_sessions()
            domains = self.get_available_domains()
            
            return render_template('results.html', 
                                 results=results, 
                                 sessions=sessions, 
                                 domains=domains,
                                 current_page=page,
                                 session_filter=session_filter,
                                 domain_filter=domain_filter)
        
        @self.app.route('/export_data', methods=['POST'])
        def export_data():
            """Export crawled data"""
            try:
                format_type = request.form.get('format', 'csv')
                session_filter = request.form.get('session', '')
                include_stats = request.form.get('include_stats') == 'on'
                
                exporter = DataExporter(self.db_path)
                
                # Generate export
                if format_type == 'csv':
                    output_file = exporter.export_to_csv(
                        session_filter=int(session_filter) if session_filter else None,
                        include_stats=False
                    )
                elif format_type == 'json':
                    output_file = exporter.export_to_json(
                        session_filter=int(session_filter) if session_filter else None,
                        include_stats=include_stats
                    )
                elif format_type == 'html':
                    output_file = exporter.export_to_html()
                else:
                    flash('Invalid export format', 'error')
                    return redirect(url_for('results'))
                
                flash(f'Export generated: {os.path.basename(output_file)}', 'success')
                
            except Exception as e:
                flash(f'Export error: {str(e)}', 'error')
            
            return redirect(url_for('results'))
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for dashboard stats"""
            return jsonify(self.get_dashboard_stats())
        
        @self.app.route('/api/crawl_status/<crawl_id>')
        def api_crawl_status(crawl_id):
            """API endpoint for crawl status"""
            if crawl_id in self.active_crawls:
                return jsonify(self.active_crawls[crawl_id])
            return jsonify({'error': 'Crawl not found'}), 404
        
        # Search Routes
        @self.app.route('/search')
        def search():
            """Advanced search page"""
            if not self.search_db:
                flash('Search functionality not available. Database not found.', 'error')
                return redirect(url_for('dashboard'))
            
            # Get filter options
            filter_options = self.search_db.get_filter_options()
            
            return render_template('search.html', filter_options=filter_options)
        
        @self.app.route('/search_results')
        def search_results():
            """Search results page"""
            if not self.search_db:
                return jsonify({'error': 'Search not available'}), 503
            
            try:
                query = request.args.get('q', '').strip()
                page = int(request.args.get('page', 1))
                per_page = min(int(request.args.get('per_page', 20)), 100)  # Limit results
                
                # Build filters from request
                filters = {}
                
                # Domain filter
                domains = request.args.getlist('domains')
                if domains:
                    filters['domains'] = domains
                
                # Date range
                date_from = request.args.get('date_from')
                date_to = request.args.get('date_to')
                if date_from:
                    try:
                        filters['date_from'] = int(datetime.fromisoformat(date_from.replace('Z', '+00:00')).timestamp())
                    except:
                        pass
                if date_to:
                    try:
                        filters['date_to'] = int(datetime.fromisoformat(date_to.replace('Z', '+00:00')).timestamp())
                    except:
                        pass
                
                # Content type filter
                content_types = request.args.getlist('content_types')
                if content_types:
                    filters['content_types'] = content_types
                
                # Size filters
                min_length = request.args.get('min_length')
                max_length = request.args.get('max_length')
                if min_length:
                    try:
                        filters['min_length'] = int(min_length)
                    except:
                        pass
                if max_length:
                    try:
                        filters['max_length'] = int(max_length)
                    except:
                        pass
                
                # Perform search
                offset = (page - 1) * per_page
                search_result = self.search_db.search_content(
                    query=query,
                    filters=filters,
                    limit=per_page,
                    offset=offset
                )
                
                # Format results for display
                formatted_results = []
                for result in search_result['results']:
                    # Parse extracted data
                    extracted_data = {}
                    if result.get('extracted_data'):
                        try:
                            extracted_data = json.loads(result['extracted_data'])
                        except:
                            pass
                    
                    formatted_result = {
                        'url': result['url'],
                        'title': result.get('title') or 'No Title',
                        'domain': result.get('domain', ''),
                        'content_type': result.get('content_type', ''),
                        'content_length': result.get('content_length', 0),
                        'timestamp': result.get('timestamp', 0),
                        'response_time': result.get('response_time', 0),
                        'status_code': result.get('status_code', 0),
                        'snippet': self.get_content_snippet(extracted_data.get('text_content', ''), query),
                        'rank': result.get('rank', 0)
                    }
                    formatted_results.append(formatted_result)
                
                # Return JSON for AJAX requests or HTML for direct access
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'results': formatted_results,
                        'total_count': search_result['total_count'],
                        'query': query,
                        'page': page,
                        'per_page': per_page,
                        'has_next': search_result['has_next'],
                        'has_prev': search_result['has_prev']
                    })
                else:
                    return render_template('search_results.html', 
                                         results=formatted_results,
                                         search_data=search_result,
                                         query=query,
                                         page=page,
                                         per_page=per_page)
                
            except Exception as e:
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({'error': str(e)}), 500
                flash(f'Search error: {str(e)}', 'error')
                return redirect(url_for('search'))
        
        @self.app.route('/api/search_suggestions')
        def api_search_suggestions():
            """API endpoint for search autocomplete suggestions"""
            if not self.search_db:
                return jsonify([])
            
            query_prefix = request.args.get('q', '').strip()
            if len(query_prefix) < 2:
                return jsonify([])
            
            try:
                suggestions = self.search_db.get_search_suggestions(query_prefix)
                return jsonify(suggestions)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/filter_options')
        def api_filter_options():
            """API endpoint for getting available filter options"""
            if not self.search_db:
                return jsonify({})
            
            try:
                options = self.search_db.get_filter_options()
                return jsonify(options)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def setup_socketio(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
        
        @self.socketio.on('subscribe_crawl')
        def handle_subscribe(data):
            crawl_id = data.get('crawl_id')
            if crawl_id:
                # Client wants updates for this crawl
                pass
    
    def run_crawl_background(self, crawl_id, url, max_pages, workers, delay):
        """Run crawler in background thread"""
        try:
            # Initialize crawl tracking
            self.active_crawls[crawl_id] = {
                'url': url,
                'max_pages': max_pages,
                'workers': workers,
                'delay': delay,
                'status': 'running',
                'pages_crawled': 0,
                'pages_found': 0,
                'errors': 0,
                'start_time': time.time(),
                'current_url': '',
                'data_size': 0
            }
            
            # Create crawler instance
            config = {
                'max_pages': max_pages,
                'delay': delay,
                'workers': workers,
                'timeout': 30,
                'user_agent': 'WebCrawler-UI/1.0',
                'respect_robots': True,
                'content_types': ['text/html']
            }
            
            crawler = WebCrawler(config)
            
            # Custom progress callback
            def progress_callback(stats):
                if crawl_id in self.active_crawls:
                    self.active_crawls[crawl_id].update({
                        'pages_crawled': stats.get('pages_processed', 0),
                        'pages_found': stats.get('total_found', 0),
                        'errors': stats.get('errors', 0),
                        'current_url': stats.get('current_url', ''),
                        'data_size': stats.get('total_size', 0)
                    })
                    
                    # Emit real-time update
                    if SOCKETIO_AVAILABLE and self.socketio:
                        self.socketio.emit('crawl_update', {
                            'crawl_id': crawl_id,
                            'data': self.active_crawls[crawl_id]
                        })
                
                # Check if we should stop
                return self.active_crawls.get(crawl_id, {}).get('status') != 'stopping'
            
            # Start crawling
            crawler.crawl(url, progress_callback=progress_callback)
            
            # Mark as completed
            if crawl_id in self.active_crawls:
                self.active_crawls[crawl_id]['status'] = 'completed'
                self.active_crawls[crawl_id]['end_time'] = time.time()
                
                # Final update
                self.socketio.emit('crawl_complete', {
                    'crawl_id': crawl_id,
                    'data': self.active_crawls[crawl_id]
                }) if SOCKETIO_AVAILABLE and self.socketio else None
        
        except Exception as e:
            print(f"Crawl error: {e}")
            if crawl_id in self.active_crawls:
                self.active_crawls[crawl_id]['status'] = 'error'
                self.active_crawls[crawl_id]['error'] = str(e)
                
                self.socketio.emit('crawl_error', {
                    'crawl_id': crawl_id,
                    'error': str(e)
                }) if SOCKETIO_AVAILABLE and self.socketio else None
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {
                    'total_pages': 0,
                    'active_crawls': len(self.active_crawls),
                    'success_rate': 0,
                    'total_errors': 0,
                    'total_sessions': 0,
                    'data_size': 0
                }
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total pages
            cursor.execute("SELECT COUNT(*) FROM pages")
            total_pages = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM pages WHERE status_code BETWEEN 200 AND 299")
            successful = cursor.fetchone()[0]
            success_rate = (successful / total_pages * 100) if total_pages > 0 else 0
            
            # Total errors
            cursor.execute("SELECT COUNT(*) FROM pages WHERE status_code >= 400")
            total_errors = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute("SELECT COUNT(DISTINCT id) FROM crawl_sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Data size
            cursor.execute("SELECT SUM(content_length) FROM pages WHERE content_length IS NOT NULL")
            result = cursor.fetchone()[0]
            data_size = result if result else 0
            
            conn.close()
            
            return {
                'total_pages': total_pages,
                'active_crawls': len([c for c in self.active_crawls.values() if c['status'] == 'running']),
                'success_rate': round(success_rate, 1),
                'total_errors': total_errors,
                'total_sessions': total_sessions,
                'data_size': data_size
            }
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {
                'total_pages': 0,
                'active_crawls': 0,
                'success_rate': 0,
                'total_errors': 0,
                'total_sessions': 0,
                'data_size': 0
            }
    
    def get_recent_crawls(self):
        """Get recent crawl sessions"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    cs.id as session_id,
                    cs.started_at as start_time,
                    cs.completed_at as end_time,
                    cs.pages_crawled as page_count,
                    cs.total_errors as error_count,
                    cs.start_url as domains
                FROM crawl_sessions cs
                ORDER BY cs.id DESC 
                LIMIT 10
            """)
            
            crawls = []
            for row in cursor.fetchall():
                session_id, start_time, end_time, page_count, error_count, domains = row
                
                status = 'completed'
                if session_id in [c for c in self.active_crawls.keys()]:
                    status = self.active_crawls[session_id]['status']
                
                crawls.append({
                    'session_id': session_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'page_count': page_count,
                    'error_count': error_count or 0,
                    'domains': domains,
                    'status': status
                })
            
            conn.close()
            return crawls
            
        except Exception as e:
            print(f"Recent crawls error: {e}")
            return []
    
    def get_paginated_results(self, page, per_page, session_filter='', domain_filter=''):
        """Get paginated crawl results"""
        try:
            if not os.path.exists(self.db_path):
                return {'pages': [], 'total': 0, 'has_next': False, 'has_prev': False}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with filters
            where_conditions = []
            params = []
            
            if session_filter:
                where_conditions.append("session_id = ?")
                params.append(session_filter)
            
            if domain_filter:
                where_conditions.append("domain = ?")
                params.append(domain_filter)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM pages {where_clause}", params)
            total = cursor.fetchone()[0]
            
            # Get paginated results
            offset = (page - 1) * per_page
            cursor.execute(f"""
                SELECT id, url, title, status_code, content_length, timestamp,
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
                       END as domain,
                       response_time
                FROM pages {where_clause}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, params + [per_page, offset])
            
            pages = []
            for row in cursor.fetchall():
                pages.append({
                    'id': row[0],
                    'url': row[1],
                    'title': row[2] or 'No title',
                    'status_code': row[3],
                    'content_length': row[4] or 0,
                    'crawl_timestamp': row[5],
                    'domain': row[6],
                    'response_time': row[7] or 0
                })
            
            conn.close()
            
            return {
                'pages': pages,
                'total': total,
                'has_next': (page * per_page) < total,
                'has_prev': page > 1,
                'page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            print(f"Results error: {e}")
            return {'pages': [], 'total': 0, 'has_next': False, 'has_prev': False}
    
    def get_available_sessions(self):
        """Get list of available sessions"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM crawl_sessions ORDER BY id DESC")
            sessions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return sessions
            
        except Exception as e:
            print(f"Sessions error: {e}")
            return []
    
    def get_available_domains(self):
        """Get list of available domains"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""SELECT DISTINCT 
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
                ORDER BY domain""")
            domains = [row[0] for row in cursor.fetchall()]
            conn.close()
            return domains
            
        except Exception as e:
            print(f"Domains error: {e}")
            return []
    
    def get_content_snippet(self, content, query, max_length=200):
        """Extract a snippet of content highlighting the search query"""
        if not content or not query:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find the first occurrence of any query term
        terms = query_lower.split()
        best_pos = len(content)
        
        for term in terms:
            pos = content_lower.find(term)
            if pos != -1 and pos < best_pos:
                best_pos = pos
        
        if best_pos == len(content):
            # No terms found, return beginning
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # Extract snippet around the found term
        start = max(0, best_pos - max_length // 3)
        end = min(len(content), start + max_length)
        
        snippet = content[start:end]
        
        # Add ellipsis if we truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """Run the web UI"""
        print(f"🕷️  Web Crawler UI starting...")
        print(f"🌐 Open your browser to: http://{host}:{port}")
        print(f"📊 Dashboard, monitoring, and data export available")
        print(f"⌨️  Terminal crawler still works: python crawler.py <url>")
        print()
        
        if SOCKETIO_AVAILABLE and self.socketio:
            self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        else:
            print("⚠️  Running without real-time updates (SocketIO not available)")
            self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point"""
    web_ui = CrawlerWebUI()
    
    try:
        web_ui.run()
    except KeyboardInterrupt:
        print("\n🛑 Web UI stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()