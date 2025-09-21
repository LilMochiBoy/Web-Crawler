# 🕸️ Web Crawler - Getting Started

## 📦 What You Received
- `crawler.py` - Main web crawler program
- `example_usage.py` - Example of how to use the crawler in code
- `test_crawler.py` - Automated test script
- `requirements.txt` - List of required packages
- `README.md` - Complete documentation
- `SETUP.md` - Quick setup guide

## 🚀 Quick Start (2 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```
*Or manually: `pip install requests beautifulsoup4 lxml`*

### Step 2: Run the Test
```bash
python test_crawler.py
```
This will automatically test everything and show you if it's working.

### Step 3: Try Your First Crawl
```bash
python crawler.py https://httpbin.org --max-pages 5
```

### Step 4: Check Results
Look in the `downloaded_pages/` folder - you should see HTML files organized by domain!

## 🧪 What the Test Script Does

The `test_crawler.py` script automatically:
- ✅ Checks if dependencies are installed
- ✅ Tests the command-line interface
- ✅ Runs a small crawl to verify everything works
- ✅ Tests the example usage script
- 📊 Shows a summary of results

## 📋 Test Output Example
```
🚀 Web Crawler Test Suite
========================================
🔍 Testing dependencies...
✅ requests is installed
✅ beautifulsoup4 is installed
✅ lxml is installed

🔍 Testing crawler help...
✅ Crawler help works correctly

🔍 Testing basic crawl...
Running: python crawler.py https://httpbin.org --max-pages 2 --max-depth 1 --delay 0.5 --output-dir test_output
✅ Basic crawl successful!
   Created files in: test_output
   📁 httpbin.org/
      📄 index.html
      📄 index.meta
   📄 crawler.log

🔍 Testing example usage script...
✅ Example usage script works!

========================================
📊 Test Results: 4/4 tests passed
🎉 All tests passed! The web crawler is working correctly.
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
**Solution:** Install dependencies with `pip install -r requirements.txt`

### "Permission denied" or file errors  
**Solution:** Make sure you have write permissions in the folder

### No files downloaded
**Solution:** Check your internet connection and try a different website

### "Robots.txt disallows"
**Solution:** The website blocks crawlers - try a different site like httpbin.org

## 🎯 Quick Examples

```bash
# Basic crawl (good for testing)
python crawler.py https://httpbin.org

# Slow, polite crawling
python crawler.py https://example.com --delay 3 --max-pages 10

# Restrict to specific domains
python crawler.py https://example.com --allowed-domains example.com

# Custom output folder
python crawler.py https://example.com --output-dir my_downloads
```

## 📖 Full Documentation
See `README.md` for complete documentation including:
- All command-line options
- Programmatic usage examples  
- Best practices and ethics
- Advanced configuration

---

**Ready to crawl the web responsibly! 🌐**