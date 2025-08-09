# FFPSA Data Extraction System

This system extracts structured data from Family First Prevention Services Act (FFPSA) state prevention plans using AI-powered analysis.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API credentials:
```bash
# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
# Or for Anthropic Claude:
# echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

3. Configure the system (optional):
Edit `config/extraction_config.json` to change:
- Model provider (openai/anthropic)
- Model name
- Chunk sizes
- Extraction categories

## Usage

### Extract from a single document:
```bash
python main.py extract-single State_Plans_Markdown/AR_Prevention_Plan.md
```

### Extract from all documents:
```bash
python main.py extract-batch -i State_Plans_Markdown -o data/output/extracted
```

### Analyze results:
```bash
python main.py analyze -o data/output/extracted
```

## Extraction Categories

The system extracts 10 categories of information:

1. **Programs Waiting to Add** - Prevention programs pending approval
2. **Target Populations** - Populations served by prevention services
3. **Eligibility Determination** - How eligibility is determined
4. **Effectiveness Outcomes** - How effectiveness is measured
5. **Monitoring & Accountability** - Oversight and quality assurance
6. **Workforce Support** - Training and professional development
7. **Funding Sources** - Federal, state, and local funding
8. **Trauma-Informed Delivery** - Use of trauma-informed approaches
9. **Equity & Disparity Reduction** - Efforts to address disparities
10. **Structural Determinants** - Addressing poverty, housing, etc.

## How the System Works

### Overview
The extraction system processes each document through a series of API calls to extract structured data across 10 categories. Understanding this process is crucial for troubleshooting and optimization.

### The Two-Phase Extraction Process

#### Phase 1: Full-Context Extraction
These categories receive the ENTIRE document in a single API call:
- `effectiveness_outcomes`
- `monitoring_accountability`
- `equity_disparity_reduction`
- `structural_determinants`

**Why full-context?** These categories require understanding relationships across the entire document.

#### Phase 2: Chunk-Based Extraction
These categories process the document in smaller chunks:
- `programs_waiting_to_add`
- `target_populations`
- `eligibility_determination`
- `workforce_support`
- `funding_sources`
- `trauma_informed_delivery`

**Why chunks?** These categories look for specific information that can be found in localized sections.

### Detailed Processing Flow

1. **Document Loading**
   ```
   Load markdown file → Count tokens → Extract metadata
   Example: AR_PreventionPlan.md = 31,444 tokens
   ```

2. **Full-Context Extraction (Phase 1)**
   ```
   For each full-context category:
     1. Create prompt with entire document
     2. Send to API: prompt + 31,444 tokens
     3. Wait for response (typically 1-2 minutes)
     4. Parse JSON response
     5. Validate extracted data
   
   Total: 4 API calls for Phase 1
   ```

3. **Document Chunking**
   ```
   Split document into chunks:
     - Target size: 3,000 tokens (configurable)
     - Overlap: 200 tokens
     - Result: ~149 chunks for a 31,444 token document
   ```

4. **Chunk-Based Extraction (Phase 2)**
   ```
   For each chunk-based category:
     1. Find relevant chunks (max 10) using keywords
     2. For each relevant chunk:
        - Create prompt with chunk content
        - Send to API
        - Parse response
     3. Merge results from all chunks
     4. Validate merged data
   
   Total: 6 categories × 10 chunks = 60 API calls for Phase 2
   ```

### Chunking Mechanism

#### How Chunks Are Created
1. **Smart Chunking**: Respects document structure (headings, paragraphs)
2. **Size Control**: Each chunk ≤ target_chunk_size tokens
3. **Overlap**: Previous chunk's end overlaps with next chunk's beginning

Example:
```
Document: [============================] 31,444 tokens
Chunks:   [Chunk1][Chunk2][Chunk3]...[Chunk149]
          └─overlap─┘└─overlap─┘
```

#### How Relevant Chunks Are Selected
Each category has keywords. For example, `funding_sources` looks for:
- "funding", "budget", "federal", "state", "braided", "finance", "resources"

Relevance scoring:
- 2+ keyword matches = highly relevant
- 1 keyword match + chunk < 5000 tokens = relevant
- Maximum 10 chunks per category

### API Call Sequence

For a typical document:
```
1. Start extraction: 11:02:58
2. Full-context calls (4 total):
   - effectiveness_outcomes: 11:04:06 (68 seconds)
   - monitoring_accountability: 11:05:04 (58 seconds)
   - equity_disparity_reduction: 11:05:56 (52 seconds)
   - structural_determinants: 11:06:48 (52 seconds)
3. Create chunks: 11:06:49
4. Chunk-based calls (60 total):
   - programs_waiting_to_add: 10 calls
   - target_populations: 10 calls
   - eligibility_determination: 10 calls
   - workforce_support: 10 calls
   - funding_sources: 10 calls
   - trauma_informed_delivery: 10 calls
5. Complete: ~11:10:00

Total time: ~7-8 minutes
Total API calls: 64
```

### Understanding Prompts

Each category has a specific prompt that tells the model:
1. What information to look for
2. How to structure the response (JSON format)
3. What fields are required vs optional

Example prompt structure:
```
System: You are an expert at extracting structured data...
User: [PROMPT TEMPLATE]
      
      Document:
      [DOCUMENT OR CHUNK CONTENT]
```

The prompts are processed **sequentially**, not in parallel:
- One category at a time
- Within each category, one chunk at a time
- This prevents rate limiting but increases total time

### Common Issues and Solutions

#### Empty Responses
- **Cause**: Model returns empty string instead of JSON
- **Impact**: "Expecting value: line 1 column 1 (char 0)" error
- **Solution**: Add retry logic or reduce chunk size

#### JSON Parse Errors
- **Cause**: Model returns malformed JSON (unterminated strings, etc.)
- **Impact**: Extraction fails for that chunk/category
- **Solution**: Validate JSON before parsing, add error handling

#### Long Processing Times
- **Cause**: Full-context categories with large documents
- **Impact**: 1-2 minutes per category
- **Solution**: Move categories to chunk-based processing

### Configuration Impact

#### Chunk Size (`target_chunk_size`)
- **Smaller chunks (1000-3000)**: More API calls, better reliability
- **Larger chunks (5000-10000)**: Fewer API calls, risk of errors
- **Recommended**: 3000 tokens

#### Overlap Size
- **Small overlap (100-200)**: Risk missing context between chunks
- **Large overlap (500+)**: Redundant processing
- **Recommended**: 200 tokens

#### Model Selection
- **gpt-4.1-mini**: Fast, cheap, good for most extractions
- **gpt-4**: More accurate but 10x more expensive
- **gpt-3.5-turbo**: Faster but less reliable for complex prompts

### Cost Breakdown

Per document with gpt-4.1-mini:
```
Full-context: 4 calls × 31,444 tokens = 125,776 tokens
Chunk-based: 60 calls × ~3,000 tokens = 180,000 tokens
Total: ~305,776 tokens ≈ $0.50-$1.00
```

## Output Files

For each state, the system creates:
- `{state}_extraction.json` - Extracted data
- `{state}_quality_report.json` - Validation and quality metrics

Batch processing also creates:
- `all_states_extracted.json` - Combined results
- `extraction_summary.json` - Summary statistics
- `detailed_analysis.csv` - Analysis spreadsheet

## Quality Assurance

Each extraction includes:
- Validation of required fields
- Completeness checking
- Confidence scoring (0-10)
- Recommendations for improvement

## Cost Estimates

Using GPT-4.1-mini (default):
- Approximately $0.50-1.00 per document
- Total for 50 states: ~$25-50

For comparison:
- GPT-4: $10-15 per document (~$500-750 total)
- GPT-3.5: $2-3 per document (~$100-150 total)

## Converting Results to CSV and Reports

After extraction, use the `convert_results.py` script to create CSV files and human-readable reports:

### Basic Usage
```bash
# Convert to all formats (detailed CSV, summary CSV, and text report)
python convert_results.py data/output/extracted/all_states_extracted.json

# Convert single state result
python convert_results.py data/output/extracted/AR_extraction.json
```

### Output Options
```bash
# Create summary CSV only (key metrics)
python convert_results.py all_states_extracted.json --summary

# Create detailed CSV only (all fields)
python convert_results.py all_states_extracted.json --detailed

# Create human-readable report only
python convert_results.py all_states_extracted.json --report

# Specify output directory
python convert_results.py all_states_extracted.json -o my_reports/
```

### Output Files

1. **extraction_summary.csv** - Key metrics in a compact format:
   - State information and confidence scores
   - Counts (programs, populations, funding sources)
   - Boolean indicators (trauma-informed, equity, etc.)
   - Easy to use for analysis and visualization

2. **extraction_detailed.csv** - Complete extraction data:
   - All fields from all categories
   - Flattened nested structures
   - Lists converted to semicolon-separated values
   - Comprehensive but may have many columns

3. **extraction_report.txt** - Human-readable summary:
   - Overall statistics and key findings
   - State-by-state summaries
   - Sample quotes from documents
   - Easy to read and share

### Example Summary CSV Columns
- state, document_date, pages, confidence_score
- programs_waiting_count, populations_count
- federal_funding_sources, state_funding_sources
- trauma_informed, addresses_equity, addresses_structural_determinants

## Troubleshooting

1. **API Key Error**: Ensure your API key is set in .env file
2. **Token Limit Error**: Reduce chunk_size in config
3. **JSON Parse Error**: Check API response format, may need prompt adjustment
4. **Missing Categories**: Some states may not address all categories

## Next Steps

After extraction:
1. Review quality reports for low-scoring states
2. Manually verify a sample of extractions
3. Use `python main.py analyze` to generate insights
4. Export to data/output/analysis_summary.csv for further analysis