#!/usr/bin/env python3
"""
Summary Page Generator for Trump Administration Policy Tracker
Generates thematic summaries using Claude API for accuracy
"""

import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Theme descriptions and importance rankings
THEME_INFO = {
    'government': {
        'title': 'Federal Workforce Restructuring and Government Operations',
        'priority': 1,
        'description': 'Systematic restructuring of federal agencies, mass layoffs, and the Department of Government Efficiency (DOGE) initiatives'
    },
    'immigration': {
        'title': 'Immigration Enforcement and Deportation Operations',
        'priority': 2,
        'description': 'Border enforcement, deportation operations, visa policies, and treatment of refugees and asylum seekers'
    },
    'science': {
        'title': 'Scientific Research and Space Programs',
        'priority': 3,
        'description': 'Changes to NSF, NASA, climate research, and federal research funding'
    },
    'health': {
        'title': 'Healthcare Policy and Public Health',
        'priority': 4,
        'description': 'CDC policies, vaccine programs, NIH research, and public health infrastructure'
    },
    'education': {
        'title': 'Educational Institutions and Academic Freedom',
        'priority': 5,
        'description': 'University funding, DEI elimination, student visas, and academic research'
    },
    'justice': {
        'title': 'Justice Department and Law Enforcement',
        'priority': 6,
        'description': 'DOJ transformation, FBI changes, prosecutorial decisions, and judicial relations'
    },
    'economy': {
        'title': 'Economic Policy and Financial Markets',
        'priority': 7,
        'description': 'Tax policies, cryptocurrency, stock market regulations, and federal budget'
    },
    'trade': {
        'title': 'Trade Policy and Tariffs',
        'priority': 8,
        'description': 'Import tariffs, trade agreements, and international commerce'
    },
    'foreign-affairs': {
        'title': 'Foreign Policy and International Relations',
        'priority': 9,
        'description': 'Relations with allies and adversaries, military aid, and diplomatic initiatives'
    },
    'environment': {
        'title': 'Environmental Deregulation and Resource Extraction',
        'priority': 10,
        'description': 'EPA changes, climate policy rollbacks, and natural resource exploitation'
    },
    'human-rights': {
        'title': 'Civil Rights and Social Policy',
        'priority': 11,
        'description': 'LGBTQ+ rights, religious freedom, reproductive rights, and discrimination policies'
    },
    'civil-society': {
        'title': 'Democratic Institutions and Civil Society',
        'priority': 12,
        'description': 'Voting rights, democratic norms, civil society organizations, and constitutional issues'
    }
}

class SummaryGenerator:
    """Generates thematic summary page with optional Claude API integration"""
    
    def __init__(self, data_file: str, output_dir: str = "output", use_claude_api: bool = False):
        self.data_file = data_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_claude_api = use_claude_api
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.data = self.load_data()
        
    def load_data(self) -> Dict:
        """Load JSON data from file"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def organize_entries_by_theme(self) -> Dict[str, List]:
        """Organize entries by their primary theme"""
        themed_entries = defaultdict(list)
        
        for entry in self.data['entries']:
            if entry['themes']:
                primary_theme = entry['themes'][0]
                themed_entries[primary_theme].append(entry)
        
        return themed_entries
    
    async def generate_theme_summary_with_claude(self, theme: str, entries: List[Dict]) -> str:
        """Generate a theme summary using Claude API"""
        if not self.claude_api_key:
            logger.warning("Claude API key not found, using fallback summary")
            return self.generate_fallback_summary(theme, entries)
        
        # Prepare entry summaries for Claude
        entry_texts = []
        for entry in entries[:20]:  # Limit to top 20 entries per theme
            entry_texts.append(f"- {entry['title']} ({entry['url']})")
        
        prompt = f"""You are creating a summary for a historical archive of the Trump administration's policies.

Theme: {THEME_INFO[theme]['title']}
Description: {THEME_INFO[theme]['description']}

Based on these news articles about this theme, write 2-3 paragraphs summarizing the key developments and their significance. Be factual, precise, and cite specific examples from the articles. Each paragraph should be 3-4 sentences.

Articles:
{chr(10).join(entry_texts)}

IMPORTANT: 
- Be completely factual and accurate
- Reference specific articles when making claims
- Avoid speculation or editorializing
- Focus on documenting what happened according to the sources
- Write in past tense as this is a historical record"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': self.claude_api_key,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 500,
                        'messages': [{'role': 'user', 'content': prompt}]
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['content'][0]['text']
                    else:
                        logger.error(f"Claude API error: {response.status}")
                        return self.generate_fallback_summary(theme, entries)
                        
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self.generate_fallback_summary(theme, entries)
    
    def generate_fallback_summary(self, theme: str, entries: List[Dict]) -> str:
        """Generate a basic summary without API"""
        info = THEME_INFO[theme]
        
        # Group entries by keywords for better organization
        keyword_groups = defaultdict(list)
        for entry in entries:
            for keyword in entry.get('keywords', []):
                keyword_groups[keyword].append(entry)
        
        # Create basic summary
        summary = f"<p>The administration implemented significant changes in {info['description'].lower()}. "
        summary += f"This section documents {len(entries)} articles tracking these developments.</p>\n\n"
        
        # Add most common topics
        if keyword_groups:
            top_keywords = sorted(keyword_groups.items(), key=lambda x: len(x[1]), reverse=True)[:3]
            summary += "<p>Key areas of focus included "
            summary += ", ".join([f"{k} ({len(v)} articles)" for k, v in top_keywords])
            summary += ".</p>\n\n"
        
        # Sample articles
        summary += "<p>Notable developments included: "
        for entry in entries[:5]:
            summary += f'<a href="{entry["url"]}">{entry["title"]}</a>; '
        summary = summary.rstrip('; ') + ".</p>"
        
        return summary
    
    async def generate_summaries(self) -> Dict[str, str]:
        """Generate all theme summaries"""
        themed_entries = self.organize_entries_by_theme()
        summaries = {}
        
        for theme in THEME_INFO.keys():
            if theme in themed_entries:
                entries = themed_entries[theme]
                logger.info(f"Generating summary for {theme} ({len(entries)} entries)...")
                
                if self.use_claude_api:
                    summary = await self.generate_theme_summary_with_claude(theme, entries)
                else:
                    summary = self.generate_fallback_summary(theme, entries)
                
                summaries[theme] = summary
        
        return summaries
    
    def generate_summary_html(self, summaries: Dict[str, str]) -> str:
        """Generate the summary.html file content"""
        
        # Sort themes by priority
        sorted_themes = sorted(
            [(k, v) for k, v in THEME_INFO.items() if k in summaries],
            key=lambda x: x[1]['priority']
        )
        
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trump Administration Policy Tracker - Thematic Summary</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            color: #2c3e50;
            background: #f8f9fa;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .subtitle {
            opacity: 0.9;
            font-size: 1.1rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .nav-tabs {
            background: white;
            padding: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .nav-tabs .container {
            display: flex;
            gap: 2rem;
            padding: 0 20px;
        }
        
        .nav-tab {
            padding: 1rem 0;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
            color: #666;
        }
        
        .nav-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .intro {
            background: #fff;
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #667eea;
        }
        
        .intro p {
            margin-bottom: 1rem;
        }
        
        .intro p:last-child {
            margin-bottom: 0;
        }
        
        .toc {
            background: white;
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .toc h2 {
            font-size: 1.3rem;
            color: #34495e;
            margin-bottom: 1rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .toc ul {
            list-style: none;
        }
        
        .toc li {
            margin-bottom: 0.5rem;
        }
        
        .toc a {
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .toc a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        
        .theme-section {
            background: white;
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .theme-section h2 {
            color: #2c3e50;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .theme-section h3 {
            color: #34495e;
            font-size: 1.3rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .theme-section p {
            margin-bottom: 1rem;
            text-align: justify;
        }
        
        .theme-section a {
            color: #2980b9;
            text-decoration: none;
        }
        
        .theme-section a:hover {
            text-decoration: underline;
        }
        
        .view-all {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: #667eea;
            color: white;
            border-radius: 4px;
            text-decoration: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        
        .view-all:hover {
            background: #5a67d8;
            text-decoration: none;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            padding: 2rem 0;
            margin-top: 4rem;
            text-align: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .theme-section h2 { font-size: 1.4rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Trump Administration Policy Tracker</h1>
            <div class="subtitle">Days 1-200: Thematic Analysis</div>
        </div>
    </div>
    
    <div class="nav-tabs">
        <div class="container">
            <div class="nav-tab active">Thematic Summary</div>
            <div class="nav-tab" onclick="window.location.href='index.html'">Chronology</div>
        </div>
    </div>
    
    <div class="container">
        <div class="intro">
            <p><strong>This archive tracks major policy developments, personnel changes, and institutional reforms during the first 200 days of the Trump-Vance administration,</strong> compiled from daily observations and news reports from January through August 2025.</p>
            
            <p>The following thematic analysis organizes ''' + str(len(self.data['entries'])) + ''' news articles into key policy areas, documenting the scope and speed of changes across federal agencies, democratic institutions, and American society. Each section provides context and links to primary sources.</p>
            
            <p><em>Note: This is a historical record based on contemporary news reporting. All claims are linked to their original sources for verification.</em></p>
        </div>
        
        <div class="toc">
            <h2>Contents</h2>
            <ul>
'''
        
        # Add table of contents
        for theme_key, theme_info in sorted_themes:
            html += f'                <li><a href="#{theme_key}">{theme_info["title"]}</a></li>\n'
        
        html += '''            </ul>
        </div>
'''
        
        # Add theme sections
        themed_entries = self.organize_entries_by_theme()
        
        for theme_key, theme_info in sorted_themes:
            entries = themed_entries.get(theme_key, [])
            summary = summaries.get(theme_key, '')
            
            html += f'''
        <div class="theme-section" id="{theme_key}">
            <h2>{theme_info["title"]}</h2>
            {summary}
            <a href="index.html?themes={theme_key}" class="view-all">
                View all {len(entries)} articles in this category →
            </a>
        </div>
'''
        
        html += '''
        <div class="footer">
            <div class="container">
                <p>Generated: ''' + datetime.now().strftime('%B %d, %Y') + '''</p>
                <p>Source: Contemporary news reporting from major outlets</p>
            </div>
        </div>
    </div>
</body>
</html>
'''
        
        return html
    
    async def generate(self):
        """Main generation process"""
        logger.info("Generating thematic summaries...")
        
        summaries = await self.generate_summaries()
        html = self.generate_summary_html(summaries)
        
        output_path = self.output_dir / 'summary.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Saved summary.html to {output_path}")
        return summaries


async def main():
    """Main entry point for summary generation"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_summary.py <data_file> [--use-claude]")
        print("Example: python generate_summary.py output/diary_data.json --use-claude")
        sys.exit(1)
    
    data_file = sys.argv[1]
    use_claude = '--use-claude' in sys.argv
    
    if use_claude and not os.getenv('ANTHROPIC_API_KEY'):
        print("Warning: --use-claude specified but ANTHROPIC_API_KEY not found in environment")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
    
    generator = SummaryGenerator(data_file, use_claude_api=use_claude)
    await generator.generate()


if __name__ == "__main__":
    asyncio.run(main())
