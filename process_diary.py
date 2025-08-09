#!/usr/bin/env python3
"""
Trump Administration Policy Tracker
Processes news diary entries, tags them, and generates an interactive website
"""

import json
import re
import os
import gzip
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Theme definitions (broader categories for summary page)
THEMES = {
    'science': ['nsf', 'nasa', 'research', 'climate', 'weather', 'scientist'],
    'health': ['cdc', 'fda', 'nih', 'vaccine', 'covid', 'pandemic', 'health', 'medical', 'hospital'],
    'education': ['education', 'school', 'university', 'college', 'student', 'teacher', 'harvard', 'columbia'],
    'environment': ['epa', 'environment', 'pollution', 'clean', 'toxic', 'waste', 'water', 'air'],
    'civil-society': ['dei', 'diversity', 'equity', 'inclusion', 'civil-rights', 'voting', 'democracy'],
    'human-rights': ['lgbtq', 'transgender', 'discrimination', 'religious', 'freedom', 'abortion'],
    'government': ['federal', 'employee', 'workforce', 'doge', 'efficiency', 'layoff', 'resign'],
    'justice': ['fbi', 'doj', 'court', 'judge', 'attorney', 'prosecutor', 'investigation'],
    'immigration': ['ice', 'deportation', 'immigrant', 'refugee', 'border', 'asylum', 'visa'],
    'trade': ['tariff', 'trade', 'import', 'export', 'nafta', 'china'],
    'economy': ['tax', 'budget', 'debt', 'inflation', 'crypto', 'bitcoin', 'stock', 'economy'],
    'foreign-affairs': ['ukraine', 'russia', 'israel', 'palestine', 'nato', 'china', 'foreign']
}

# Keyword definitions (specific entities/programs for granular filtering)
KEYWORD_PATTERNS = {
    'doge': ['doge', 'efficiency'],
    'fbi': ['fbi', 'federal bureau'],
    'ice': ['ice', 'immigration enforcement'],
    'epa': ['epa', 'environmental protection'],
    'cdc': ['cdc', 'disease control'],
    'nasa': ['nasa', 'space'],
    'nsf': ['nsf', 'national science foundation'],
    'nih': ['nih', 'health institute'],
    'supreme-court': ['supreme court', 'scotus'],
    'tariffs': ['tariff'],
    'ukraine': ['ukraine', 'zelensky'],
    'russia': ['russia', 'putin'],
    'israel': ['israel', 'gaza', 'palestine'],
    'musk': ['musk', 'elon'],
    'rfk-jr': ['rfk', 'kennedy jr'],
    'hegseth': ['hegseth'],
    'harvard': ['harvard'],
    'columbia': ['columbia university'],
    'voice-of-america': ['voice of america', 'voa'],
    'peace-corps': ['peace corps'],
    'social-security': ['social security', 'ssa'],
    'veterans': ['veteran', 'va '],
    'medicare': ['medicare', 'medicaid'],
    'lgbt': ['lgbt', 'transgender', 'gay', 'lesbian'],
    'dei': ['dei', 'diversity', 'equity', 'inclusion'],
    'climate': ['climate', 'carbon', 'emission'],
    'covid': ['covid', 'coronavirus', 'pandemic'],
    'abortion': ['abortion', 'reproductive'],
    'crypto': ['crypto', 'bitcoin', 'digital currency']
}

@dataclass
class NewsEntry:
    """Represents a single news entry"""
    id: int
    url: str
    title: str
    date: Optional[str] = None
    themes: List[str] = None
    keywords: List[str] = None
    content_snippet: Optional[str] = None
    
    def __post_init__(self):
        if self.themes is None:
            self.themes = []
        if self.keywords is None:
            self.keywords = []

class DiaryProcessor:
    """Main processor for Trump diary entries"""
    
    def __init__(self, input_file: str, output_dir: str = "output"):
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.entries: List[NewsEntry] = []
        self.bluesky_content_cache = {}
        
    def parse_input_file(self) -> List[NewsEntry]:
        """Parse the input text file into NewsEntry objects"""
        entries = []
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Parse each line: "N. <a href="URL">TITLE</a>"
            match = re.match(r'^\d+\.\s*<a href="([^"]+)">([^<]+)</a>', line.strip())
            if match:
                url = match.group(1)
                title = match.group(2)
                
                entry = NewsEntry(
                    id=i,
                    url=url,
                    title=title,
                    date=self.extract_date(url)
                )
                entries.append(entry)
            else:
                logger.warning(f"Could not parse line {i}: {line[:100]}")
        
        logger.info(f"Parsed {len(entries)} entries from input file")
        return entries
    
    def extract_date(self, url: str) -> Optional[str]:
        """Extract date from URL if possible"""
        # Common date patterns in URLs
        patterns = [
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /YYYY/MM/DD/
            r'/(\d{4})-(\d{2})-(\d{2})',        # /YYYY-MM-DD
            r'(\d{4})(\d{2})(\d{2})',           # YYYYMMDD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    if 2024 <= year <= 2026 and 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year:04d}-{month:02d}-{day:02d}"
                except:
                    continue
        return None
    
    def tag_entry(self, entry: NewsEntry) -> None:
        """Tag an entry with themes and keywords based on URL and title"""
        text = f"{entry.url} {entry.title}".lower()
        
        # Assign themes (aim for 1-2)
        theme_scores = {}
        for theme, patterns in THEMES.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                theme_scores[theme] = score
        
        # Take top 2 themes
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        entry.themes = [theme for theme, _ in sorted_themes[:2]]
        
        # Assign keywords (max 3)
        keyword_matches = []
        for keyword, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    keyword_matches.append(keyword)
                    break
        
        entry.keywords = list(set(keyword_matches))[:3]
        
        # Default theme if none found
        if not entry.themes:
            # Fallback based on domain
            domain = urlparse(entry.url).netloc
            if 'supreme' in domain or 'scotus' in domain:
                entry.themes = ['justice']
            elif any(gov in domain for gov in ['.gov', 'whitehouse']):
                entry.themes = ['government']
            else:
                entry.themes = ['government']  # Generic fallback
    
    async def fetch_bluesky_content(self, url: str) -> Optional[str]:
        """Fetch content from Bluesky posts"""
        if url in self.bluesky_content_cache:
            return self.bluesky_content_cache[url]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Look for post content in various possible containers
                        content_selectors = [
                            'div[data-testid="postText"]',
                            'div.post-content',
                            'div[class*="post"]',
                            'meta[property="og:description"]'
                        ]
                        
                        for selector in content_selectors:
                            element = soup.select_one(selector)
                            if element:
                                content = element.get('content') if element.name == 'meta' else element.get_text()
                                self.bluesky_content_cache[url] = content[:500]  # Limit length
                                return content[:500]
                        
                        logger.warning(f"Could not extract content from Bluesky URL: {url}")
        except Exception as e:
            logger.error(f"Error fetching Bluesky content from {url}: {e}")
        
        return None
    
    async def process_bluesky_entries(self):
        """Process all Bluesky entries to fetch their content"""
        bluesky_entries = [e for e in self.entries if 'bsky.app' in e.url]
        
        if not bluesky_entries:
            return
        
        logger.info(f"Fetching content for {len(bluesky_entries)} Bluesky posts...")
        
        tasks = []
        for entry in bluesky_entries:
            tasks.append(self.fetch_bluesky_content(entry.url))
        
        contents = await asyncio.gather(*tasks)
        
        for entry, content in zip(bluesky_entries, contents):
            if content:
                entry.content_snippet = content
                # Re-tag with the actual content
                self.tag_entry_with_content(entry, content)
    
    def tag_entry_with_content(self, entry: NewsEntry, content: str):
        """Re-tag entry using actual content (for Bluesky posts)"""
        combined_text = f"{entry.url} {entry.title} {content}".lower()
        
        # Re-run tagging with additional content
        theme_scores = {}
        for theme, patterns in THEMES.items():
            score = sum(2 if pattern in content.lower() else 1 
                       for pattern in patterns 
                       if pattern in combined_text)
            if score > 0:
                theme_scores[theme] = score
        
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        entry.themes = [theme for theme, _ in sorted_themes[:2]]
        
        # Re-assign keywords
        keyword_matches = []
        for keyword, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined_text:
                    keyword_matches.append(keyword)
                    break
        
        entry.keywords = list(set(keyword_matches))[:3]
    
    def generate_json_data(self) -> Dict:
        """Generate JSON data structure for the website"""
        return {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'total_entries': len(self.entries),
                'themes': list(THEMES.keys()),
                'keywords': list(KEYWORD_PATTERNS.keys())
            },
            'entries': [asdict(entry) for entry in self.entries]
        }
    
    def save_compressed_json(self, data: Dict, filename: str):
        """Save JSON data as compressed gzip file"""
        json_path = self.output_dir / filename
        gz_path = self.output_dir / f"{filename}.gz"
        
        # Save uncompressed for development
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save compressed for production
        with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"Saved data to {json_path} and {gz_path}")
    
    async def process(self):
        """Main processing pipeline"""
        logger.info("Starting diary processing...")
        
        # Parse input file
        self.entries = self.parse_input_file()
        
        # Initial tagging based on URL and title
        logger.info("Tagging entries...")
        for entry in self.entries:
            self.tag_entry(entry)
        
        # Fetch Bluesky content and re-tag those entries
        await self.process_bluesky_entries()
        
        # Generate and save JSON data
        data = self.generate_json_data()
        self.save_compressed_json(data, 'diary_data.json')
        
        # Generate statistics
        self.print_statistics()
        
        logger.info("Processing complete!")
        return data
    
    def print_statistics(self):
        """Print statistics about the processed entries"""
        theme_counts = {}
        keyword_counts = {}
        
        for entry in self.entries:
            for theme in entry.themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            for keyword in entry.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        print("\n=== Processing Statistics ===")
        print(f"Total entries: {len(self.entries)}")
        print(f"Entries with dates: {sum(1 for e in self.entries if e.date)}")
        print(f"Bluesky entries: {sum(1 for e in self.entries if 'bsky.app' in e.url)}")
        
        print("\n=== Theme Distribution ===")
        for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {theme}: {count}")
        
        print("\n=== Top Keywords ===")
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {keyword}: {count}")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python process_diary.py <input_file>")
        print("Example: python process_diary.py 'Trump diary days 0001-0200.txt'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    processor = DiaryProcessor(input_file)
    await processor.process()


if __name__ == "__main__":
    asyncio.run(main())
