# PaperIQ - Research Paper Insight Analyzer

**Milestone 1: Paper Upload & Parsing**

PaperIQ is a pure Python application that extracts and analyzes research papers. Upload a PDF and get automatic section identification, image extraction, and table detection with confidence scoring.

## 🚀 Features

- **📤 PDF Upload** - Upload research papers through a web interface
- **📝 Section Detection** - Automatically identify:
  - Abstract
  - Introduction
  - Methodology/Methods
  - Results/Experiments
  - Discussion
  - Conclusion
  - References
- **🖼️ Image Extraction** - Extract all figures and diagrams with metadata
- **📊 Table Extraction** - Extract tables and convert to CSV format
- **✅ Quality Validation** - Confidence scores and validation reports
- **💾 Persistent Storage** - SQLite database for data persistence

## 📋 Requirements

- Python 3.9+
- pip

## 🛠️ Installation

1. **Clone or navigate to the project:**
   ```bash
   cd /path/to/PaperIQ
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment configuration (optional):**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

## 🏃 Running the Application

Start the Streamlit app:

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
paperiq/
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── .gitignore
├── README.md
│
├── src/                     # Source code
│   ├── __init__.py
│   ├── parsers/             # PDF parsing logic
│   │   ├── pdf_extractor.py    # Text extraction with PyMuPDF
│   │   ├── section_detector.py # Section identification
│   │   ├── table_handler.py    # Table extraction with Camelot
│   │   ├── image_handler.py    # Image extraction
│   │   └── text_cleaner.py     # Text preprocessing
│   │
│   ├── storage/             # Data persistence
│   │   ├── db_handler.py       # SQLite operations
│   │   └── file_manager.py     # File system operations
│   │
│   ├── utils/               # Helper functions
│   │   ├── validators.py       # PDF and content validation
│   │   ├── logger_config.py    # Logging setup
│   │   └── config.py           # App configuration
│   │
│   └── models/              # Data structures
│       └── paper_model.py      # Paper data classes
│
├── app/                     # Streamlit UI
│   ├── main.py             # Main application entry
│   ├── pages/
│   │   ├── 1_📤_Upload.py     # Upload and parse page
│   │   └── 2_📊_Results.py    # View results page
│   │
│   └── components/          # Reusable UI components
│       ├── upload_widget.py
│       ├── section_viewer.py
│       ├── image_gallery.py
│       └── validation_report.py
│
├── data/                    # Data directory (auto-created)
│   ├── uploads/            # Uploaded PDF files
│   ├── extracted/
│   │   ├── images/         # Extracted images
│   │   └── tables/         # Extracted tables as CSV
│   └── paperiq.db          # SQLite database
│
└── tests/
    └── sample_papers/      # Test PDFs for validation
```

## 🔧 Configuration

Configuration options in `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_PDF_SIZE_MB` | 50 | Maximum file size in MB |
| `ENABLE_OCR` | False | Enable OCR (future feature) |
| `MIN_SECTION_LENGTH` | 50 | Minimum section length in chars |
| `HIGH_CONFIDENCE_THRESHOLD` | 0.8 | High confidence score threshold |
| `MEDIUM_CONFIDENCE_THRESHOLD` | 0.6 | Medium confidence threshold |

## 📊 How It Works

### Processing Pipeline

1. **Upload** - Validate and save PDF file
2. **Text Extraction** - Extract text with layout info using PyMuPDF
3. **Image Extraction** - Extract embedded images
4. **Table Extraction** - Detect and extract tables using Camelot
5. **Section Detection** - Identify sections using pattern matching + layout analysis
6. **Validation** - Generate confidence scores and quality report
7. **Storage** - Save results to SQLite database

### Section Detection

Uses a two-phase approach:

1. **Pattern Matching** - Regex patterns for common section headers
2. **Layout Analysis** - Font size and bold formatting detection

Combined confidence scoring:
- **High (≥80%)**: Pattern match + large font + bold
- **Medium (60-80%)**: Pattern match + layout feature
- **Low (<60%)**: Weak signals

## 🎨 UI Features

- **Dashboard** - Overview with quick stats
- **Upload Page** - Drag & drop PDF upload with progress tracking
- **Results Page** - Tabbed view of sections, images, tables, and validation
- **Confidence Badges** - Color-coded confidence indicators
- **Export** - Download extracted tables as CSV

## ⚠️ Known Limitations

- OCR not yet supported (digital PDFs only)
- Some complex table layouts may not extract correctly
- Multi-language support is limited

## 🧪 Testing

Place test PDFs in `tests/sample_papers/` directory.

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

This is a Milestone 1 implementation. Future milestones will add:
- Milestone 2: NLP analysis (summarization, keywords)
- Milestone 3: Multi-paper comparison
- Milestone 4: AI-powered insights
