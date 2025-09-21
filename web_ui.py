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
            cursor.execute("SELECT COUNT(*) FROM crawled_pages")
            total_pages = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM crawled_pages WHERE status_code BETWEEN 200 AND 299")
            successful = cursor.fetchone()[0]
            success_rate = (successful / total_pages * 100) if total_pages > 0 else 0
            
            # Total errors
            cursor.execute("SELECT COUNT(*) FROM crawled_pages WHERE status_code >= 400")
            total_errors = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM crawled_pages")
            total_sessions = cursor.fetchone()[0]
            
            # Data size
            cursor.execute("SELECT SUM(content_length) FROM crawled_pages WHERE content_length IS NOT NULL")
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
                    session_id,
                    MIN(crawl_timestamp) as start_time,
                    MAX(crawl_timestamp) as end_time,
                    COUNT(*) as page_count,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                    GROUP_CONCAT(DISTINCT domain, ', ') as domains
                FROM crawled_pages 
                GROUP BY session_id 
                ORDER BY session_id DESC 
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
            cursor.execute(f"SELECT COUNT(*) FROM crawled_pages {where_clause}", params)
            total = cursor.fetchone()[0]
            
            # Get paginated results
            offset = (page - 1) * per_page
            cursor.execute(f"""
                SELECT id, url, title, status_code, content_length, crawl_timestamp, domain, response_time
                FROM crawled_pages {where_clause}
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
            cursor.execute("SELECT DISTINCT session_id FROM crawled_pages ORDER BY session_id DESC")
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
            cursor.execute("SELECT DISTINCT domain FROM crawled_pages ORDER BY domain")
            domains = [row[0] for row in cursor.fetchall()]
            conn.close()
            return domains
            
        except Exception as e:
            print(f"Domains error: {e}")
            return []
    
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