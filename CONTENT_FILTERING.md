# Content Filtering Guide

The Web Crawler includes comprehensive content filtering capabilities to enable targeted, efficient crawling for specific content types and requirements.

## Overview

Content filtering allows you to:
- **Focus crawling** on relevant content only
- **Exclude unwanted** content types or patterns
- **Control content quality** with size and structure requirements
- **Optimize performance** by avoiding unnecessary processing
- **Target specific domains** or URL patterns

## Filter Types

### 1. Keyword Filters

Target or avoid content containing specific keywords.

```bash
# Include pages containing specific keywords (case-insensitive)
python crawler.py https://example.com --include-keywords "python,programming,tutorial"

# Exclude pages containing unwanted keywords
python crawler.py https://example.com --exclude-keywords "spam,advertisement,popup"

# Combine both (pages must contain include keywords AND not contain exclude keywords)
python crawler.py https://example.com --include-keywords "python" --exclude-keywords "spam"
```

### 2. URL Pattern Filters

Control which URLs to crawl using wildcard patterns.

```bash
# Only crawl specific URL patterns
python crawler.py https://example.com --include-patterns "*/docs/*,*/blog/*,*.html"

# Exclude certain URL patterns
python crawler.py https://example.com --exclude-patterns "*/admin/*,*/private/*,*.pdf"

# Match specific documentation sections
python crawler.py https://docs.python.org --include-patterns "*/library/*,*/tutorial/*"
```

**Pattern Examples:**
- `*.html` - All HTML files
- `*/docs/*` - Any URL containing "/docs/"
- `*/api/v*/` - API documentation URLs
- `*github.com*` - Any GitHub URL
- `*.php` - All PHP files

### 3. File Extension Filters

Target specific file types for crawling.

```bash
# Only crawl HTML and PHP files
python crawler.py https://example.com --include-extensions ".html,.htm,.php"

# Exclude image and document files
python crawler.py https://example.com --exclude-extensions ".jpg,.png,.pdf,.doc"

# Focus on web pages only
python crawler.py https://example.com --include-extensions ".html,.htm,.aspx,.jsp"
```

### 4. Content Length Filters

Control the size range of content to process.

```bash
# Only crawl substantial content (500+ characters)
python crawler.py https://example.com --min-content-length 500

# Avoid very large pages (under 10KB)
python crawler.py https://example.com --max-content-length 10000

# Target medium-sized articles (1KB to 50KB)
python crawler.py https://example.com --min-content-length 1000 --max-content-length 50000
```

### 5. Content Structure Filters

Require specific content structure elements.

```bash
# Only crawl pages that have titles
python crawler.py https://example.com --require-title

# Combine with other filters for quality content
python crawler.py https://example.com --require-title --min-content-length 500 --include-keywords "article,blog,news"
```

### 6. Language Filters

Target content in specific languages.

```bash
# Only crawl English content
python crawler.py https://example.com --language-filter "en"

# Multiple languages
python crawler.py https://example.com --language-filter "en,es,fr"
```

## Practical Examples

### Blog Content Mining
```bash
python crawler.py https://techblog.com \
  --include-keywords "python,ai,machine learning" \
  --include-patterns "*/blog/*,*/articles/*" \
  --min-content-length 1000 \
  --require-title \
  --max-pages 50
```

### Documentation Crawling
```bash
python crawler.py https://docs.framework.org \
  --include-patterns "*/docs/*,*/api/*,*/guide/*" \
  --include-extensions ".html,.htm" \
  --exclude-patterns "*/download/*,*/install/*" \
  --min-content-length 300
```

### News Article Collection
```bash
python crawler.py https://news-site.com \
  --include-keywords "technology,software,programming" \
  --exclude-keywords "advertisement,sponsored,popup" \
  --min-content-length 800 \
  --max-content-length 15000 \
  --require-title
```

### Research Data Collection
```bash
python crawler.py https://research-portal.edu \
  --include-keywords "research,study,analysis,paper" \
  --include-patterns "*/papers/*,*/research/*,*/publications/*" \
  --include-extensions ".html,.htm,.php" \
  --min-content-length 2000 \
  --language-filter "en"
```

## Configuration File

Add default filters to `crawler_config.yaml`:

```yaml
filtering:
  include_keywords: []
  exclude_keywords: ["spam", "advertisement", "popup"]
  include_patterns: []
  exclude_patterns: ["*/admin/*", "*/private/*"]
  include_extensions: [".html", ".htm", ".php", ".aspx"]
  exclude_extensions: [".jpg", ".png", ".gif", ".pdf", ".doc"]
  min_content_length: 100
  max_content_length: null
  require_title: false
  language_filter: []
```

## Filter Logic

### How Filters Are Applied

1. **URL Filtering** (before crawling):
   - Check include/exclude patterns
   - Check include/exclude extensions
   - If URL passes, proceed to crawl

2. **Content Filtering** (after crawling):
   - Check include/exclude keywords
   - Check content length (min/max)
   - Check title requirement
   - Check language filter
   - If content passes, save to database

### Filter Combination Rules

- **Include filters**: Content must match ALL include criteria
- **Exclude filters**: Content must match NO exclude criteria
- **Mixed filters**: Content must pass ALL include AND avoid ALL exclude criteria

## Performance Impact

### Positive Impact
- **Reduced storage**: Only relevant content saved
- **Faster processing**: Skip unwanted pages early
- **Better data quality**: Focused, clean dataset
- **Reduced bandwidth**: Fewer unnecessary downloads

### Considerations
- **Pattern matching overhead**: Complex patterns may slow URL checking
- **Content analysis**: Keyword filtering requires parsing page content
- **False positives/negatives**: Filters may miss relevant content or include irrelevant content

## Statistics and Monitoring

The crawler tracks filtering statistics:

```
[FILTERED] URLs Filtered: 25        # URLs blocked by URL filters
[FILTERED] Content Filtered: 8      # Pages blocked by content filters
[SUCCESS] Success Rate: 85.2%       # Percentage of crawled pages that passed filters
```

## Best Practices

### 1. Start Broad, Then Narrow
```bash
# First run: discover what's available
python crawler.py https://example.com --max-pages 10

# Second run: apply focused filters based on findings
python crawler.py https://example.com --include-keywords "relevant,terms" --max-pages 100
```

### 2. Test Filters First
```bash
# Test with small page limit
python crawler.py https://example.com --include-keywords "test" --max-pages 5

# Scale up after validation
python crawler.py https://example.com --include-keywords "test" --max-pages 1000
```

### 3. Combine Complementary Filters
```bash
# Quality content: good size + structure + relevant keywords
python crawler.py https://example.com \
  --min-content-length 500 \
  --require-title \
  --include-keywords "quality,content"
```

### 4. Use Exclude Lists for Common Noise
```bash
# Filter out common unwanted content
python crawler.py https://example.com \
  --exclude-keywords "cookie,privacy,gdpr,advertisement" \
  --exclude-patterns "*/ads/*,*/tracking/*"
```

### 5. Monitor Filter Effectiveness
- Check `[FILTERED]` statistics in crawler output
- Review success rates to ensure filters aren't too restrictive
- Adjust filters based on results quality

## Troubleshooting

### Too Many Pages Filtered
- **Issue**: Very low success rate, most content filtered out
- **Solution**: Relax filters, check keyword spelling, verify patterns

### Not Enough Filtering
- **Issue**: Still getting irrelevant content
- **Solution**: Add more specific exclude keywords, tighten patterns

### Missing Expected Content
- **Issue**: Expected pages not being crawled
- **Solution**: Check if URL patterns are too restrictive, verify keywords are present in target content

### Performance Issues
- **Issue**: Crawling very slow with filters
- **Solution**: Simplify complex patterns, use fewer regex patterns, increase `--delay`

## Advanced Usage

### Custom Filter Combinations

```bash
# Academic paper collection
python crawler.py https://university.edu \
  --include-patterns "*/papers/*,*/research/*,*/publications/*" \
  --include-keywords "research,study,analysis,methodology" \
  --exclude-keywords "draft,preliminary,confidential" \
  --min-content-length 2000 \
  --require-title \
  --language-filter "en"

# Technical documentation
python crawler.py https://developer-site.com \
  --include-patterns "*/docs/*,*/api/*,*/reference/*" \
  --include-extensions ".html,.htm" \
  --include-keywords "documentation,reference,guide,tutorial" \
  --min-content-length 300 \
  --exclude-patterns "*/download/*,*/sales/*"

# News and blog aggregation
python crawler.py https://tech-news.com \
  --include-patterns "*/blog/*,*/news/*,*/articles/*" \
  --include-keywords "technology,software,programming,development" \
  --exclude-keywords "advertisement,sponsored,promoted,popup" \
  --min-content-length 800 \
  --max-content-length 20000 \
  --require-title
```

Content filtering transforms the crawler from a general-purpose tool into a targeted, efficient data collection system perfect for research, analysis, and focused content gathering.