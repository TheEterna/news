# Project Structure

## Directory Organization

```
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
│
├── models/               # Pydantic data models
│   ├── schemas.py        # Request/response schemas
│   └── __init__.py
│
├── services/             # Business logic layer
│   ├── keyword_generator.py    # AI keyword generation
│   ├── news_crawler.py         # News collection orchestrator
│   ├── news_classifier.py     # AI news filtering
│   ├── summarizer.py          # AI summarization
│   ├── renderer.py            # HTML template rendering
│   ├── spreadsheet_parser.py  # Excel/CSV processing
│   ├── search_engine/         # Search engine implementations
│   │   ├── serper_engine.py   # Serper.dev integration
│   │   ├── baidu_engine.py    # Baidu search (legacy)
│   │   └── tavily_engine.py   # Tavily search (legacy)
│   └── __init__.py
│
├── database/             # Data access layer
│   ├── connection.py     # PostgreSQL connection & schema
│   ├── repository.py     # Data access methods
│   └── __init__.py
│
├── templates/            # Jinja2 HTML templates
│   ├── index.html        # Main dashboard
│   ├── batch.html        # Batch processing UI
│   ├── news_browser.html # News filtering interface
│   ├── tasks.html        # Task management
│   ├── review_list.html  # Human review interface
│   ├── final_report.html # Generated reports
│   └── *.html
│
├── utils/                # Shared utilities
│   ├── logger.py         # Logging configuration
│   └── __init__.py
│
└── data/                 # File storage
    └── news/             # Generated JSON/HTML files
        ├── *.json        # Raw data exports
        ├── *_列表.html    # News list pages
        └── *_详情.html    # Detailed reports
```

## Architecture Patterns

### Service Layer Pattern
- **Services**: Business logic encapsulated in service classes
- **Repository**: Data access abstraction over PostgreSQL
- **Models**: Pydantic schemas for validation and serialization

### Dependency Injection
- Singleton pattern for service instances (`get_*()` functions)
- Lazy initialization to avoid circular imports
- Clean separation between layers

### API Design
- RESTful endpoints with clear versioning (`/api/v2/`)
- Consistent response formats using Pydantic models
- HTML responses for user-facing pages, JSON for API calls

## File Naming Conventions

### Python Files
- **Snake_case**: All Python files and directories
- **Descriptive names**: `news_crawler.py`, `keyword_generator.py`
- **Service suffix**: Services end with purpose (e.g., `_engine.py`, `_parser.py`)

### Templates
- **Lowercase**: HTML templates in lowercase
- **Purpose-based**: Named after their function (`review_list.html`)
- **Chinese suffixes**: Generated files use Chinese descriptors (`_列表.html`, `_详情.html`)

### Data Files
- **Timestamp format**: `{company}_{YYYYMMDD_HHMMSS}.json`
- **Descriptive suffixes**: `_列表.html` (list), `_详情.html` (details)

## Import Conventions

### Relative Imports
```python
# Within same package
from .schemas import NewsItem

# Cross-package imports
from models.schemas import NewsRequest
from services.news_crawler import get_news_crawler
from database.repository import get_repository
```

### External Dependencies
```python
# Standard library first
import json
from datetime import datetime
from pathlib import Path

# Third-party packages
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports last
from config import DATA_DIR
from utils.logger import logger
```

## Configuration Management

### Environment Variables
- **Required**: `OPENAI_API_KEY`, `SERPER_API_KEY`
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Optional**: `OPENAI_BASE_URL`, `MODEL_NAME`

### Default Values
- Fallback values in `config.py` for development
- Production values should override via environment variables
- Sensitive data never committed to repository