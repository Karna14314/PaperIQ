# PaperIQ - Research Paper Insight Analyzer

**Milestone 1: Paper Upload and Parsing**

PaperIQ is a pure Python application that extracts and analyzes research papers. Upload a PDF and get automatic section identification, image extraction, and table detection with confidence scoring.

## Features

- **PDF Upload** - Upload research papers through a web interface
- **Section Detection** - Automatically identify Abstract, Introduction, Methodology, Results, Discussion, Conclusion, and References
- **Image Extraction** - Extract all figures and diagrams with metadata
- **Table Extraction** - Extract tables and convert to CSV format
- **Quality Validation** - Confidence scores and validation reports
- **Persistent Storage** - SQLite database for data persistence

## Requirements

- Python 3.9+
- pip

## Installation

1. Clone or navigate to the project:
   ```bash
   cd /path/to/PaperIQ
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration (optional):
   ```bash
   cp .env.example .env
   ```

## Running the Application

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

## Project Structure

```
paperiq/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md
│
├── src/
│   ├── parsers/
│   │   ├── pdf_extractor.py
│   │   ├── section_detector.py
│   │   ├── table_handler.py
│   │   ├── image_handler.py
│   │   └── text_cleaner.py
│   │
│   ├── storage/
│   │   ├── db_handler.py
│   │   └── file_manager.py
│   │
│   ├── utils/
│   │   ├── validators.py
│   │   ├── logger_config.py
│   │   └── config.py
│   │
│   └── models/
│       └── paper_model.py
│
├── app/
│   ├── main.py
│   ├── pages/
│   │   ├── 1_Upload.py
│   │   └── 2_Results.py
│   └── components/
│
├── data/
│   ├── uploads/
│   ├── extracted/
│   │   ├── images/
│   │   └── tables/
│   └── paperiq.db
│
└── tests/
    └── sample_papers/
```

## Configuration

Configuration options in `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_PDF_SIZE_MB` | 50 | Maximum file size in MB |
| `ENABLE_OCR` | False | Enable OCR (future feature) |
| `MIN_SECTION_LENGTH` | 50 | Minimum section length in chars |
| `HIGH_CONFIDENCE_THRESHOLD` | 0.8 | High confidence threshold |
| `MEDIUM_CONFIDENCE_THRESHOLD` | 0.6 | Medium confidence threshold |

## Processing Pipeline

1. **Upload** - Validate and save PDF file
2. **Text Extraction** - Extract text with layout info using PyMuPDF
3. **Image Extraction** - Extract embedded images
4. **Table Extraction** - Detect and extract tables using Camelot
5. **Section Detection** - Identify sections using pattern matching and layout analysis
6. **Validation** - Generate confidence scores and quality report
7. **Storage** - Save results to SQLite database

## Technology Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| PDF Parsing | PyMuPDF |
| Table Extraction | Camelot-py |
| Image Processing | Pillow |
| Database | SQLite |
| Data Processing | Pandas |

## Known Limitations

- OCR not yet supported (digital PDFs only)
- Some complex table layouts may not extract correctly
- Multi-language support is limited

## License

This project is for educational purposes.
