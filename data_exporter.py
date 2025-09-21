#!/usr/bin/env python3
"""
Advanced Data Export and Reporting System for Web Crawler

This module provides comprehensive data export capabilities including:
- CSV exports for spreadsheet analysis
- JSON exports for programmatic use
- XML exports for structured data exchange
- HTML reports with charts and statistics
- Custom filtering and data transformation
"""

import sqlite3
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any, Optional
import argparse
from collections import Counter, defaultdict
import html
from urllib.parse import urlparse


class DataExporter:
    """
    Professional data export and reporting system for crawler data.
    """
    
    def __init__(self, db_path: str = "downloaded_pages/crawler_data.db"):
        """Initialize the data exporter with database connection."""
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure the database file exists."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    # ========================================
    # DATA RETRIEVAL METHODS
    # ========================================
    
    def get_pages_data(self, session_id: Optional[int] = None, 
                      domain_filter: Optional[str] = None,
                      keyword_filter: Optional[str] = None,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve pages data with optional filtering.
        
        Args:
            session_id: Filter by specific crawl session (not directly supported by current schema)
            domain_filter: Filter by domain (supports wildcards with %)
            keyword_filter: Filter by content containing keywords
            date_from: Filter by date from (YYYY-MM-DD format)
            date_to: Filter by date to (YYYY-MM-DD format)
            limit: Limit number of results returned
        """
        conn = self.get_connection()
        
        # Simplified query to match actual database schema
        query = """
        SELECT 
            p.id,
            p.url,
            p.title,
            p.status_code,
            p.content_length,
            p.content_type,
            p.timestamp as crawl_timestamp,
            p.response_time,
            p.extracted_data
        FROM pages p
        WHERE 1=1
        """
        
        params = []
        
        # Note: session_id filtering not available due to schema limitations
        if session_id:
            # For now, we'll filter by timestamp range if we know the session
            try:
                # Get session timing to approximate filtering
                session_conn = self.get_connection()
                session_cursor = session_conn.execute(
                    "SELECT started_at, completed_at FROM crawl_sessions WHERE id = ?", 
                    (session_id,)
                )
                session_data = session_cursor.fetchone()
                if session_data:
                    start_time, end_time = session_data
                    if start_time:
                        query += " AND p.timestamp >= ?"
                        params.append(start_time)
                    if end_time:
                        query += " AND p.timestamp <= ?"
                        params.append(end_time)
                session_conn.close()
            except Exception:
                # If session lookup fails, ignore session filter
                pass
        
        # Extract domain from URL for domain filtering
        if domain_filter:
            query += " AND p.url LIKE ?"
            params.append(f"%{domain_filter}%")
        
        if keyword_filter:
            query += " AND (p.title LIKE ? OR p.url LIKE ?)"
            params.append(f"%{keyword_filter}%")
            params.append(f"%{keyword_filter}%")
        
        if date_from:
            # Convert date to timestamp for comparison
            from datetime import datetime
            date_ts = datetime.strptime(date_from, '%Y-%m-%d').timestamp()
            query += " AND p.timestamp >= ?"
            params.append(date_ts)
        
        if date_to:
            # Convert date to timestamp for comparison
            from datetime import datetime
            date_ts = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S').timestamp()
            query += " AND p.timestamp <= ?"
            params.append(date_ts)
        
        query += " ORDER BY p.timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Add derived fields for compatibility
        for result in results:
            if result.get('url'):
                parsed = urlparse(result['url'])
                result['domain'] = parsed.netloc
                result['crawl_timestamp'] = datetime.fromtimestamp(result.get('timestamp', 0)).isoformat() if result.get('timestamp') else None
        
        conn.close()
        return results
    
    def get_links_data(self, session_id: Optional[int] = None) -> List[Dict]:
        """Retrieve links data - simplified for current schema."""
        return []  # Links not stored separately in current schema
    
    def get_images_data(self, session_id: Optional[int] = None) -> List[Dict]:
        """Retrieve images data - simplified for current schema.""" 
        return []  # Images not stored separately in current schema
    
    def get_sessions_data(self) -> List[Dict]:
        """Retrieve all crawl sessions data."""
        conn = self.get_connection()
        
        query = """
        SELECT 
            id,
            start_url,
            started_at as start_time,
            completed_at as end_time,
            max_pages,
            max_depth,
            pages_crawled,
            total_errors,
            status
        FROM crawl_sessions
        ORDER BY started_at DESC
        """
        
        cursor = conn.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Convert timestamps to readable format
        for result in results:
            if result.get('start_time'):
                result['start_time'] = datetime.fromtimestamp(result['start_time']).isoformat()
            if result.get('end_time'):
                result['end_time'] = datetime.fromtimestamp(result['end_time']).isoformat()
        
        conn.close()
        return results
    
    def get_crawl_statistics(self, session_id: Optional[int] = None) -> Dict:
        """Generate comprehensive crawl statistics."""
        conn = self.get_connection()
        
        # Base statistics
        stats = {}
        
        # Session filter (approximate by timestamp if session_id provided)
        session_filter = ""
        params = []
        if session_id:
            try:
                # Get session timing
                session_cursor = conn.execute(
                    "SELECT started_at, completed_at FROM crawl_sessions WHERE id = ?", 
                    (session_id,)
                )
                session_data = session_cursor.fetchone()
                if session_data:
                    start_time, end_time = session_data
                    if start_time and end_time:
                        session_filter = "WHERE timestamp BETWEEN ? AND ?"
                        params = [start_time, end_time]
                    elif start_time:
                        session_filter = "WHERE timestamp >= ?"
                        params = [start_time]
            except Exception:
                pass
        
        # Total pages
        cursor = conn.execute(f"SELECT COUNT(*) FROM pages {session_filter}", params)
        stats['total_pages'] = cursor.fetchone()[0]
        
        # Total links and images (simplified - not stored separately)
        stats['total_links'] = 0
        stats['total_images'] = 0
        
        # Domain distribution
        cursor = conn.execute(f"""
            SELECT 
                CASE 
                    WHEN url LIKE 'http://%' THEN SUBSTR(url, 8, INSTR(SUBSTR(url, 8), '/') - 1)
                    WHEN url LIKE 'https://%' THEN SUBSTR(url, 9, INSTR(SUBSTR(url, 9), '/') - 1)
                    ELSE 'unknown'
                END as domain,
                COUNT(*) as count 
            FROM pages {session_filter}
            GROUP BY domain 
            ORDER BY count DESC
        """, params)
        stats['domain_distribution'] = dict(cursor.fetchall())
        
        # Status code distribution
        cursor = conn.execute(f"""
            SELECT status_code, COUNT(*) as count 
            FROM pages {session_filter}
            GROUP BY status_code 
            ORDER BY count DESC
        """, params)
        stats['status_codes'] = dict(cursor.fetchall())
        
        # Content type distribution
        cursor = conn.execute(f"""
            SELECT content_type, COUNT(*) as count 
            FROM pages {session_filter}
            GROUP BY content_type 
            ORDER BY count DESC
        """, params)
        stats['content_types'] = dict(cursor.fetchall())
        
        # Average response time
        cursor = conn.execute(f"""
            SELECT AVG(response_time) 
            FROM pages 
            {'WHERE' if not session_filter else session_filter + ' AND'} response_time IS NOT NULL
        """, params)
        avg_response = cursor.fetchone()[0]
        stats['avg_response_time'] = round(avg_response, 3) if avg_response else 0
        
        # Total content size
        cursor = conn.execute(f"""
            SELECT SUM(content_length) 
            FROM pages 
            {'WHERE' if not session_filter else session_filter + ' AND'} content_length IS NOT NULL
        """, params)
        total_size = cursor.fetchone()[0]
        stats['total_content_size'] = total_size or 0
        stats['total_content_size_mb'] = round((total_size or 0) / 1024 / 1024, 2)
        
        conn.close()
        return stats
    
    # ========================================
    # CSV EXPORT METHODS
    # ========================================
    
    def export_to_csv(self, output_file: str, data_type: str = "pages", **filters) -> str:
        """
        Export data to CSV format.
        
        Args:
            output_file: Output CSV file path
            data_type: Type of data to export (pages, links, images, sessions)
            **filters: Filtering options
        """
        if data_type == "pages":
            data = self.get_pages_data(**filters)
        elif data_type == "links":
            data = self.get_links_data(**filters)
        elif data_type == "images":
            data = self.get_images_data(**filters)
        elif data_type == "sessions":
            data = self.get_sessions_data()
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        if not data:
            raise ValueError(f"No {data_type} data found with given filters")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        return f"Exported {len(data)} {data_type} records to {output_file}"
    
    # ========================================
    # JSON EXPORT METHODS
    # ========================================
    
    def export_to_json(self, output_file: str, data_type: str = "pages", 
                      include_stats: bool = True, **filters) -> str:
        """
        Export data to JSON format.
        
        Args:
            output_file: Output JSON file path
            data_type: Type of data to export
            include_stats: Whether to include statistics in output
            **filters: Filtering options
        """
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "data_type": data_type,
                "filters": filters
            }
        }
        
        if data_type == "pages":
            export_data["pages"] = self.get_pages_data(**filters)
        elif data_type == "links":
            export_data["links"] = self.get_links_data(**filters)
        elif data_type == "images":
            export_data["images"] = self.get_images_data(**filters)
        elif data_type == "sessions":
            export_data["sessions"] = self.get_sessions_data()
        elif data_type == "all":
            export_data["pages"] = self.get_pages_data(**filters)
            export_data["links"] = self.get_links_data(**filters)
            export_data["images"] = self.get_images_data(**filters)
            export_data["sessions"] = self.get_sessions_data()
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        if include_stats:
            export_data["statistics"] = self.get_crawl_statistics(filters.get('session_id'))
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, default=str)
        
        record_count = len(export_data.get(data_type, export_data.get("pages", [])))
        return f"Exported {record_count} records to {output_file}"
    
    # ========================================
    # XML EXPORT METHODS
    # ========================================
    
    def export_to_xml(self, output_file: str, data_type: str = "pages", **filters) -> str:
        """
        Export data to XML format.
        
        Args:
            output_file: Output XML file path
            data_type: Type of data to export
            **filters: Filtering options
        """
        root = ET.Element("crawler_export")
        
        # Add export info
        export_info = ET.SubElement(root, "export_info")
        ET.SubElement(export_info, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(export_info, "data_type").text = data_type
        
        # Add filters info
        if filters:
            filters_elem = ET.SubElement(export_info, "filters")
            for key, value in filters.items():
                if value is not None:
                    ET.SubElement(filters_elem, key).text = str(value)
        
        # Get and add data
        if data_type == "pages":
            data = self.get_pages_data(**filters)
            data_elem = ET.SubElement(root, "pages")
            for page in data:
                page_elem = ET.SubElement(data_elem, "page")
                for key, value in page.items():
                    if value is not None:
                        ET.SubElement(page_elem, key).text = str(value)
        
        elif data_type == "links":
            data = self.get_links_data(**filters)
            data_elem = ET.SubElement(root, "links")
            for link in data:
                link_elem = ET.SubElement(data_elem, "link")
                for key, value in link.items():
                    if value is not None:
                        ET.SubElement(link_elem, key).text = str(value)
        
        elif data_type == "sessions":
            data = self.get_sessions_data()
            data_elem = ET.SubElement(root, "sessions")
            for session in data:
                session_elem = ET.SubElement(data_elem, "session")
                for key, value in session.items():
                    if value is not None:
                        ET.SubElement(session_elem, key).text = str(value)
        
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        # Write XML file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        return f"Exported {len(data)} {data_type} records to {output_file}"
    
    # ========================================
    # HTML REPORT METHODS
    # ========================================
    
    def generate_html_report(self, output_file: str, session_id: Optional[int] = None,
                           include_charts: bool = True) -> str:
        """
        Generate comprehensive HTML report with statistics and charts.
        
        Args:
            output_file: Output HTML file path
            session_id: Optional session ID to filter by
            include_charts: Whether to include interactive charts
        """
        stats = self.get_crawl_statistics(session_id)
        pages_data = self.get_pages_data(session_id=session_id, limit=100)  # Limit for performance
        sessions_data = self.get_sessions_data()
        
        html_content = self._generate_html_template(stats, pages_data, sessions_data, 
                                                  session_id, include_charts)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)
        
        return f"Generated HTML report: {output_file}"
    
    def _generate_html_template(self, stats: Dict, pages_data: List[Dict], 
                              sessions_data: List[Dict], session_id: Optional[int],
                              include_charts: bool) -> str:
        """Generate HTML template for the report."""
        
        session_info = ""
        if session_id:
            session_data = next((s for s in sessions_data if s['id'] == session_id), None)
            if session_data:
                session_info = f"""
                <div class="session-info">
                    <h3>Session Information</h3>
                    <p><strong>Session ID:</strong> {session_id}</p>
                    <p><strong>Start URL:</strong> {session_data.get('start_url', 'N/A')}</p>
                    <p><strong>Start Time:</strong> {session_data.get('start_time', 'N/A')}</p>
                    <p><strong>End Time:</strong> {session_data.get('end_time', 'In Progress')}</p>
                </div>
                """
        
        # Generate domain chart data
        domain_chart = ""
        if include_charts and stats.get('domain_distribution'):
            domains = list(stats['domain_distribution'].keys())[:10]  # Top 10
            counts = [stats['domain_distribution'][d] for d in domains]
            domain_chart = f"""
            <script>
                const domainData = {{
                    labels: {json.dumps(domains)},
                    datasets: [{{
                        label: 'Pages per Domain',
                        data: {json.dumps(counts)},
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }}]
                }};
                
                const domainCtx = document.getElementById('domainChart').getContext('2d');
                new Chart(domainCtx, {{
                    type: 'bar',
                    data: domainData,
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Pages per Domain'
                            }}
                        }}
                    }}
                }});
            </script>
            """
        
        # Generate recent pages table
        recent_pages_rows = ""
        for page in pages_data[:20]:  # Top 20 recent pages
            recent_pages_rows += f"""
            <tr>
                <td><a href="{html.escape(page.get('url', ''))}" target="_blank">{html.escape(page.get('url', '')[:60])}...</a></td>
                <td>{html.escape(page.get('title', '') or 'No Title')[:40]}...</td>
                <td>{page.get('status_code', 'N/A')}</td>
                <td>{page.get('domain', 'N/A')}</td>
                <td>{page.get('crawl_timestamp', 'N/A')}</td>
            </tr>
            """
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .timestamp {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin-top: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }}
        .session-info {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .charts-section {{
            margin: 40px 0;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .table-section {{
            margin: 40px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .distribution {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }}
        .distribution-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .distribution-item h4 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .dist-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .dist-bar:last-child {{
            border-bottom: none;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #7f8c8d;
        }}
    </style>
    {'<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' if include_charts else ''}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ Web Crawler Report</h1>
            <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        {session_info}
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Pages</h3>
                <div class="value">{stats.get('total_pages', 0):,}</div>
            </div>
            <div class="stat-card">
                <h3>Total Links</h3>
                <div class="value">{stats.get('total_links', 0):,}</div>
            </div>
            <div class="stat-card">
                <h3>Total Images</h3>
                <div class="value">{stats.get('total_images', 0):,}</div>
            </div>
            <div class="stat-card">
                <h3>Content Size</h3>
                <div class="value">{stats.get('total_content_size_mb', 0)}</div>
                <small>MB</small>
            </div>
            <div class="stat-card">
                <h3>Avg Response</h3>
                <div class="value">{stats.get('avg_response_time', 0)}</div>
                <small>seconds</small>
            </div>
            <div class="stat-card">
                <h3>Domains</h3>
                <div class="value">{len(stats.get('domain_distribution', {}))}</div>
            </div>
        </div>
        
        <div class="distribution">
            <div class="distribution-item">
                <h4>Top Domains</h4>
                {"".join([f'<div class="dist-bar"><span>{domain}</span><strong>{count}</strong></div>' 
                         for domain, count in list(stats.get('domain_distribution', {}).items())[:10]])}
            </div>
            <div class="distribution-item">
                <h4>Status Codes</h4>
                {"".join([f'<div class="dist-bar"><span>HTTP {code}</span><strong>{count}</strong></div>' 
                         for code, count in stats.get('status_codes', {}).items()])}
            </div>
        </div>
        
        {f'<div class="charts-section"><div class="chart-container"><canvas id="domainChart" width="400" height="200"></canvas></div></div>' if include_charts else ''}
        
        <div class="table-section">
            <h3>Recent Pages</h3>
            <table>
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Domain</th>
                        <th>Crawled</th>
                    </tr>
                </thead>
                <tbody>
                    {recent_pages_rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Report generated by Advanced Web Crawler Export System</p>
            <p>Database: {html.escape(self.db_path)}</p>
        </div>
    </div>
    
    {domain_chart}
</body>
</html>
        """
        
        return html_template


def main():
    """Command-line interface for data export."""
    parser = argparse.ArgumentParser(description="Export and analyze web crawler data")
    
    parser.add_argument("--db", default="downloaded_pages/crawler_data.db",
                       help="Database file path")
    parser.add_argument("--format", choices=["csv", "json", "xml", "html"], 
                       default="csv", help="Export format")
    parser.add_argument("--data-type", choices=["pages", "links", "images", "sessions", "all"],
                       default="pages", help="Type of data to export")
    parser.add_argument("--output", "-o", required=True,
                       help="Output file path")
    parser.add_argument("--session-id", type=int,
                       help="Filter by session ID")
    parser.add_argument("--domain", 
                       help="Filter by domain (supports wildcards)")
    parser.add_argument("--keyword",
                       help="Filter by keyword in title")
    parser.add_argument("--date-from",
                       help="Filter from date (YYYY-MM-DD)")
    parser.add_argument("--date-to",
                       help="Filter to date (YYYY-MM-DD)")
    parser.add_argument("--include-stats", action="store_true",
                       help="Include statistics in JSON export")
    parser.add_argument("--no-charts", action="store_true",
                       help="Disable charts in HTML report")
    
    args = parser.parse_args()
    
    try:
        exporter = DataExporter(args.db)
        
        # Build filters
        filters = {}
        if args.session_id:
            filters['session_id'] = args.session_id
        if args.domain:
            filters['domain_filter'] = args.domain
        if args.keyword:
            filters['keyword_filter'] = args.keyword
        if args.date_from:
            filters['date_from'] = args.date_from
        if args.date_to:
            filters['date_to'] = args.date_to
        
        # Export data
        if args.format == "csv":
            result = exporter.export_to_csv(args.output, args.data_type, **filters)
        elif args.format == "json":
            result = exporter.export_to_json(args.output, args.data_type, 
                                           args.include_stats, **filters)
        elif args.format == "xml":
            result = exporter.export_to_xml(args.output, args.data_type, **filters)
        elif args.format == "html":
            result = exporter.generate_html_report(args.output, args.session_id, 
                                                  not args.no_charts)
        
        print(f"✅ {result}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())