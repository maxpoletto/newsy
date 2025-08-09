#!/usr/bin/env python3
"""
HTML Generator for Trump Administration Policy Tracker
Generates the interactive index page with theme/keyword filtering
"""

import json
import gzip
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IndexPageGenerator:
    """Generates the interactive index page"""
    
    def __init__(self, data_file: str, output_dir: str = "output"):
        self.data_file = data_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.data = self.load_data()
        
    def load_data(self) -> Dict:
        """Load JSON data from file"""
        if self.data_file.endswith('.gz'):
            with gzip.open(self.data_file, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def generate_index_html(self) -> str:
        """Generate the index.html file content"""
        
        # Theme and keyword colors
        theme_colors = {
            'science': '#3498db',
            'health': '#e74c3c',
            'education': '#9b59b6',
            'environment': '#27ae60',
            'civil-society': '#f39c12',
            'human-rights': '#e67e22',
            'government': '#34495e',
            'justice': '#2c3e50',
            'immigration': '#16a085',
            'trade': '#8e44ad',
            'economy': '#2ecc71',
            'foreign-affairs': '#c0392b'
        }
        
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trump Administration Policy Tracker - Chronology</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .nav-tabs {
            background: white;
            padding: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
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
        
        .controls {
            background: white;
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .control-section {
            margin-bottom: 1.5rem;
        }
        
        .control-section:last-child {
            margin-bottom: 0;
        }
        
        .control-section h3 {
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #666;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .tags-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .tag {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
            font-weight: 500;
            border: 2px solid transparent;
            user-select: none;
        }
        
        .tag.theme {
            background: var(--color);
            color: white;
            opacity: 0.9;
        }
        
        .tag.theme.selected {
            opacity: 1;
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .tag.theme:not(.selected) {
            opacity: 0.4;
        }
        
        .tag.keyword {
            background: #f0f0f0;
            color: #333;
            border-color: #d0d0d0;
        }
        
        .tag.keyword.selected {
            background: #333;
            color: white;
            border-color: #333;
        }
        
        .stats {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 0.9rem;
        }
        
        .entries {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            padding: 1rem;
        }
        
        .entry {
            padding: 1rem;
            border-bottom: 1px solid #e0e0e0;
            transition: all 0.2s;
        }
        
        .entry:last-child {
            border-bottom: none;
        }
        
        .entry:hover {
            background: #f8f9fa;
        }
        
        .entry.hidden {
            display: none;
        }
        
        .entry-header {
            display: flex;
            align-items: baseline;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .entry-number {
            color: #999;
            font-size: 0.9rem;
            min-width: 50px;
        }
        
        .entry-title {
            flex: 1;
        }
        
        .entry-title a {
            color: #2c3e50;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }
        
        .entry-title a:hover {
            color: #667eea;
        }
        
        .entry-date {
            color: #666;
            font-size: 0.85rem;
        }
        
        .entry-tags {
            margin-left: 60px;
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.5rem;
        }
        
        .entry-tag {
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .entry-tag.theme {
            background: var(--color);
            color: white;
            opacity: 0.8;
        }
        
        .entry-tag.theme:hover {
            opacity: 1;
        }
        
        .entry-tag.keyword {
            background: #f0f0f0;
            color: #666;
            border: 1px solid #d0d0d0;
        }
        
        .entry-tag.keyword:hover {
            background: #333;
            color: white;
            border-color: #333;
        }
        
        .select-controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .select-btn {
            padding: 0.4rem 1rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        
        .select-btn:hover {
            background: #5a67d8;
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .entry-header { flex-direction: column; gap: 0.5rem; }
            .entry-tags { margin-left: 0; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Trump Administration Policy Tracker</h1>
            <div class="subtitle">Days 1-200: Comprehensive News Archive</div>
        </div>
    </div>
    
    <div class="nav-tabs">
        <div class="container">
            <div class="nav-tab" onclick="window.location.href='summary.html'">Thematic Summary</div>
            <div class="nav-tab active">Chronology</div>
        </div>
    </div>
    
    <div class="container">
        <div class="controls">
            <div class="control-section">
                <h3>Themes</h3>
                <div class="select-controls">
                    <button class="select-btn" onclick="selectAllThemes()">Select All</button>
                    <button class="select-btn" onclick="deselectAllThemes()">Deselect All</button>
                </div>
                <div class="tags-container" id="themes-container"></div>
            </div>
            
            <div class="control-section">
                <h3>Keywords</h3>
                <div class="select-controls">
                    <button class="select-btn" onclick="selectAllKeywords()">Select All</button>
                    <button class="select-btn" onclick="deselectAllKeywords()">Deselect All</button>
                </div>
                <div class="tags-container" id="keywords-container"></div>
            </div>
            
            <div class="stats" id="stats">
                Showing <span id="visible-count">0</span> of <span id="total-count">0</span> entries
            </div>
        </div>
        
        <div class="entries" id="entries-container">
            <!-- Entries will be populated by JavaScript -->
        </div>
    </div>
    
    <script>
        // Theme colors mapping
        const themeColors = ''' + json.dumps(theme_colors) + ''';
        
        // Global data
        let diaryData = null;
        let selectedThemes = new Set();
        let selectedKeywords = new Set();
        
        // Load data on page load
        async function loadData() {
            try {
                // Try compressed version first
                let response = await fetch('diary_data.json.gz');
                if (!response.ok) {
                    // Fall back to uncompressed
                    response = await fetch('diary_data.json');
                }
                diaryData = await response.json();
                initializeControls();
                renderEntries();
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('entries-container').innerHTML = 
                    '<p style="color: red; padding: 2rem;">Error loading data. Please ensure diary_data.json is available.</p>';
            }
        }
        
        function initializeControls() {
            // Initialize themes
            const themesContainer = document.getElementById('themes-container');
            diaryData.metadata.themes.forEach(theme => {
                const tag = createTag(theme, 'theme', themeColors[theme] || '#666');
                themesContainer.appendChild(tag);
                selectedThemes.add(theme);
            });
            
            // Initialize keywords
            const keywordsContainer = document.getElementById('keywords-container');
            diaryData.metadata.keywords.forEach(keyword => {
                const tag = createTag(keyword, 'keyword');
                keywordsContainer.appendChild(tag);
                selectedKeywords.add(keyword);
            });
            
            // Update from URL parameters
            updateFromURL();
        }
        
        function createTag(name, type, color = null) {
            const tag = document.createElement('div');
            tag.className = `tag ${type} selected`;
            tag.textContent = name;
            tag.dataset.value = name;
            
            if (color) {
                tag.style.setProperty('--color', color);
            }
            
            tag.onclick = () => toggleTag(name, type);
            
            return tag;
        }
        
        function toggleTag(value, type) {
            const set = type === 'theme' ? selectedThemes : selectedKeywords;
            
            if (set.has(value)) {
                set.delete(value);
            } else {
                set.add(value);
            }
            
            // Update UI
            const tag = document.querySelector(`.tag.${type}[data-value="${value}"]`);
            tag.classList.toggle('selected');
            
            // Update URL and render
            updateURL();
            renderEntries();
        }
        
        function selectAllThemes() {
            diaryData.metadata.themes.forEach(theme => {
                selectedThemes.add(theme);
                document.querySelector(`.tag.theme[data-value="${theme}"]`).classList.add('selected');
            });
            updateURL();
            renderEntries();
        }
        
        function deselectAllThemes() {
            selectedThemes.clear();
            document.querySelectorAll('.tag.theme').forEach(tag => {
                tag.classList.remove('selected');
            });
            updateURL();
            renderEntries();
        }
        
        function selectAllKeywords() {
            diaryData.metadata.keywords.forEach(keyword => {
                selectedKeywords.add(keyword);
                document.querySelector(`.tag.keyword[data-value="${keyword}"]`).classList.add('selected');
            });
            updateURL();
            renderEntries();
        }
        
        function deselectAllKeywords() {
            selectedKeywords.clear();
            document.querySelectorAll('.tag.keyword').forEach(tag => {
                tag.classList.remove('selected');
            });
            updateURL();
            renderEntries();
        }
        
        function renderEntries() {
            const container = document.getElementById('entries-container');
            container.innerHTML = '';
            
            let visibleCount = 0;
            
            diaryData.entries.forEach(entry => {
                // Check if entry matches filters
                const hasSelectedTheme = entry.themes.some(t => selectedThemes.has(t));
                const hasSelectedKeyword = entry.keywords.length === 0 || 
                                         entry.keywords.some(k => selectedKeywords.has(k));
                
                if (hasSelectedTheme && hasSelectedKeyword) {
                    visibleCount++;
                    const entryEl = createEntryElement(entry);
                    container.appendChild(entryEl);
                }
            });
            
            // Update stats
            document.getElementById('visible-count').textContent = visibleCount;
            document.getElementById('total-count').textContent = diaryData.entries.length;
        }
        
        function createEntryElement(entry) {
            const div = document.createElement('div');
            div.className = 'entry';
            
            // Create header with number, title, and date
            const header = document.createElement('div');
            header.className = 'entry-header';
            
            const number = document.createElement('span');
            number.className = 'entry-number';
            number.textContent = `#${entry.id}`;
            
            const title = document.createElement('span');
            title.className = 'entry-title';
            const link = document.createElement('a');
            link.href = entry.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = entry.title;
            title.appendChild(link);
            
            header.appendChild(number);
            header.appendChild(title);
            
            if (entry.date) {
                const date = document.createElement('span');
                date.className = 'entry-date';
                date.textContent = entry.date;
                header.appendChild(date);
            }
            
            div.appendChild(header);
            
            // Create tags
            if (entry.themes.length > 0 || entry.keywords.length > 0) {
                const tagsDiv = document.createElement('div');
                tagsDiv.className = 'entry-tags';
                
                // Add theme tags
                entry.themes.forEach(theme => {
                    const tag = document.createElement('span');
                    tag.className = 'entry-tag theme';
                    tag.textContent = theme;
                    tag.style.setProperty('--color', themeColors[theme] || '#666');
                    tag.onclick = (e) => {
                        e.stopPropagation();
                        // Toggle this theme in controls
                        toggleTag(theme, 'theme');
                    };
                    tagsDiv.appendChild(tag);
                });
                
                // Add keyword tags
                entry.keywords.forEach(keyword => {
                    const tag = document.createElement('span');
                    tag.className = 'entry-tag keyword';
                    tag.textContent = keyword;
                    tag.onclick = (e) => {
                        e.stopPropagation();
                        // Toggle this keyword in controls
                        toggleTag(keyword, 'keyword');
                    };
                    tagsDiv.appendChild(tag);
                });
                
                div.appendChild(tagsDiv);
            }
            
            return div;
        }
        
        function updateURL() {
            const params = new URLSearchParams();
            
            if (selectedThemes.size !== diaryData.metadata.themes.length) {
                params.set('themes', Array.from(selectedThemes).join(','));
            }
            
            if (selectedKeywords.size !== diaryData.metadata.keywords.length) {
                params.set('keywords', Array.from(selectedKeywords).join(','));
            }
            
            const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
            window.history.replaceState({}, '', newURL);
        }
        
        function updateFromURL() {
            const params = new URLSearchParams(window.location.search);
            
            // Update themes from URL
            if (params.has('themes')) {
                const themes = params.get('themes').split(',').filter(t => t);
                selectedThemes = new Set(themes);
                
                // Update UI
                document.querySelectorAll('.tag.theme').forEach(tag => {
                    if (selectedThemes.has(tag.dataset.value)) {
                        tag.classList.add('selected');
                    } else {
                        tag.classList.remove('selected');
                    }
                });
            }
            
            // Update keywords from URL
            if (params.has('keywords')) {
                const keywords = params.get('keywords').split(',').filter(k => k);
                selectedKeywords = new Set(keywords);
                
                // Update UI
                document.querySelectorAll('.tag.keyword').forEach(tag => {
                    if (selectedKeywords.has(tag.dataset.value)) {
                        tag.classList.add('selected');
                    } else {
                        tag.classList.remove('selected');
                    }
                });
            }
        }
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
'''
        
        return html
    
    def save_index_page(self):
        """Save the index.html file"""
        html = self.generate_index_html()
        output_path = self.output_dir / 'index.html'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Saved index.html to {output_path}")


def generate_html_files(data_file: str, output_dir: str = "output"):
    """Generate all HTML files"""
    generator = IndexPageGenerator(data_file, output_dir)
    generator.save_index_page()
    logger.info("HTML generation complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python generate_html.py <data_file>")
        print("Example: python generate_html.py output/diary_data.json")
        sys.exit(1)
    
    generate_html_files(sys.argv[1])