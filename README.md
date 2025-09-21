# Web Crawler

A comprehensive Python web crawler that downloads webpages with proper etiquette, rate limiting, and organization.

## Features

- **Polite Crawling**: Respects `robots.txt` files and includes delays between requests
- **URL Validation**: Filters out non-HTML content and validates URLs
- **Domain Filtering**: Optional restriction to specific domains
- **Depth Control**: Configurable maximum crawling depth
- **File Organization**: Saves pages in organized directory structure by domain
- **Metadata Tracking**: Saves metadata for each downloaded page
- **Comprehensive Logging**: Detailed logs of crawling activity
- **Command Line Interface**: Easy-to-use CLI with configurable options
- **Programmatic API**: Can be used as a Python module

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
```bash
pip install requests beautifulsoup4 lxml
```

## Command Line Usage

### Basic Usage
```bash
python crawler.py https://example.com
```

### Advanced Usage
```bash
python crawler.py https://example.com \
    --max-depth 3 \
    --delay 2.0 \
    --max-pages 100 \
    --output-dir my_downloads \
    --allowed-domains example.com subdomain.example.com \
    --user-agent "MyBot/1.0"
```

### Command Line Options

- `url`: Starting URL to crawl (required)
- `--max-depth`: Maximum crawling depth (default: 2)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--max-pages`: Maximum number of pages to download (default: 50)
- `--output-dir`: Output directory (default: "downloaded_pages")
- `--allowed-domains`: List of allowed domains (default: all domains)
- `--user-agent`: User agent string (default: "WebCrawler-Bot/1.0")

## Programmatic Usage

```python
from crawler import WebCrawler

# Create crawler instance
crawler = WebCrawler(
    max_depth=2,
    delay=1.0,
    max_pages=50,
    output_dir="downloads",
    allowed_domains=["example.com"],
    user_agent="MyBot/1.0"
)

# Start crawling
crawler.crawl("https://example.com")
print(f"Downloaded {crawler.downloaded_pages} pages")
```

## Output Structure

The crawler organizes downloaded content as follows:

```
output_directory/
├── crawler.log                 # Crawling activity log
├── example.com/               # Domain-based directories
│   ├── index.html            # Downloaded HTML page
│   ├── index.meta            # Page metadata
│   ├── about.html
│   └── about.meta
└── subdomain.example.com/
    ├── page.html
    └── page.meta
```

### Metadata Files

Each downloaded page has an associated `.meta` file containing:
- Original URL
- HTTP status code
- Content type
- Content length
- Download timestamp

## Features in Detail

### URL Validation
- Validates URL schemes (http/https only)
- Filters out binary files (images, documents, etc.)
- Normalizes URLs (removes fragments, lowercase domains)
- Prevents duplicate downloads

### Politeness Features
- Respects `robots.txt` files
- Configurable delays between requests
- Proper HTTP headers and User-Agent
- Connection keep-alive for efficiency

### Error Handling
- Graceful handling of network errors
- Skips inaccessible pages
- Logs all errors and activities
- Continues crawling on individual page failures

## Examples

### Download a small website completely
```bash
python crawler.py https://httpbin.org --max-depth 2 --max-pages 20
```

### Crawl only specific domains
```bash
python crawler.py https://example.com --allowed-domains example.com www.example.com
```

### Slow, polite crawling
```bash
python crawler.py https://example.com --delay 5.0 --max-pages 10
```

### Custom output directory
```bash
python crawler.py https://example.com --output-dir my_website_backup
```

## Best Practices

1. **Be Respectful**: Always use reasonable delays (1+ seconds) between requests
2. **Limit Scope**: Use `--allowed-domains` to stay within intended boundaries
3. **Start Small**: Begin with low `--max-pages` and `--max-depth` values
4. **Check Logs**: Review `crawler.log` to understand crawler behavior
5. **Monitor Progress**: Watch the progress output to ensure expected behavior

## Legal and Ethical Considerations

- Always check and respect website terms of service
- Respect `robots.txt` files (the crawler does this automatically)
- Use reasonable delays to avoid overloading servers
- Consider contacting website owners for permission on large crawls
- Be aware of copyright and data protection laws

## Troubleshooting

### Common Issues

1. **"Robots.txt disallows" messages**: The website's robots.txt forbids crawling
2. **Network timeout errors**: Try increasing the delay or checking internet connection
3. **Permission errors**: Ensure the output directory is writable
4. **No pages downloaded**: Check if the start URL is accessible and contains links

### Debugging

Enable verbose logging by checking the `crawler.log` file in the output directory.

## License

This project is open source and available under the MIT License.