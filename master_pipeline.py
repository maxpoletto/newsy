#!/usr/bin/env python3
"""
Master pipeline for Trump Administration Policy Tracker
Orchestrates the complete processing workflow
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the modules (assuming they're in the same directory)
from process_diary import DiaryProcessor
from generate_html import IndexPageGenerator
from generate_summary import SummaryGenerator

async def run_pipeline(input_file: str, output_dir: str = "output", use_claude: bool = False):
    """Run the complete processing pipeline"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Step 1: Process diary entries
    logger.info("=" * 60)
    logger.info("STEP 1: Processing diary entries and tagging...")
    logger.info("=" * 60)
    
    processor = DiaryProcessor(input_file, output_dir)
    data = await processor.process()
    
    # Step 2: Generate index page
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Generating interactive index page...")
    logger.info("=" * 60)
    
    index_generator = IndexPageGenerator(
        str(output_path / "diary_data.json"),
        output_dir
    )
    index_generator.save_index_page()
    
    # Step 3: Generate summary page
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Generating thematic summary page...")
    logger.info("=" * 60)
    
    summary_generator = SummaryGenerator(
        str(output_path / "diary_data.json"),
        output_dir,
        use_claude_api=use_claude
    )
    await summary_generator.generate()
    
    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"\nGenerated files in '{output_dir}/':")
    logger.info("  - diary_data.json (and .json.gz) - Tagged entry data")
    logger.info("  - index.html - Interactive chronological view")
    logger.info("  - summary.html - Thematic summary page")
    logger.info("\nTo view the site, open index.html or summary.html in a web browser.")
    
    return data

def create_requirements_file():
    """Create requirements.txt file"""
    requirements = """# Requirements for Trump Administration Policy Tracker
aiohttp>=3.8.0
beautifulsoup4>=4.11.0
anthropic>=0.18.0  # Optional: for Claude API integration
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    logger.info("Created requirements.txt")

def create_readme():
    """Create README with instructions"""
    readme = """# Trump Administration Policy Tracker

A comprehensive system for processing, tagging, and presenting news articles about the Trump administration's policies and actions.

## Features

- **Automatic Tagging**: Categorizes articles into themes (broad categories) and keywords (specific topics)
- **Interactive Filtering**: Web interface with dual-level filtering by themes and keywords
- **Thematic Summaries**: Organized summary pages for each policy area
- **URL-based State**: Filter selections are preserved in URLs for easy sharing
- **Bluesky Support**: Special handling for Bluesky posts to fetch actual content
- **Compressed Data**: Supports gzipped JSON for efficient loading

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) For enhanced summaries using Claude API:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

## Usage

### Basic Processing

Process your diary file and generate the website:

```bash
python run_pipeline.py "Trump diary days 0001-0200.txt"
```

### With Claude API for Better Summaries

```bash
python run_pipeline.py "Trump diary days 0001-0200.txt" --use-claude
```

### Individual Components

You can also run components separately:

```bash
# Process and tag entries
python process_diary.py "Trump diary days 0001-0200.txt"

# Generate HTML pages
python generate_html.py output/diary_data.json
python generate_summary.py output/diary_data.json --use-claude
```

## Input Format

The input file should contain numbered entries with links:
```
1. <a href="URL">Article Title</a>
2. <a href="URL">Another Article</a>
...
```

## Output Files

- `output/diary_data.json` - Tagged entry data
- `output/diary_data.json.gz` - Compressed version for production
- `output/index.html` - Interactive chronological view
- `output/summary.html` - Thematic summary page

## Themes

Articles are categorized into these themes:
- **science**: NSF, NASA, research, climate
- **health**: CDC, FDA, NIH, vaccines, public health
- **education**: Universities, schools, students, academic freedom
- **environment**: EPA, pollution, climate policy
- **civil-society**: DEI, diversity, civil rights, democracy
- **human-rights**: LGBTQ+, discrimination, religious freedom
- **government**: Federal workforce, DOGE, efficiency initiatives
- **justice**: FBI, DOJ, courts, investigations
- **immigration**: ICE, deportations, refugees, visas
- **trade**: Tariffs, trade agreements, imports/exports
- **economy**: Taxes, budget, crypto, financial markets
- **foreign-affairs**: Ukraine, Russia, NATO, international relations

## Keywords

Specific entities and programs for granular filtering:
- Agencies: doge, fbi, ice, epa, cdc, nasa, nsf, nih
- Courts: supreme-court
- People: musk, rfk-jr, hegseth
- Universities: harvard, columbia
- Programs: voice-of-america, peace-corps, social-security, veterans
- Topics: tariffs, ukraine, russia, israel, lgbt, dei, climate, covid, abortion, crypto

## Automation with Claude API

For repeatable processing of future batches, create a script:

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

# Read your new entries
with open('new_entries.txt', 'r') as f:
    entries = f.read()

# Have Claude process and tag them
response = client.messages.create(
    model="claude-3-opus-20241022",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": f'''Please tag these news entries using the theme and keyword system.
        
        Themes: {themes_list}
        Keywords: {keywords_list}
        
        For each entry, assign 1-2 themes and up to 3 keywords.
        
        Entries:
        {entries}
        
        Return as JSON with structure: {{"entries": [...]}}'''
    }]
)
```

## Deployment

1. Upload all files in the `output/` directory to your web server
2. Ensure your server supports gzip compression for .json.gz files
3. No server-side processing needed - everything runs in the browser

## Future Enhancements

- [ ] Article archiving system
- [ ] Automated daily processing
- [ ] RSS feed generation
- [ ] Search functionality
- [ ] Data visualization charts
- [ ] Mobile app version

## Important Notes

- **Accuracy**: All summaries should be factual and cite sources
- **Bluesky**: Content fetching may require authentication in the future
- **Rate Limiting**: Be mindful of API limits when fetching content
- **Copyright**: Respect content licensing and fair use

## License

This project is for historical documentation and research purposes.
"""
    
    with open("README.md", "w") as f:
        f.write(readme)
    
    logger.info("Created README.md")