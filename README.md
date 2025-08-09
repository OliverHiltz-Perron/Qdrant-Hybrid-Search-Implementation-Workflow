# FFPSA Data Extraction System

A Python-based system for extracting structured data from state child welfare prevention plans under the Family First Prevention Services Act (FFPSA). The system converts PDF documents to markdown format and extracts key information across 10 predefined categories using AI-powered analysis.

## Overview

This system processes state prevention plans to extract:
- Programs waiting to be added (pending clearinghouse approval)
- Target populations served
- Eligibility determination methods
- Effectiveness outcomes and metrics
- Monitoring and accountability systems
- Workforce support and credentialing
- Funding sources
- Trauma-informed service delivery
- Equity and disparity reduction efforts
- Structural determinants addressed

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key (for GPT-4 access)
- LlamaParse API key (for PDF conversion)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd FFPSA
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
LLAMA_CLOUD_API_KEY=your_llamaparse_api_key_here
```

## Usage

### 1. Convert PDFs to Markdown

First, convert your state plan PDFs to markdown format:

```bash
# Convert all PDFs in the default directory
python batch_convert_state_plans.py

# Convert with custom directories
python batch_convert_state_plans.py -i "path/to/pdfs" -o "path/to/markdown"

# Convert a single PDF
python llamaparse_converter.py -i document.pdf -o output_folder/
```

### 2. Extract Data from Markdown Files

#### Extract from a single document:
```bash
python main.py extract-single State_Plans_Markdown/AR_PreventionPlan.md
```

#### Extract from all documents in a directory:
```bash
python main.py extract-batch -i State_Plans_Markdown -o data/output/extracted
```

#### Extract with a different model (optional):
```bash
python main.py extract-single document.md --model claude-3-opus-20240229
```

### 3. Analyze Results

Generate analysis reports from extracted data:
```bash
python main.py analyze -o data/output/extracted
```

### 4. Convert to CSV/Reports

Convert JSON extraction results to readable formats:
```bash
# Convert the combined results to CSV
python convert_results.py data/output/extracted/all_states_extracted.json

# Convert with custom output directory
python convert_results.py results.json --output-dir custom_reports
```

### 5. Convert to Excel with Multiple Sheets

Create an Excel file with 10 sheets (one per category) plus a summary:
```bash
# Convert single state result
python json_to_excel.py data/output/extracted/CO_extraction.json -o CO_results.xlsx

# Convert all states combined
python json_to_excel.py data/output/extracted/all_states_extracted.json -o all_states_results.xlsx
```

## Output Files

The system generates several output files:

1. **Individual State Extractions**: `data/output/extracted/{STATE}_extraction.json`
   - Complete extraction results for each state
   - Includes all categories with supporting quotes
   - Metadata and confidence scores

2. **Combined Results**: `data/output/extracted/all_states_extracted.json`
   - All state results in a single file
   - Summary statistics

3. **CSV Reports**: `data/output/reports/`
   - `extraction_results_detailed.csv` - All extracted data
   - `extraction_results_summary.csv` - Key metrics only
   - `extraction_results.txt` - Human-readable summary

4. **Excel Reports**: Custom named `.xlsx` files
   - Summary sheet with overview of all states
   - 10 category sheets with detailed extractions:
     - Programs Waiting to Add
     - Target Populations
     - Eligibility Determination
     - Effectiveness Outcomes
     - Monitoring & Accountability
     - Workforce Support
     - Funding Sources
     - Trauma-Informed Delivery
     - Equity & Disparity Reduction
     - Structural Determinants

5. **Quality Reports**: `data/output/extracted/{STATE}_quality_report.json`
   - Validation results
   - Completeness scores
   - Recommendations for improvement

## Data Categories Extracted

1. **Programs Waiting to Add**: Programs pending clearinghouse evaluation
2. **Target Populations**: Groups explicitly described as recipients
3. **Eligibility Determination**: How eligibility is determined, including screening tools
4. **Effectiveness Outcomes**: System-level outcome goals (not program-specific)
5. **Monitoring & Accountability**: CQI systems, fidelity checks, oversight
6. **Workforce Support**: Training plans and credentialing requirements
7. **Funding Sources**: All funding streams (federal, state, local, private)
8. **Trauma-Informed Delivery**: Whether trauma-informed approaches are used
9. **Equity/Disparity Reduction**: How equity is addressed
10. **Structural Determinants**: Support for housing, childcare, employment, etc.

## Examples

### Full Workflow Example
```bash
# 1. Convert PDFs
python batch_convert_state_plans.py

# 2. Extract data from all converted files
python main.py extract-batch -i State_Plans_Markdown -o data/output/extracted

# 3. Generate analysis
python main.py analyze -o data/output/extracted

# 4. Create CSV reports
python convert_results.py data/output/extracted/all_states_extracted.json
```

### Single State Example
```bash
# Convert one state's PDF
python llamaparse_converter.py -i "State Plans for Analysis/CA_PreventionPlan.pdf" -o State_Plans_Markdown/

# Extract data
python main.py extract-single State_Plans_Markdown/CA_PreventionPlan.md

# View results
cat data/output/extracted/CA_extraction.json | python -m json.tool
```

## Configuration

Edit `config/extraction_config.json` to customize:
- Model settings (GPT-4 vs Claude)
- Token limits
- Chunk sizes
- Extraction parameters

Default configuration uses:
- Model: `gpt-4o-mini` (cost-effective)
- Chunk size: 3000 tokens
- Chunk overlap: 200 tokens
- Temperature: 0 (deterministic)

## Cost Estimates

Using default settings (gpt-4o-mini):
- PDF to Markdown conversion: ~$0.10-0.20 per document
- Data extraction: ~$0.50-1.00 per document
- Total: ~$0.60-1.20 per state plan

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Ensure `.env` file exists with valid API keys
   - Check environment variable names match exactly

2. **"File not found" errors**
   - Use absolute paths or ensure you're in the FFPSA directory
   - Check file extensions (.md for markdown files)

3. **JSON parsing errors during extraction**
   - Usually indicates API response issues
   - Check logs for details
   - May need to retry extraction

4. **Low quality scores**
   - Review the document to ensure it contains expected information
   - Check if PDF conversion was successful
   - Consider adjusting chunk size in config

### Logs

Extraction logs are saved with timestamps:
- `extraction_YYYYMMDD_HHMMSS.log`
- Contains detailed debugging information

## Project Structure

```
FFPSA/
├── State Plans for Analysis/     # Input PDFs
├── State_Plans_Markdown/         # Converted markdown files
├── src/                          # Source code
│   ├── document_processor.py     # Document chunking
│   ├── extraction_engine.py      # Main extraction logic
│   ├── prompts.py               # Category-specific prompts
│   ├── validators.py            # Data validation
│   └── utils.py                 # Utility functions
├── data/output/                 # Extraction results
│   ├── extracted/               # JSON results
│   └── reports/                 # CSV and text reports
├── config/
│   └── extraction_config.json   # System configuration
├── main.py                      # Main entry point
├── batch_convert_state_plans.py # Batch PDF converter
├── llamaparse_converter.py      # PDF to markdown converter
├── convert_results.py           # Results formatter
└── requirements.txt             # Python dependencies
```

## Contributing

When modifying the extraction system:
1. Test changes on a single document first
2. Ensure all 10 categories are properly extracted
3. Verify quotes are included for data validation
4. Run the full pipeline to ensure compatibility

## License

[Your license information here]