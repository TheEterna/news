# Technology Stack

## Backend Framework
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Python 3.8+**: Core language with type hints throughout
- **Uvicorn**: ASGI server for production deployment

## Database & Storage
- **PostgreSQL**: Primary database with psycopg2-binary driver
- **File System**: JSON and HTML reports stored in `data/news/` directory
- **Database Schema**: Three main tables (batch_groups, search_tasks, news_items)

## AI & External Services
- **OpenAI API**: LLM integration for summarization and keyword generation
- **Serper.dev**: Primary news search engine (Google News API)
- **Custom AI Classification**: Batch processing for news relevance filtering

## Frontend & Templates
- **Jinja2**: Server-side HTML templating
- **Swiss Design System**: Custom CSS framework with minimalist aesthetic
- **Vanilla JavaScript**: No frontend frameworks, progressive enhancement approach

## Key Libraries
```
fastapi>=0.104.0          # Web framework
uvicorn>=0.24.0           # ASGI server
psycopg2-binary>=2.9.0    # PostgreSQL driver
openai>=1.0.0             # LLM integration
tavily-python>=0.5.0      # Search API (legacy)
google-search-results>=2.4.2  # SerpAPI (legacy)
pydantic>=2.0.0           # Data validation
jinja2>=3.1.0             # Templates
openpyxl>=3.1.0           # Excel processing
python-multipart>=0.0.6   # File uploads
```

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application
```bash
# Development server
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Database Management
- Database tables are auto-created on first run
- Migrations handled via SQL in `database/connection.py`
- No separate migration system - schema changes done in `_create_tables()`

### Configuration
- Environment variables in `.env` file
- Main config in `config.py`
- Database connection settings for PostgreSQL
- OpenAI API configuration for LLM calls