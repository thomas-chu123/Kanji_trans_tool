# Copilot Instructions for Kanji_trans_tool

## Project Overview

**日文文章轉換工具** (Japanese Article Conversion Tool) - A FastAPI web application that converts Japanese text to furigana (reading), hiragana, and romanized (romaji) representations. The app supports text input, file uploads (TXT/PDF), image OCR, Chinese translation, and provides a history/favorites system.

## Development Setup

### Initial Setup
```bash
# One-command setup (creates venv, installs dependencies, initializes database)
bash setup.sh
```

### Running the Application
```bash
# Development server (auto-reload on changes)
bash run.sh
# Or manually:
source venv/bin/activate
python -m uvicorn app:app --host 0.0.0.0 --port 8888 --reload
```

The app runs on **http://localhost:8888** with API docs at **http://localhost:8888/docs**

### Database Operations
```bash
# Initialize/reset database
python db/init_db.py
```

### Running Tests
```bash
# End-to-end test (requires app running in another terminal)
python tests/test_e2e.py

# Individual test modules
python tests/test_ocr.py
python tests/test_translate.py
python -m pytest tests/  # if pytest is installed
```

## High-Level Architecture

### 1. **Request Flow**
- User submits text/file via `POST /convert` form
- FastAPI handler validates input (size limits, encoding)
- Text is processed through multiple modules (furigana → romanization → HTML generation)
- Optional: Chinese translation via translation module
- Result is saved to SQLite, then redirected to results page

### 2. **Core Processing Pipeline** (`processors/`)
- **furigana.py**: PyKakasi integration (main Japanese processing)
  - Global `_kakasi_instance` singleton initialized at app startup
  - `process_text()` → returns list of `Token` objects with original/hiragana/romanji/type
  - `generate_ruby_html()` → generates HTML with `<ruby>` tags for display
  
- **romanization.py**: Hiragana ↔ Romaji conversion using Hepburn standard
  
- **translator.py**: Chinese translation via `translate` library with global translator instance
  
- **ocr.py**: PaddleOCR for image text extraction (supports JPG/PNG/GIF/BMP)
  
- **storage.py**: SQLite CRUD operations for translations and favorites

### 3. **Frontend Architecture**
- **Templates** (Jinja2):
  - `base.html` - Base layout with Tailwind CSS (CDN), navigation, footer
  - `index.html` - Main input page with text area, file upload, recent/favorites sidebar
  - `results.html` - Result display with ruby text rendering, copy/download/favorite buttons
  - `history.html` - Paginated search history (20 items per page)
  - `favorites.html` - Saved favorites with notes/tags
  
- **Static Files** (Tailwind CSS via CDN):
  - `static/css/custom.css` - Custom styling for ruby tags, responsive layout
  - `static/js/main.js` - Form handling, copy functionality, dynamic textarea resizing

### 4. **Data Model**
```
translations (SQLite)
├── id: auto-increment primary key
├── input_text: original Japanese text
├── output_html: <ruby> tag HTML for display
├── processed_data: JSON array of token objects
├── chinese_translation: optional Chinese translation
├── created_at, updated_at: timestamps

favorites (linked to translations via translation_id)
├── translation_id: FK to translations(id)
├── notes: user notes
├── tags: comma-separated tags
```

### 5. **Global Initialization at Startup**
App initializes expensive resources once on startup (app.py `@app.on_event("startup")`):
- PyKakasi instance (`initialize_kakasi()`)
- Translator instance (`initialize_translator()`)
- Database schema validation

## Key Conventions & Patterns

### Code Style
- All Chinese docstrings and comments (see `app.py`, `processors/furigana.py`)
- Detailed logging with emoji prefixes (✓, ❌, 🚀, etc.) for visibility
- Error messages in Chinese with user-friendly details

### Database Operations
- All CRUD operations go through `processors/storage.py` (single source of truth)
- `DB_PATH` calculated relative to module location: `Path(__file__).parent.parent / "db" / "translations.db"`
- Use `sqlite3.Row` for dictionary-like row access
- Auto-migration support: `ensure_translation_column()` adds missing columns safely

### API Endpoints Structure
- **Form endpoints** (`/convert`): Use `Form()` for text input, `UploadFile` for files
- **JSON API endpoints** (`/api/*`): Return `{"success": bool, ...}` with appropriate status codes
- **Page endpoints** (`/`, `/history`, etc.): Return `TemplateResponse` with context dict
- **Error handling**: Wrap in try/except with detailed logging; raise `HTTPException` for HTTP errors

### File Upload Handling
- Auto-detect file type by extension (.txt, .pdf, .jpg, .png, etc.)
- Try multiple encodings for text files: UTF-8 → Shift-JIS → GBK
- Image files → OCR extraction
- File size limit: 5MB; text length limit: 100,000 characters

### Token Data Structure
```python
@dataclass
class Token:
    original: str        # Original Japanese
    hiragana: str       # Hiragana reading
    romanji: str        # Romanized form
    token_type: str     # 'HIRAGANA', 'KANJI', 'KATAKANA', 'SYMBOL', 'OTHER'
```

### HTML Generation
- Ruby tags for furigana: `<ruby>漢<rt>かん</rt>字<rt>じ</rt></ruby>`
- Romanization below text: `<span class="romanji-below">kan</span>`
- Custom CSS in base template for sizing ruby text (smaller font for readings)

### Async/Await
- File upload processing is async (`await file.read()`)
- Image OCR is async (`await extract_text_from_image()`)
- Forms use `Form()` for backward compatibility (not JSON)

### Production Deployment
- PM2 configuration in `ecosystem.config.js` (fork mode, 500MB max memory)
- Logs: `logs/error.log`, `logs/out.log`
- Startup command: `run.sh` (activates venv, then runs uvicorn)
- Port: 8888 (configured in `run.sh`)

## Important Implementation Details

### PyKakasi Initialization
- Expensive initialization done once at startup, cached in `_kakasi_instance` global
- Fallback graceful: app continues if PyKakasi fails, but conversion won't work
- All requests use `get_kakasi_instance()` to access shared instance

### Translation Module
- Global `_translator` instance initialized at startup
- If initialization fails, translation feature is disabled but app continues
- Non-blocking: translation errors don't crash the convert endpoint

### Database Connections
- Connection pool via `check_same_thread=False` for async handling
- Row factory set to return dicts: `conn.row_factory = sqlite3.Row`
- Auto-commit for data modifications

### Encoding Handling
- Multi-step fallback for uploaded files: UTF-8 → UTF-8-sig → Shift-JIS → GBK
- Filename encoding: attempts UTF-8 decode with latin-1 fallback
- JSON responses use `charset=utf-8` explicitly for Chinese characters

## Testing
- End-to-end tests in `tests/test_e2e.py` - requires running app to test complete workflow
- Unit tests for specific modules (OCR, translation) exist but may need environment setup
- Manual testing: Use Postman/curl for API endpoints or browser for pages

## Common Task Patterns

**Adding a new API endpoint:**
1. Create handler function in `app.py` with route decorator
2. Add form parameters via `Form()` or JSON via `await request.json()`
3. Process via existing processor modules
4. Return `JSONResponse` with proper status codes or `TemplateResponse` for pages
5. Add comprehensive logging with emoji prefix

**Modifying database schema:**
1. Update `db/init_db.py` CREATE TABLE statement
2. Add migration function (like `ensure_translation_column()`) to `storage.py`
3. Call migration function at app startup or when needed

**Adding a processor module:**
1. Create in `processors/` directory
2. Initialize global instance at app startup if expensive operation
3. Expose functions in `app.py` or via existing processor modules
4. Add error handling with logging

## Troubleshooting

- **PyKakasi fails**: Run `pip install --upgrade pykakasi` or reinstall from source
- **Database locked**: Likely due to multiple connections; use `check_same_thread=False`
- **OCR not working**: Ensure PaddleOCR dependencies are installed (`paddleocr`, `paddlepaddle`)
- **Translation fails**: Non-blocking by design; check logs for translation library issues
- **Port already in use**: Modify port in `run.sh` or `app.py`

## Files You'll Likely Modify

- `app.py` - Main application, routes, business logic
- `processors/furigana.py` - Japanese text processing logic
- `processors/storage.py` - Database operations
- `templates/index.html`, `results.html` - Frontend pages
- `db/init_db.py` - Database schema

## Architecture Diagram (Simplified)

```
User Request → FastAPI Route (app.py)
    ↓
Input Validation (size, encoding)
    ↓
Branch:
  [Text] → PyKakasi (furigana.py) → Token objects
  [File] → Encoding detection → Text
  [Image] → PaddleOCR (ocr.py) → Text
    ↓
Romanization (romanization.py)
    ↓
HTML Generation + Optional Translation
    ↓
SQLite Storage (storage.py)
    ↓
Redirect to Results Page → Jinja2 Template → HTML Response
```
