# Web Crawler - Database Storage Integration Complete

## 🎉 What's New

Your web crawler now includes **professional-grade database storage** with SQLite! This enhancement stores all crawled data in a structured database for advanced analysis and querying.

## 📊 Database Features

### Automated Data Storage
- **Session Tracking**: Every crawl run is tracked with unique session IDs
- **Page Storage**: All webpage data, metadata, and extracted content stored
- **Error Logging**: All errors during crawling are logged with details
- **Statistics**: Comprehensive crawl statistics stored and retrievable

### Database Schema
```sql
-- Sessions table tracks each crawl run
crawl_sessions (id, start_url, max_pages, max_depth, pages_crawled, total_errors, started_at, completed_at, status)

-- Pages table stores all downloaded webpages
pages (id, url, title, status_code, content_type, content_length, response_time, timestamp, extracted_data)

-- Errors table logs all crawling errors
errors (id, session_id, url, error_type, error_message, timestamp)
```

## 🚀 Usage Examples

### 1. Basic Crawl with Database (Default)
```powershell
python crawler.py https://example.com --max-pages 10 --max-depth 2
```
- Database storage is **enabled by default**
- Creates session, stores all pages and metadata
- Shows database statistics at the end

### 2. Crawl without Database
```powershell
python crawler.py https://example.com --no-database --max-pages 5
```
- Use `--no-database` flag to disable database storage
- Only saves files to disk (original behavior)

### 3. Explore Database
```powershell
# List all crawling sessions
python database_explorer.py --sessions

# Show detailed session information
python database_explorer.py --session 3

# Export session data to JSON
python database_explorer.py --session 3 --export session_3_data.json

# Query recent pages
python database_explorer.py --pages --limit 20

# Query pages from specific domain
python database_explorer.py --pages --domain github.com --limit 10
```

## 📈 Database Statistics Display

After each crawl, you'll see database statistics:

```
[DATABASE] DATABASE STATISTICS
[SESSION] Session ID: 3
[STORED] Pages in Database: 1
[LINKS] Links Stored: 0
[IMAGES] Images Stored: 0
[SOCIAL] Social Links: 0
[DB ERRORS] Logged Errors: 0
```

## 🔍 Database Explorer Tool

The new `database_explorer.py` tool provides powerful database querying:

```powershell
# Basic commands
python database_explorer.py --sessions              # List all sessions
python database_explorer.py --session 3             # Session details
python database_explorer.py --pages                 # Recent pages
python database_explorer.py --pages --domain example.com  # Domain-specific pages

# Export data
python database_explorer.py --session 3 --export my_crawl_data.json
```

### Session Explorer Output
```
[SESSIONS] CRAWLING SESSIONS
================================================================================
Session ID: 3
Start URL: https://example.com
Start Time: 2025-09-21 21:28:42
End Time: 2025-09-21 21:28:45
Settings: depth=1, max_pages=1
Results: pages=1, errors=0
```

## 📁 File Structure

```
Web-Crawler/
├── crawler.py              # Main crawler with database integration
├── database_explorer.py    # Database analysis tool
├── analyze_content.py      # Content analysis tool
├── downloaded_pages/
│   ├── crawler_data.db     # SQLite database (auto-created)
│   ├── crawler.log         # Crawling logs
│   └── [domain]/           # Downloaded files
└── requirements.txt        # Dependencies
```

## 💡 Use Cases

### 1. Content Analysis
- Query all pages with specific keywords
- Analyze crawling patterns across sessions
- Track error trends and success rates

### 2. Research Projects
- Store multiple crawl sessions for comparison
- Export data for external analysis tools
- Maintain historical crawl records

### 3. Website Monitoring
- Track changes across multiple crawl sessions
- Monitor website availability and response times
- Detect content changes over time

## 🛠 Technical Details

### Database Location
- **File**: `downloaded_pages/crawler_data.db`
- **Type**: SQLite (no server required)
- **Size**: Grows with crawled data

### Data Retention
- All crawl sessions are permanently stored
- No automatic cleanup (you control retention)
- Export functionality for data archival

### Performance
- Minimal impact on crawling speed
- Efficient SQLite storage and indexing
- Background database operations

## 🎯 Next Steps

1. **Run a crawl** to see database integration in action
2. **Explore your data** using the database explorer tool  
3. **Export results** for analysis in other tools
4. **Scale up** with larger crawling projects

The crawler now provides enterprise-level data storage while maintaining the same simple interface you're familiar with!

## 🔧 Commands Summary

```powershell
# Crawl with database (default)
python crawler.py https://example.com

# Crawl without database  
python crawler.py https://example.com --no-database

# Explore sessions
python database_explorer.py --sessions

# Session details
python database_explorer.py --session [ID]

# Export data
python database_explorer.py --session [ID] --export data.json

# Query pages
python database_explorer.py --pages [--domain domain.com] [--limit N]
```

Your crawler is now ready for professional data collection and analysis! 🎉