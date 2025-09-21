# Quick Setup Guide for Web Crawler

## Prerequisites
- Python 3.7 or higher installed
- Internet connection

## Setup Instructions

### 1. Download/Extract the Project
Extract all files to a folder on your computer.

### 2. Install Dependencies
Open your terminal/command prompt in the project folder and run:

**Windows:**
```cmd
pip install requests beautifulsoup4 lxml
```

**Mac/Linux:**
```bash
pip install requests beautifulsoup4 lxml
```

### 3. Quick Test
Run this command to test if everything works:

**Windows:**
```cmd
python crawler.py https://httpbin.org --max-pages 3 --max-depth 1
```

**Mac/Linux:**
```bash
python3 crawler.py https://httpbin.org --max-pages 3 --max-depth 1
```

### 4. Check Results
After running, you should see:
- A `downloaded_pages/` folder with HTML files
- Console output showing download progress
- A `crawler.log` file with detailed logs

## Alternative: Run the Test Script
```cmd
python test_crawler.py
```

This will automatically test the crawler with safe settings.

## Need Help?
- Check the `README.md` for detailed documentation
- Look at `example_usage.py` for code examples
- Check `crawler.log` for troubleshooting