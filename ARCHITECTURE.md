# PaperIQ - Architecture Overview

## 🎯 Project Goal

PaperIQ is a **Research Paper Insight Analyzer** that automatically extracts and analyzes content from academic PDF papers.

**Milestone 1 Focus:** PDF Upload & Parsing

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Upload    │    │   Results   │    │  Validation │         │
│  │    Page     │───▶│    Page     │───▶│   Report    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PROCESSING PIPELINE                          │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │   PDF    │──▶│  Section │──▶│  Image   │──▶│  Table   │     │
│  │Extractor │   │ Detector │   │ Handler  │   │ Handler  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA STORAGE                                │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   SQLite Database   │    │    File System      │            │
│  │   (metadata)        │    │   (PDFs, images,    │            │
│  │                     │    │    CSV tables)      │            │
│  └─────────────────────┘    └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
paperiq/
├── app/                    # UI Layer (Streamlit)
│   ├── main.py            # Dashboard home page
│   └── pages/
│       ├── 1_📤_Upload.py  # Upload & process PDFs
│       └── 2_📊_Results.py # View extracted content
│
├── src/                    # Core Logic
│   ├── parsers/           # PDF Processing
│   │   ├── pdf_extractor.py    # Text extraction (PyMuPDF)
│   │   ├── section_detector.py # Section identification
│   │   ├── image_handler.py    # Image extraction
│   │   ├── table_handler.py    # Table extraction (Camelot)
│   │   └── text_cleaner.py     # Text preprocessing
│   │
│   ├── storage/           # Data Persistence
│   │   ├── db_handler.py       # SQLite operations
│   │   └── file_manager.py     # File system operations
│   │
│   ├── models/            # Data Structures
│   │   └── paper_model.py      # Paper, Section, Image, Table
│   │
│   └── utils/             # Utilities
│       ├── config.py           # Configuration
│       ├── validators.py       # PDF validation
│       └── logger_config.py    # Logging
│
└── data/                  # Runtime Data
    ├── uploads/           # Uploaded PDFs
    ├── extracted/
    │   ├── images/        # Extracted images
    │   └── tables/        # Extracted tables (CSV)
    └── paperiq.db         # SQLite database
```

---

## 🔄 Processing Pipeline

```
1. UPLOAD          2. EXTRACT         3. DETECT          4. STORE
   │                  │                  │                  │
   ▼                  ▼                  ▼                  ▼
┌──────┐          ┌──────┐          ┌──────┐          ┌──────┐
│ PDF  │─────────▶│ Text │─────────▶│Sections─────────▶│SQLite│
│Upload│          │Images│          │  with │          │ Files│
│      │          │Tables│          │Scores │          │      │
└──────┘          └──────┘          └──────┘          └──────┘
```

### Step-by-Step:

| Step | Action | Tool Used |
|------|--------|-----------|
| 1 | Validate PDF | Custom validator |
| 2 | Extract text with layout | PyMuPDF |
| 3 | Extract images | PyMuPDF + Pillow |
| 4 | Extract tables | Camelot-py |
| 5 | Detect sections | Pattern matching + Layout analysis |
| 6 | Calculate confidence | Combined scoring |
| 7 | Save to database | SQLite |
| 8 | Generate report | Validation checks |

---

## 🧠 Section Detection Logic

**Two-Phase Approach:**

### Phase 1: Pattern Matching
- Search for keywords: "ABSTRACT", "INTRODUCTION", "METHODOLOGY", etc.
- Handle variations: "Methods", "Materials and Methods", "Experimental Setup"
- Base confidence: **0.7**

### Phase 2: Layout Analysis
- Check font size (headers are larger)
- Check bold formatting
- Check positioning
- Additional confidence: **+0.15 to +0.25**

### Confidence Scoring:
| Level | Score | Meaning |
|-------|-------|---------|
| 🟢 High | ≥80% | Pattern + font + bold |
| 🟡 Medium | 60-80% | Pattern + one layout feature |
| 🔴 Low | <60% | Weak signals |

---

## 💾 Data Models

### Paper
```python
- id, filename, title
- page_count, file_size
- status (uploaded/processing/completed/failed)
- sections[], images[], tables[]
```

### Section
```python
- section_type (abstract/introduction/methodology/...)
- content (full text)
- confidence (0.0 to 1.0)
- word_count
```

### ExtractedImage / ExtractedTable
```python
- file_path (saved location)
- page_number
- dimensions (width, height)
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI | Streamlit | Web dashboard |
| PDF Parsing | PyMuPDF | Text & image extraction |
| Table Extraction | Camelot-py | Table detection |
| Image Processing | Pillow | Image handling |
| Database | SQLite | Data persistence |
| Data Processing | Pandas | Table manipulation |

---

## ✅ Key Features (Milestone 1)

- [x] PDF upload through web interface
- [x] Text extraction with layout info
- [x] Automatic section identification (7 types)
- [x] Confidence scoring for each section
- [x] Image extraction with metadata
- [x] Table extraction to CSV
- [x] Persistent storage (SQLite)
- [x] Validation report generation
- [x] Clean, responsive UI

---

## 🚀 How to Run

```bash
# 1. Navigate to project
cd /path/to/PaperIQ

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
streamlit run app/main.py
```

App opens at: **http://localhost:8501**

---

## 📊 Demo Flow

1. **Upload** → Drag & drop a research paper PDF
2. **Process** → Click "Parse Paper", watch progress bar
3. **View Sections** → See Abstract, Introduction, Methods, etc.
4. **Check Images** → Browse extracted figures
5. **Download Tables** → Get tables as CSV files
6. **Validate** → Review quality score and checklist

---

## 🔮 Future Milestones

| Milestone | Focus |
|-----------|-------|
| M2 | NLP analysis (summarization, keywords) |
| M3 | Multi-paper comparison |
| M4 | AI-powered insights |

---

*Built with Python 🐍 | Pure local processing | No external servers*
