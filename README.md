# Advanced Web Crawler

A professional-grade Python web crawler with advanced features for targeted data collection, concurrent processing, content filtering, and database storage.

## Key Features

### Core Crawling
- **Polite Crawling**: Respects `robots.txt` files and includes delays between requests
- **Concurrent Processing**: Multi-threaded crawling with configurable worker threads
- **Smart Rate Limiting**: Per-domain rate limiting with intelligent queue management
- **Resume Capability**: Resume interrupted crawls from where they left off
- **Depth Control**: Configurable maximum crawling depth with breadth-first traversal

### Data Management
- **SQLite Database**: Structured storage of pages, links, images, and metadata
- **Content Extraction**: Automatic extraction of titles, headings, text, and structured data
- **JSON Output**: Clean, structured data export for analysis
- **File Organization**: Domain-based directory structure with organized storage

### Advanced Filtering
- **Keyword Filtering**: Include/exclude content based on keywords
- **URL Pattern Filtering**: Wildcard-based URL inclusion/exclusion
- **File Extension Control**: Target specific file types
- **Content Length Limits**: Filter by content size for quality control
- **Language Detection**: Target content in specific languages

### Professional Features
- **Configuration Management**: YAML-based configuration with CLI overrides
- **Comprehensive Statistics**: Detailed performance and success metrics
- **Error Recovery**: Robust error handling with detailed logging
- **Progress Tracking**: Real-time progress bars with performance metrics
- **Session Management**: Track crawl sessions with detailed metadata

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
```bash
pip install -r requirements.txt
```

**Required packages:**
- `requests` - HTTP library for web requests
- `beautifulsoup4` - HTML parsing and content extraction
- `lxml` - Fast XML/HTML parser
- `PyYAML` - Configuration file support
- `tqdm` - Progress bars and performance monitoring

## Quick Start

### Basic Crawling
```bash
python crawler.py https://example.com
```

### Professional Data Collection
```bash
python crawler.py https://docs.python.org \
    --max-pages 100 \
    --workers 4 \
    --include-patterns "*/library/*,*/tutorial/*" \
    --include-keywords "python,programming,tutorial" \
    --min-content-length 500 \
    --max-depth 3
```

### Resume Previous Crawl
```bash
python crawler.py --resume
```

## Command Line Interface

### Essential Options
- `url`: Starting URL to crawl (required, unless using `--resume`)
- `--max-pages`: Maximum pages to download (default: 50)
- `--workers`: Concurrent worker threads (default: 3)
- `--max-depth`: Maximum crawling depth (default: 2)
- `--delay`: Delay between requests in seconds (default: 1.0)

### Content Filtering
- `--include-keywords`: Only crawl pages containing these keywords
- `--exclude-keywords`: Skip pages containing these keywords
- `--include-patterns`: Only crawl URLs matching these patterns
- `--exclude-patterns`: Skip URLs matching these patterns
- `--include-extensions`: Only crawl these file extensions
- `--exclude-extensions`: Skip these file extensions
- `--min-content-length`: Minimum page content length
- `--max-content-length`: Maximum page content length
- `--require-title`: Only crawl pages with titles
- `--language-filter`: Only crawl content in these languages

### Advanced Options
- `--output-dir`: Output directory (default: "downloaded_pages")
- `--allowed-domains`: Restrict to specific domains
- `--user-agent`: Custom User-Agent string
- `--config`: Configuration file path (default: "crawler_config.yaml")
- `--resume`: Resume from previous crawl session
- `--session-id`: Resume specific session ID

## Advanced Usage Examples

### Academic Research Collection
```bash
python crawler.py https://university.edu \
    --include-patterns "*/research/*,*/papers/*,*/publications/*" \
    --include-keywords "research,study,analysis,methodology" \
    --min-content-length 2000 \
    --require-title \
    --max-pages 500 \
    --workers 2
```

### Technical Documentation Mining
```bash
python crawler.py https://docs.framework.org \
    --include-patterns "*/docs/*,*/api/*,*/reference/*" \
    --include-extensions ".html,.htm" \
    --exclude-patterns "*/download/*,*/install/*" \
    --min-content-length 300 \
    --workers 4
```

### News and Blog Content
```bash
python crawler.py https://tech-blog.com \
    --include-keywords "technology,software,programming" \
    --exclude-keywords "advertisement,sponsored,popup" \
    --min-content-length 800 \
    --max-content-length 15000 \
    --require-title \
    --workers 3
```

### Large-Scale Concurrent Crawling
```bash
python crawler.py https://large-site.com \
    --max-pages 10000 \
    --workers 8 \
    --max-depth 4 \
    --delay 0.5 \
    --include-extensions ".html,.htm,.php"
```

## Configuration Management

### YAML Configuration

Create `crawler_config.yaml` for default settings:

```yaml
crawling:
  max_depth: 2
  max_pages: 50
  delay: 1.0
  workers: 3
  user_agent: "AdvancedWebCrawler/2.0"

output:
  directory: "downloaded_pages"
  save_html: true
  save_json: true
  save_metadata: true

filtering:
  include_keywords: []
  exclude_keywords: ["spam", "advertisement"]
  include_patterns: []
  exclude_patterns: ["*/admin/*", "*/private/*"]
  min_content_length: 100
  max_content_length: null
  require_title: false

database:
  enabled: true
  path: "downloaded_pages/crawler_data.db"
```

### CLI Override

Command line options override configuration file settings:
```bash
python crawler.py https://example.com --max-pages 200 --workers 6
```

## Professional Features

### Concurrent Crawling
- **Multi-threaded processing** with configurable worker threads
- **Per-domain rate limiting** to respect server resources  
- **Thread-safe queue management** for efficient URL handling
- **Dynamic load balancing** across domains

### Resume Capability
```bash
# Resume most recent crawl
python crawler.py --resume

# Resume specific session
python crawler.py --resume --session-id 5

# List available sessions
python database_explorer.py
```

### Content Filtering
See [CONTENT_FILTERING.md](CONTENT_FILTERING.md) for comprehensive filtering guide.

### Performance Monitoring
Real-time statistics during crawling:
- Pages per minute processing rate
- Success/failure rates  
- Queue depth and domain distribution
- Memory usage and response times

## Database Analysis

Use the database explorer for analysis:

```bash
# Interactive database exploration
python database_explorer.py

# Quick statistics
python check_db.py

# Analyze specific content
python analyze_content.py
```

## Programmatic Usage

```python
from crawler import WebCrawler, ContentFilter

# Create content filter
content_filter = ContentFilter(
    include_keywords=['python', 'tutorial'],
    min_content_length=500,
    require_title=True
)

# Create crawler with advanced options
crawler = WebCrawler(
    max_depth=3,
    delay=1.0,
    max_pages=100,
    workers=4,
    content_filter=content_filter,
    output_dir="research_data"
)

# Start crawling
stats = crawler.crawl("https://docs.python.org")
print(f"Downloaded: {stats['downloaded']} pages")
print(f"Filtered: {stats['filtered']} pages")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

## Output Structure

The crawler creates a comprehensive data structure:

```
downloaded_pages/
├── crawler_data.db           # SQLite database with structured data
├── crawler.log              # Detailed crawling activity log
├── example.com/             # Domain-based file organization
│   ├── index.html          # Downloaded HTML content
│   ├── index.json          # Extracted structured data
│   ├── index.meta          # Page metadata
│   ├── about.html
│   ├── about.json
│   └── about.meta
└── docs.example.com/
    ├── guide.html
    ├── guide.json
    └── guide.meta
```

### Database Schema

The SQLite database contains comprehensive crawl data:

**Tables:**
- `crawl_sessions` - Session metadata and configuration
- `pages` - Downloaded page content and metadata
- `links` - All discovered links and their relationships
- `images` - Image metadata and references
- `social_links` - Social media links found
- `crawl_errors` - Detailed error logging

### Data Formats

**JSON Files** contain extracted structured data:
```json
{
    "url": "https://example.com",
    "title": "Example Page",
    "headings": {"h1": ["Main Title"], "h2": ["Subtitle"]},
    "text_content": "Clean text content...",
    "links": [{"url": "...", "text": "..."}],
    "images": [{"src": "...", "alt": "..."}],
    "social_links": {"twitter": "...", "github": "..."},
    "metadata": {"description": "...", "keywords": "..."}
}
```

**Meta Files** contain crawl metadata:
- Original URL and final URL (after redirects)
- HTTP status code and headers
- Content type and length
- Download timestamp and processing time
- Content hash for duplicate detection

## Documentation

- **[Getting Started](GETTING_STARTED.md)** - Quick start guide and basic usage
- **[Content Filtering](CONTENT_FILTERING.md)** - Comprehensive filtering guide  
- **[Resume Feature](RESUME_FEATURE.md)** - Resume capability documentation
- **[Database Integration](DATABASE_INTEGRATION.md)** - Database schema and analysis
- **[Concurrent Crawling](CONCURRENT_CRAWLING.md)** - Multi-threading and performance
- **[Setup Guide](SETUP.md)** - Installation and configuration
- **[User Guide](USER_GUIDE.md)** - Complete feature reference

## Performance Benchmarks

Typical performance on standard hardware:

| Configuration | Pages/Minute | Concurrent Requests | Memory Usage |
|--------------|-------------|-------------------|-------------|
| Single thread | 15-25 | 1 | 50-100 MB |
| 3 workers | 45-75 | 3 | 100-200 MB |
| 8 workers | 100-150 | 8 | 200-400 MB |

**Factors affecting performance:**
- Network latency and server response times
- Content size and complexity
- Filtering complexity (patterns, keywords)
- Storage I/O (database writes, file saves)
- Rate limiting delays

## Best Practices

### Crawling Ethics
1. **Respect robots.txt** - Always honored automatically
2. **Use reasonable delays** - Minimum 0.5s, preferably 1s+
3. **Limit concurrent workers** - Max 2-4 per domain
4. **Monitor server load** - Watch for 429/503 responses
5. **Contact website owners** - For large crawls or commercial use

### Performance Optimization
1. **Start small** - Test with low limits first
2. **Use filtering** - Reduce unnecessary processing
3. **Monitor memory** - Large crawls can consume significant RAM
4. **Database maintenance** - Regular VACUUM for large datasets
5. **Resume capability** - Use for long-running crawls

### Data Quality
1. **Content filtering** - Use keyword and length filters
2. **Duplicate detection** - Built-in hash-based detection
3. **Error monitoring** - Check logs for systematic issues
4. **Result validation** - Spot-check downloaded content
5. **Structured extraction** - Leverage JSON output for analysis

## Troubleshooting

### Common Issues

**Slow Crawling**
- Increase `--workers` (test optimal number)
- Reduce `--delay` if server allows
- Use content filtering to skip unwanted pages
- Check network connectivity and DNS resolution

**High Memory Usage**  
- Reduce `--workers` count
- Enable content filtering to reduce data volume
- Process crawls in smaller batches
- Consider using `--max-pages` limits

**Database Errors**
- Check disk space availability
- Ensure write permissions on output directory  
- Use `fix_database.py` for corruption issues
- Consider splitting large crawls across sessions

**Content Not Found**
- Verify URL patterns and keyword filters
- Check robots.txt restrictions
- Ensure JavaScript-free content (static HTML only)
- Test with minimal filtering first

### Debugging

**Enable Verbose Logging:**
```bash
python crawler.py https://example.com --max-pages 5 --workers 1
```

**Check Database:**
```bash
python database_explorer.py
```

**Analyze Recent Session:**
```bash  
python analyze_content.py --session-id latest
```

## Examples by Use Case

### Research and Academia
```bash
# Academic paper collection
python crawler.py https://arxiv.org \
    --include-patterns "*/abs/*" \
    --include-keywords "machine learning,neural network,AI" \
    --min-content-length 1000 \
    --max-pages 1000 \
    --workers 2
```

### SEO and Marketing
```bash  
# Competitor content analysis
python crawler.py https://competitor.com \
    --include-patterns "*/blog/*,*/products/*" \
    --exclude-keywords "privacy,cookie,terms" \
    --require-title \
    --workers 3
```

### Data Journalism  
```bash
# Government data collection
python crawler.py https://data.gov \
    --include-patterns "*/dataset/*,*/catalog/*" \
    --include-keywords "public,data,statistics" \
    --min-content-length 500 \
    --max-pages 2000
```

### Technical Documentation
```bash
# API documentation crawling
python crawler.py https://api-docs.com \
    --include-patterns "*/reference/*,*/guide/*" \
    --include-extensions ".html,.htm" \
    --exclude-patterns "*/examples/*" \
    --workers 4
```

## License

This project is open source and available under the MIT License.