#!/usr/bin/env python3
"""
Test script for the Web Crawler
This script runs automated tests to verify the crawler works correctly.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_dependencies():
    """Test if required dependencies are installed."""
    print("🔍 Testing dependencies...")
    
    # Map package names to their import names
    dependencies = {
        'requests': 'requests',
        'beautifulsoup4': 'bs4', 
        'lxml': 'lxml'
    }
    
    for package_name, import_name in dependencies.items():
        success, _, _ = run_command(f'python -c "import {import_name}"')
        if success:
            print(f"✅ {package_name} is installed")
        else:
            print(f"❌ {package_name} is NOT installed")
            print(f"   Run: pip install {package_name}")
            return False
    return True

def test_crawler_help():
    """Test if the crawler shows help correctly."""
    print("\n🔍 Testing crawler help...")
    
    success, stdout, stderr = run_command("python crawler.py --help")
    if success and "Web Crawler to download webpages" in stdout:
        print("✅ Crawler help works correctly")
        return True
    else:
        print("❌ Crawler help failed")
        print(f"Error: {stderr}")
        return False

def test_basic_crawl():
    """Test basic crawling functionality."""
    print("\n🔍 Testing basic crawl...")
    
    # Clean up any existing test directory
    test_dir = Path("test_output")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Run a small crawl test
    command = "python crawler.py https://httpbin.org --max-pages 2 --max-depth 1 --delay 0.5 --output-dir test_output"
    print(f"Running: {command}")
    
    success, stdout, stderr = run_command(command)
    
    if success:
        # Check if files were created
        if test_dir.exists() and any(test_dir.iterdir()):
            print("✅ Basic crawl successful!")
            print(f"   Created files in: {test_dir}")
            
            # List what was downloaded
            for item in test_dir.iterdir():
                if item.is_dir():
                    print(f"   📁 {item.name}/")
                    for subitem in item.iterdir():
                        print(f"      📄 {subitem.name}")
                else:
                    print(f"   📄 {item.name}")
            return True
        else:
            print("❌ Crawl ran but no files were created")
            return False
    else:
        print("❌ Basic crawl failed")
        print(f"Error: {stderr}")
        return False

def test_example_usage():
    """Test the example usage script."""
    print("\n🔍 Testing example usage script...")
    
    if not Path("example_usage.py").exists():
        print("⚠️  example_usage.py not found, skipping this test")
        return True
    
    success, stdout, stderr = run_command("python example_usage.py")
    
    if success:
        print("✅ Example usage script works!")
        return True
    else:
        print("❌ Example usage script failed")
        print(f"Error: {stderr}")
        return False

def main():
    """Run all tests."""
    print("🚀 Web Crawler Test Suite")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Crawler Help", test_crawler_help),
        ("Basic Crawl", test_basic_crawl),
        ("Example Usage", test_example_usage)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The web crawler is working correctly.")
        print("\n📖 Next steps:")
        print("   - Read README.md for detailed usage instructions")
        print("   - Try: python crawler.py https://httpbin.org --max-pages 5")
        print("   - Check the downloaded_pages/ folder for results")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        print("   - Make sure all dependencies are installed: pip install requests beautifulsoup4 lxml")
        print("   - Check that you have internet connection")
        print("   - Ensure Python 3.7+ is installed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)