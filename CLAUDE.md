# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FFPSA (Family First Prevention Services Act) is a Python-based data extraction and analysis system for state child welfare prevention plans. The project converts PDF documents to markdown format and extracts structured data across 10 categories using AI-powered analysis.

## Common Commands

### Environment Setup
```bash
# Required environment variables (add to .env file)
LLAMA_CLOUD_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here  # Or ANTHROPIC_API_KEY for Claude

# Install dependencies
pip install -r requirements.txt
```

### Document Conversion
```bash
# Convert all state PDFs to markdown (default directories)
python batch_convert_state_plans.py

# Convert with custom directories
python batch_convert_state_plans.py -i "State Plans for Analysis" -o "State_Plans_Markdown"

# Convert single file or directory
python llamaparse_converter.py -i document.pdf -o output_folder/
python llamaparse_converter.py -i pdf_directory/ -o markdown_output/

# Convert ZIP archive
python llamaparse_converter.py -i documents.zip -o markdown_output/
```

### Data Extraction
```bash
# Extract from single document
python main.py extract-single State_Plans_Markdown/AR_PreventionPlan.md

# Batch extract from all documents
python main.py extract-batch -i State_Plans_Markdown -o data/output/extracted

# Extract with different model
python main.py extract-single document.md --model claude-3-opus-20240229
```

### Analysis and Reporting
```bash
# Generate analysis reports
python main.py analyze -o data/output/extracted

# Convert JSON results to CSV and text reports
python convert_results.py data/output/extracted/all_states_extracted.json

# Generate custom report
python convert_results.py results.json --output-dir custom_reports
```

## Architecture

### Project Structure
```
FFPSA/
├── State Plans for Analysis/     # Input PDFs (42 states)
├── State_Plans_Markdown/         # Converted markdown files
├── src/                         # Core modules
│   ├── document_processor.py    # Document chunking and analysis
│   ├── extraction_engine.py     # Main extraction logic
│   ├── prompts.py              # Category-specific prompts
│   ├── validators.py           # Data validation
│   └── utils.py                # Utilities
├── data/output/                # Extraction results
│   ├── extracted/              # JSON files
│   └── reports/                # CSV and text reports
├── config/
│   └── extraction_config.json  # System configuration
└── tests/                      # Test directory (empty)
```

### Data Flow
1. **Input**: PDF state prevention plans in `State Plans for Analysis/`
2. **Conversion**: LlamaParse API converts PDFs to markdown
3. **Storage**: Markdown files saved to `State_Plans_Markdown/`
4. **Extraction**: Two-phase AI extraction (full-context + chunk-based)
5. **Output**: JSON results in `data/output/extracted/`
6. **Analysis**: CSV reports and summaries in `data/output/reports/`

### Extraction Strategy

The system uses a hybrid extraction approach:

**Full-Context Extraction** (4 categories):
- Programs Waiting to Add
- Monitoring & Accountability
- Funding Sources
- Structural Determinants

**Chunk-Based Extraction** (6 categories):
- Target Populations
- Eligibility Determination
- Effectiveness Outcomes
- Workforce Support
- Trauma-Informed Delivery
- Equity & Disparity Reduction

### Key Configuration

**Model Settings** (config/extraction_config.json):
- Default model: gpt-4o-mini
- Max tokens: 8000
- Temperature: 0
- Chunk size: 3000 tokens
- Chunk overlap: 200 tokens

**Processing Limits**:
- Max concurrent extractions: 3
- Retry attempts: 3
- Cost estimate: $0.50-1.00 per document

### Current State
- **Available**: 42 state PDFs for analysis
- **Converted**: 7 states to markdown (AR, AZ, CA, CO, CT, DC, FL)
- **Extracted**: 3 states with results (AR, AZ, CA)
- **Missing**: Automated tests and linting configuration

## Development Guidelines

### Adding New Extraction Categories
1. Add category to `config/extraction_config.json`
2. Create prompt in `src/prompts.py`
3. Add validation schema in `src/validators.py`
4. Update extraction logic if needed

### Modifying Extraction Logic
- Full-context logic: `src/extraction_engine.py::_extract_full_context()`
- Chunk-based logic: `src/extraction_engine.py::_extract_chunk_based()`
- Document processing: `src/document_processor.py`

### Error Handling
- All scripts include comprehensive logging
- Failed conversions logged but don't stop batch processing
- Extraction failures saved with error details
- Check logs for debugging information

### Cost Optimization
- Use gpt-4o-mini for routine extractions
- Consider chunk size vs accuracy tradeoffs
- Monitor token usage in extraction results