# 🕸️ Complete Web Crawler User Guide

## 🌟 **What Your Crawler Can Do**

Your web crawler is now a **professional-grade tool** with these features:
- ✅ **Smart crawling** with depth control and domain filtering
- ✅ **Polite behavior** respects robots.txt and delays
- ✅ **Configuration files** for easy settings management
- ✅ **Real-time progress** with visual progress bars
- ✅ **Comprehensive statistics** and performance metrics
- ✅ **Intelligent filtering** skips unwanted file types
- ✅ **Detailed logging** with categorized error messages
- ✅ **Organized storage** saves files by domain

---

## 🚀 **3 Ways to Use Your Crawler**

### **Method 1: Configuration File (Easiest)**
```bash
# 1. Edit crawler_config.yaml with your settings
# 2. Simply run:
python crawler.py https://example.com
```

### **Method 2: Command Line (Quick)**
```bash
python crawler.py https://example.com --max-pages 20 --delay 2.0
```

### **Method 3: Mixed Approach (Flexible)**
```bash
# Uses config file but overrides specific settings
python crawler.py https://example.com --max-pages 50
```

---

## ⚙️ **Configuration File Explained**

Your `crawler_config.yaml` file contains all settings:

```yaml
crawler:
  max_depth: 2                    # How many clicks deep to go
  delay: 1.0                     # Seconds between requests
  max_pages: 50                  # Maximum pages to download
  user_agent: "WebCrawler-Bot/1.0"

output:
  directory: "downloaded_pages"   # Where to save files

filters:
  allowed_domains: []            # Restrict to specific domains
  skip_patterns:                 # Skip URLs containing these
    - "/admin"
    - "/login"
```

### **Key Settings Explained:**

**`max_depth`**: 
- `0` = Only the starting page
- `1` = Start page + all linked pages
- `2` = Start page + links + links from those pages
- `3+` = Goes deeper (be careful!)

**`delay`**:
- `1.0` = 1 second between requests (polite)
- `2.0` = 2 seconds (very polite)
- `0.5` = 0.5 seconds (faster but less polite)

**`max_pages`**:
- `10` = Small test crawl
- `50` = Medium crawl
- `200+` = Large crawl

---

## 📋 **All Command Line Options**

```bash
python crawler.py <URL> [OPTIONS]

Required:
  URL                    Starting website to crawl

Optional:
  --config FILE          Configuration file (default: crawler_config.yaml)
  --max-depth N          How deep to crawl (overrides config)
  --delay SECONDS        Delay between requests (overrides config)
  --max-pages N          Maximum pages to download (overrides config)
  --output-dir DIR       Where to save files (overrides config)
  --allowed-domains D1 D2  Only crawl these domains (overrides config)
  --user-agent STRING    User agent string (overrides config)
```

---

## 🎯 **Common Use Cases & Examples**

### **1. Quick Website Backup**
```bash
python crawler.py https://example.com --max-pages 100 --max-depth 2
```

### **2. Test Small Website**
```bash
python crawler.py https://httpbin.org --max-pages 5 --delay 0.5
```

### **3. Deep Documentation Crawl**
```bash
python crawler.py https://docs.example.com --max-depth 3 --max-pages 200
```

### **4. Stay Within One Domain**
```bash
python crawler.py https://example.com --allowed-domains example.com
```

### **5. Slow, Respectful Crawl**
```bash
python crawler.py https://example.com --delay 5.0 --max-pages 20
```

### **6. Custom Output Location**
```bash
python crawler.py https://example.com --output-dir "my-website-backup"
```

---

## 📊 **Understanding the Output**

### **What You'll See While Crawling:**

```
📝 Loaded configuration from crawler_config.yaml
🚀 Web Crawler Starting...
📋 Settings: depth=2, pages=50, delay=1.0s
2025-09-21 19:23:20,303 - INFO - Starting crawl from: https://example.com
📥 Downloading:  33%|██████      | 17/50 [00:45<01:30, 2.7s/pages, Domain=example.com, Queue=23, Speed=2.1s]
```

**Progress Bar Shows:**
- **33%**: Percentage complete
- **17/50**: Pages downloaded so far
- **Domain**: Current domain being crawled
- **Queue**: How many URLs are waiting
- **Speed**: Average time per page

### **Final Statistics Report:**

```
📊 CRAWLING STATISTICS
==================================================
⏱️  Duration: 145.2 seconds (2.4 minutes)
🔍 URLs Found: 234
✅ Pages Downloaded: 50
⏭️  Pages Skipped: 12
🌐 Domains Crawled: 3
💾 Data Downloaded: 15.67 MB
⚡ Average Response Time: 2.31s
📈 Pages/minute: 20.7
❌ Total Errors: 5
   └── timeout: 2
   └── http_errors: 3
📊 Success Rate: 89.3%
```

---

## 📁 **File Organization**

Your crawler organizes downloaded files like this:

```
downloaded_pages/           # Main folder
├── crawler.log            # Detailed activity log
├── example.com/           # Domain-based folders
│   ├── index.html        # Main page
│   ├── index.meta        # Page metadata
│   ├── about.html        # About page
│   ├── about.meta        # About page metadata
│   └── products.html     # Products page
├── subdomain.example.com/
│   ├── api.html
│   └── api.meta
└── cdn.example.com/
    ├── docs.html
    └── docs.meta
```

### **File Types Created:**

**`.html` files**: The actual webpage content
**`.meta` files**: Information about each page:
```
URL: https://example.com/about
Status Code: 200
Content-Type: text/html; charset=utf-8
Content-Length: 15423
Downloaded: 2025-09-21 19:23:45
```

**`crawler.log`**: Complete activity log with timestamps

---

## 🔧 **Advanced Usage Tips**

### **1. Testing New Websites**
Always start small when testing a new website:
```bash
python crawler.py https://new-site.com --max-pages 3 --max-depth 1
```

### **2. Large Crawls**
For big websites, use generous delays:
```bash
python crawler.py https://large-site.com --delay 3.0 --max-pages 500
```

### **3. Domain Restrictions**
Stay within specific domains to avoid wandering:
```yaml
filters:
  allowed_domains: 
    - "example.com"
    - "docs.example.com"
    - "blog.example.com"
```

### **4. Skip Unwanted Content**
Avoid admin areas and search pages:
```yaml
filters:
  skip_patterns:
    - "/admin"
    - "/login"
    - "?search="
    - "/api/"
```

---

## 🚨 **Error Messages & Solutions**

### **Common Errors:**

**❌ "Timeout error (>30s)"**
→ Website is slow. Try: `--delay 2.0`

**❌ "Rate limited (429)"** 
→ Too fast. Try: `--delay 5.0`

**❌ "Connection error"**
→ Check internet or try different website

**⚠️ "Robots.txt disallows"**
→ Website blocks crawlers for that page (normal)

**❌ "Access forbidden (403)"**
→ Page requires login or is restricted

---

## 📈 **Performance Tips**

### **Speed vs Politeness:**
- **Fast**: `--delay 0.5` (use only for testing)
- **Normal**: `--delay 1.0` (default, good balance)  
- **Polite**: `--delay 3.0` (respectful, recommended)
- **Very polite**: `--delay 5.0` (for sensitive sites)

### **Memory Usage:**
- **Small crawls**: `--max-pages 50` uses minimal memory
- **Large crawls**: `--max-pages 500+` may use more memory

---

## ✅ **Best Practices**

### **1. Always Be Respectful**
- Use delays of 1+ seconds
- Check robots.txt compliance (automatic)
- Don't overload servers

### **2. Start Small**
- Test with `--max-pages 5` first
- Gradually increase for larger crawls
- Monitor the output directory size

### **3. Use Configuration Files**
- Create different configs for different projects
- `crawler_config_news.yaml`, `crawler_config_docs.yaml`

### **4. Monitor Progress**
- Watch the progress bar and statistics
- Check `crawler.log` for detailed information
- Stop if you see many errors (Ctrl+C)

---

## 🎯 **Quick Start Checklist**

1. **✅ Edit `crawler_config.yaml`** with your preferred settings
2. **✅ Choose your starting URL**
3. **✅ Run:** `python crawler.py https://your-target-site.com`
4. **✅ Watch the progress bar** and statistics
5. **✅ Check results** in the output directory
6. **✅ Review `crawler.log`** for detailed information

Your web crawler is now a powerful, professional tool that can handle websites of all sizes while being respectful and providing detailed feedback! 🚀