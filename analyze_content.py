#!/usr/bin/env python3
"""
Content Analysis Tool
Analyze and explore extracted content from web crawling.
"""

import json
import os
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Any
import re


class ContentAnalyzer:
    """
    Analyze extracted content from web crawling.
    """
    
    def __init__(self, data_directory: str = "downloaded_pages"):
        self.data_dir = Path(data_directory)
        self.extracted_data = []
        self._load_extracted_data()
    
    def _load_extracted_data(self):
        """Load all JSON files with extracted content."""
        json_files = list(self.data_dir.rglob("*.json"))
        
        print(f"[LOADING] Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.extracted_data.append(data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"[ERROR] Failed to load {json_file}: {e}")
        
        print(f"[LOADED] Successfully loaded {len(self.extracted_data)} pages")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if not self.extracted_data:
            print("[ERROR] No data to analyze")
            return
        
        print("=" * 60)
        print("CONTENT ANALYSIS SUMMARY REPORT")
        print("=" * 60)
        
        # Basic statistics
        total_pages = len(self.extracted_data)
        total_words = sum(page.get('word_count', 0) for page in self.extracted_data)
        total_images = sum(len(page.get('images', [])) for page in self.extracted_data)
        total_internal_links = sum(len(page.get('internal_links', [])) for page in self.extracted_data)
        total_external_links = sum(len(page.get('external_links', [])) for page in self.extracted_data)
        
        print(f"📊 OVERVIEW:")
        print(f"   • Total Pages Analyzed: {total_pages}")
        print(f"   • Total Words: {total_words:,}")
        print(f"   • Average Words per Page: {total_words / total_pages:.0f}")
        print(f"   • Total Images: {total_images}")
        print(f"   • Total Internal Links: {total_internal_links}")
        print(f"   • Total External Links: {total_external_links}")
        
        # Language distribution
        languages = Counter(page.get('language', 'unknown') for page in self.extracted_data)
        print(f"\n🌐 LANGUAGES:")
        for lang, count in languages.most_common(5):
            print(f"   • {lang}: {count} pages")
        
        # Content types analysis
        self._analyze_content_types()
        
        # Most common words in titles
        self._analyze_titles()
        
        # Author analysis
        self._analyze_authors()
        
        # External domains analysis
        self._analyze_external_domains()
        
        # Content length distribution
        self._analyze_content_length()
    
    def _analyze_content_types(self):
        """Analyze content sections and types."""
        print(f"\n📄 CONTENT SECTIONS:")
        
        section_totals = defaultdict(int)
        for page in self.extracted_data:
            sections = page.get('content_sections', {})
            for section, count in sections.items():
                section_totals[section] += count
        
        for section, total in sorted(section_totals.items(), key=lambda x: x[1], reverse=True):
            avg = total / len(self.extracted_data)
            print(f"   • {section.title()}: {total} total ({avg:.1f} avg per page)")
    
    def _analyze_titles(self):
        """Analyze page titles."""
        print(f"\n📝 TITLE ANALYSIS:")
        
        titles = [page.get('title', '') for page in self.extracted_data if page.get('title')]
        
        if titles:
            avg_title_length = sum(len(title) for title in titles) / len(titles)
            print(f"   • Average Title Length: {avg_title_length:.0f} characters")
            
            # Most common words in titles
            title_words = []
            for title in titles:
                words = re.findall(r'\b\w+\b', title.lower())
                title_words.extend(word for word in words if len(word) > 3)
            
            common_words = Counter(title_words).most_common(10)
            print(f"   • Most Common Title Words:")
            for word, count in common_words:
                print(f"     - {word}: {count}")
    
    def _analyze_authors(self):
        """Analyze author information."""
        print(f"\n✍️ AUTHOR ANALYSIS:")
        
        authors = Counter(page.get('author', 'Unknown') for page in self.extracted_data)
        known_authors = {author: count for author, count in authors.items() 
                        if author not in ['Unknown', '', 'N/A']}
        
        if known_authors:
            print(f"   • Authors Found: {len(known_authors)}")
            print(f"   • Top Authors:")
            for author, count in Counter(known_authors).most_common(5):
                print(f"     - {author}: {count} pages")
        else:
            print(f"   • No author information found")
    
    def _analyze_external_domains(self):
        """Analyze external domains linked to."""
        print(f"\n🔗 EXTERNAL DOMAINS:")
        
        domain_counter = Counter()
        for page in self.extracted_data:
            external_links = page.get('external_links', [])
            for link in external_links:
                url = link.get('url', '')
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        if domain:
                            domain_counter[domain] += 1
                    except:
                        continue
        
        if domain_counter:
            print(f"   • Most Linked External Domains:")
            for domain, count in domain_counter.most_common(10):
                print(f"     - {domain}: {count} links")
        else:
            print(f"   • No external domains found")
    
    def _analyze_content_length(self):
        """Analyze content length distribution."""
        print(f"\n📏 CONTENT LENGTH DISTRIBUTION:")
        
        word_counts = [page.get('word_count', 0) for page in self.extracted_data]
        
        if word_counts:
            word_counts.sort()
            total = len(word_counts)
            
            print(f"   • Shortest Page: {word_counts[0]} words")
            print(f"   • Longest Page: {word_counts[-1]} words")
            print(f"   • Median: {word_counts[total//2]} words")
            
            # Distribution buckets
            buckets = {
                'Very Short (0-100 words)': sum(1 for wc in word_counts if 0 <= wc <= 100),
                'Short (101-500 words)': sum(1 for wc in word_counts if 101 <= wc <= 500),
                'Medium (501-1500 words)': sum(1 for wc in word_counts if 501 <= wc <= 1500),
                'Long (1501-3000 words)': sum(1 for wc in word_counts if 1501 <= wc <= 3000),
                'Very Long (3000+ words)': sum(1 for wc in word_counts if wc > 3000),
            }
            
            print(f"   • Length Distribution:")
            for category, count in buckets.items():
                percentage = (count / total) * 100
                print(f"     - {category}: {count} pages ({percentage:.1f}%)")
    
    def search_content(self, keyword: str, field: str = 'title'):
        """Search for specific content."""
        keyword = keyword.lower()
        matches = []
        
        for page in self.extracted_data:
            if field == 'title':
                text = page.get('title', '').lower()
            elif field == 'description':
                text = page.get('description', '').lower()
            elif field == 'content':
                text = page.get('text_content', '').lower()
            elif field == 'author':
                text = page.get('author', '').lower()
            else:
                continue
            
            if keyword in text:
                matches.append({
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    field: page.get(field, '')
                })
        
        print(f"\n🔍 SEARCH RESULTS for '{keyword}' in {field}:")
        print(f"   Found {len(matches)} matches")
        
        for match in matches[:10]:  # Show top 10
            print(f"   • {match['title']}")
            print(f"     URL: {match['url']}")
            if field != 'title':
                content = match[field][:100] + "..." if len(match[field]) > 100 else match[field]
                print(f"     {field.title()}: {content}")
            print()
    
    def export_summary(self, filename: str = "content_analysis.json"):
        """Export analysis summary to JSON."""
        if not self.extracted_data:
            print("[ERROR] No data to export")
            return
        
        summary = {
            'analysis_date': str(Path().cwd()),
            'total_pages': len(self.extracted_data),
            'total_words': sum(page.get('word_count', 0) for page in self.extracted_data),
            'languages': dict(Counter(page.get('language', 'unknown') for page in self.extracted_data)),
            'authors': dict(Counter(page.get('author', 'Unknown') for page in self.extracted_data)),
            'pages': self.extracted_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"[EXPORT] Analysis exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Analyze extracted web content")
    parser.add_argument('--dir', default='downloaded_pages', help='Directory containing extracted data')
    parser.add_argument('--search', help='Search for keyword in content')
    parser.add_argument('--field', default='title', choices=['title', 'description', 'content', 'author'],
                       help='Field to search in')
    parser.add_argument('--export', help='Export analysis to JSON file')
    
    args = parser.parse_args()
    
    analyzer = ContentAnalyzer(args.dir)
    
    if args.search:
        analyzer.search_content(args.search, args.field)
    else:
        analyzer.generate_summary_report()
    
    if args.export:
        analyzer.export_summary(args.export)


if __name__ == "__main__":
    main()