# BKV Matrix Normalizer

A Python-based data processing tool that converts Excel (.xlsx) and CSV files into structured JSON/JSONL format with advanced parsing capabilities and downloadable output.

## 🚀 Overview

BKV Matrix Normalizer is designed to streamline the process of converting tabular data from Excel spreadsheets and CSV files into structured JSON or JSON Lines (JSONL) format. The tool provides intelligent data parsing, normalization, and export capabilities with a user-friendly interface.

## 🛠 Technologies & Libraries

### Core Technologies

- **Python 3.8+** - Primary programming language
- **FastAPI** - Modern, fast web framework for building APIs with Python 3.6+ based on standard Python type hints
- **HTML/CSS/JavaScript** - Frontend interface

### Key Libraries

#### Data Processing

- **pandas** - Data manipulation and analysis
- **openpyxl** - Excel file reading and writing
- **xlrd** - Legacy Excel file support
- **csv** - Built-in CSV processing

#### File Handling & Validation

- **pathlib** - Modern path handling
- **mimetypes** - File type validation
- **python-multipart** - File upload handling for FastAPI
- **aiofiles** - Async file operations

#### JSON Processing

- **json** - Built-in JSON handling
- **jsonlines** - JSONL format support

#### Web Framework & UI

- **FastAPI** - Modern, fast web framework with automatic API documentation
- **Uvicorn** - Lightning-fast ASGI server implementation
- **Pydantic** - Data validation and settings management using Python type annotations
- **Jinja2** - Template engine for HTML rendering

#### Development & Testing

- **pytest** - Testing framework
- **pytest-asyncio** - Async testing support
- **httpx** - Async HTTP client for testing FastAPI
- **black** - Code formatting
- **flake8** - Code linting
- **pre-commit** - Git hooks for code quality

## 📋 Features

- ✅ **Multi-format Support**: Process both .xlsx and .csv files
- ✅ **Intelligent Parsing**: Automatic data type detection and conversion
- ✅ **Flexible Output**: Generate JSON or JSONL format
- ✅ **Data Validation**: Input validation and error handling
- ✅ **Web Interface**: User-friendly upload and download interface
- ✅ **Batch Processing**: Handle multiple files simultaneously
- ✅ **Custom Mapping**: Configure column mappings and transformations
- ✅ **Preview Mode**: Preview data before conversion
- ✅ **Download Management**: Secure file download with cleanup

## 🏗 Project Structure

```
bkv-matrix-normalizer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py    # File upload endpoints
│   │   │   ├── convert.py   # Data conversion endpoints
│   │   │   └── download.py  # File download endpoints
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Pydantic settings configuration
│   │   └── exceptions.py    # Custom exception handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py       # Pydantic models for request/response
│   │   └── enums.py         # Enumerations and constants
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── excel_processor.py    # Excel file processing
│   │   ├── csv_processor.py      # CSV file processing
│   │   └── json_generator.py     # JSON/JSONL generation
│   ├── validators/
│   │   ├── __init__.py
│   │   └── file_validator.py     # File validation logic
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py            # Utility functions
│       └── logger.py             # Logging configuration
├── templates/
│   ├── base.html
│   ├── upload.html
│   ├── convert.html
│   └── download.html
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── app.js
│   └── uploads/                  # Temporary file storage
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── test_api/
│   │   ├── __init__.py
│   │   ├── test_upload.py
│   │   ├── test_convert.py
│   │   └── test_download.py
│   ├── test_processors/
│   │   ├── __init__.py
│   │   ├── test_excel_processor.py
│   │   ├── test_csv_processor.py
│   │   └── test_json_generator.py
│   ├── test_validators/
│   │   ├── __init__.py
│   │   └── test_file_validator.py
│   └── fixtures/                 # Test data files
│       ├── sample.xlsx
│       └── sample.csv
├── requirements.txt
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Project configuration
├── .env.example                # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml          # Docker setup
├── Dockerfile
└── README.md
```

## 🔄 Execution Flow

### 1. File Upload & Validation

```
User uploads file → File type validation → Size check → Temporary storage
```

### 2. Data Processing Pipeline

```
File parsing → Data normalization → Type conversion → Structure validation
```

### 3. JSON Generation

```
Processed data → JSON/JSONL formatting → Output file generation → Download preparation
```

### 4. Download & Cleanup

```
File download → Temporary file cleanup → Success notification
```

## 📦 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/Nouman64-cat/bkv-matrix-normalizer.git
cd bkv-matrix-normalizer
```

2. **Create virtual environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Environment configuration**

```bash
# Copy environment template
copy .env.example .env

# Edit .env file with your settings
# ENVIRONMENT=development
# MAX_FILE_SIZE=10485760
# UPLOAD_FOLDER=static/uploads
# API_V1_STR=/api/v1
# PROJECT_NAME=BKV Matrix Normalizer
```

5. **Run the application**

```bash
# Development server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using the run script
python -m app.main
```

## 🎯 Usage

### Web Interface

1. Navigate to `http://localhost:8000`
2. Upload your Excel (.xlsx) or CSV file
3. Configure output format (JSON/JSONL)
4. Set any custom mappings or transformations
5. Process and download the converted file

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Endpoints

```python
# File Operations
POST /api/v1/files/upload           # Upload file for processing
GET  /api/v1/files/{file_id}        # Get file information
DELETE /api/v1/files/{file_id}      # Delete uploaded file

# Data Processing
GET  /api/v1/process/preview/{file_id}     # Preview processed data
POST /api/v1/process/convert/{file_id}     # Convert to JSON/JSONL
GET  /api/v1/process/status/{job_id}       # Check conversion status

# Download
GET  /api/v1/download/{file_id}     # Download converted file
POST /api/v1/download/batch         # Batch download multiple files

# Health Check
GET  /api/v1/health                 # Application health status
```

## ⚙️ Configuration

### FastAPI Configuration

```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BKV Matrix Normalizer"
    API_V1_STR: str = "/api/v1"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {'.xlsx', '.csv'}
    OUTPUT_FORMATS: list = ['json', 'jsonl']
    UPLOAD_FOLDER: str = "static/uploads"
    TEMP_FILE_RETENTION: int = 3600  # 1 hour
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
```

### Data Processing Options

- **Column mapping**: Map source columns to target JSON keys
- **Data type conversion**: Automatic or manual type specification
- **Null value handling**: Configure how empty cells are processed
- **Array handling**: Process multi-value cells as arrays

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/ --cov-report=html

# Run specific test file
pytest tests/test_api/test_upload.py -v

# Run async tests
pytest tests/test_api/ -v --asyncio-mode=auto

# Run tests with detailed output
pytest -s -v tests/
```

## 🔒 Security Considerations

- **File validation**: Strict file type and size validation
- **Input sanitization**: Clean and validate all user inputs
- **Temporary file management**: Automatic cleanup of uploaded files
- **Path traversal protection**: Secure file handling
- **CSRF protection**: Cross-site request forgery prevention

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Maintain 90%+ test coverage
- Document all public functions

### Git Workflow

1. Create feature branch from `main`
2. Make changes with descriptive commits
3. Run tests and linting
4. Submit pull request

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**File Upload Fails**

- Check file size (max 10MB)
- Verify file format (.xlsx or .csv)
- Ensure proper file permissions

**Conversion Errors**

- Validate Excel file isn't corrupted
- Check for special characters in column names
- Verify CSV delimiter settings

**Memory Issues**

- Large files may require increased memory limits
- Consider processing in chunks for very large datasets

## 📞 Support

For support and questions:

- Create an issue on GitHub
- Email: support@bkv-matrix-normalizer.com
- Documentation: [Wiki](https://github.com/Nouman64-cat/bkv-matrix-normalizer/wiki)

## 🗺 Roadmap

- [ ] Support for additional file formats (ODS, TSV)
- [ ] Advanced data transformation rules
- [ ] API rate limiting and authentication
- [ ] Docker containerization
- [ ] Cloud deployment templates
- [ ] Real-time processing status updates
