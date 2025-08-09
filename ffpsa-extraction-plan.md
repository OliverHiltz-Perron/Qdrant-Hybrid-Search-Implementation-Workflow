# FFPSA Data Extraction Plan and Implementation Guide

## Project Overview

This guide provides a complete implementation plan for extracting structured data from Family First Prevention Services Act (FFPSA) state prevention plans using a hybrid AI approach.

## Phase 1: Setup and Preparation

### 1.1 Project Structure

```python
ffpsa_extraction/
├── src/
│   ├── __init__.py
│   ├── document_processor.py
│   ├── extraction_engine.py
│   ├── prompts.py
│   ├── validators.py
│   └── utils.py
├── data/
│   ├── input/
│   │   └── state_plans/
│   ├── output/
│   │   ├── extracted/
│   │   └── validated/
│   └── schemas/
├── config/
│   └── extraction_config.json
├── tests/
├── requirements.txt
└── main.py
```

### 1.2 Dependencies Installation

```python
# requirements.txt
openai==1.12.0  # or anthropic==0.18.0 for Claude
tiktoken==0.5.2
pydantic==2.6.0
pandas==2.2.0
numpy==1.26.3
python-dotenv==1.0.0
tqdm==4.66.1
jsonschema==4.21.1
```

### 1.3 Configuration

```python
# config/extraction_config.json
{
    "model_config": {
        "provider": "openai",  # or "anthropic"
        "model_name": "gpt-4-turbo-preview",
        "temperature": 0.1,
        "max_tokens": 4000
    },
    "chunking_config": {
        "method": "smart",
        "target_chunk_size": 10000,
        "overlap": 500
    },
    "extraction_categories": {
        "full_context": [
            "effectiveness_outcomes",
            "monitoring_accountability",
            "equity_disparity_reduction",
            "structural_determinants"
        ],
        "chunk_based": [
            "programs_waiting_to_add",
            "target_populations",
            "eligibility_determination",
            "workforce_support",
            "funding_sources",
            "trauma_informed_delivery"
        ]
    }
}
```

## Phase 2: Core Implementation

### 2.1 Document Processor

```python
# src/document_processor.py
import re
from typing import List, Dict, Tuple
import tiktoken

class DocumentProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.encoding = tiktoken.encoding_for_model(config['model_config']['model_name'])
    
    def analyze_structure(self, markdown_text: str) -> Dict:
        """Analyze document structure to identify key sections."""
        structure = {
            'total_tokens': len(self.encoding.encode(markdown_text)),
            'sections': [],
            'table_of_contents': []
        }
        
        # Find major sections
        section_pattern = r'^#{1,3}\s+(.+)$'
        matches = list(re.finditer(section_pattern, markdown_text, re.MULTILINE))
        
        for i, match in enumerate(matches):
            section_start = match.start()
            section_end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
            
            section = {
                'title': match.group(1),
                'level': len(match.group(0).split()[0]),  # Number of #
                'start': section_start,
                'end': section_end,
                'content': markdown_text[section_start:section_end],
                'tokens': len(self.encoding.encode(markdown_text[section_start:section_end]))
            }
            
            # Classify section type based on title
            section['type'] = self._classify_section(section['title'])
            structure['sections'].append(section)
        
        return structure
    
    def _classify_section(self, title: str) -> str:
        """Classify section based on title keywords."""
        title_lower = title.lower()
        
        classifications = {
            'eligibility': ['eligibility', 'qualification', 'criteria', 'screening'],
            'programs': ['program', 'service', 'intervention', 'evidence-based'],
            'outcomes': ['outcome', 'result', 'effectiveness', 'evaluation', 'metric'],
            'workforce': ['workforce', 'training', 'staff', 'personnel', 'credential'],
            'funding': ['funding', 'budget', 'finance', 'cost', 'payment'],
            'monitoring': ['monitor', 'quality', 'accountability', 'oversight', 'fidelity'],
            'equity': ['equity', 'disparity', 'disparities', 'racial', 'cultural'],
            'target': ['target', 'population', 'demographic', 'serve', 'client']
        }
        
        for category, keywords in classifications.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def create_smart_chunks(self, markdown_text: str, structure: Dict) -> List[Dict]:
        """Create intelligent chunks based on document structure."""
        chunks = []
        current_chunk = {
            'content': '',
            'sections': [],
            'tokens': 0,
            'categories': set()
        }
        
        target_size = self.config['chunking_config']['target_chunk_size']
        
        for section in structure['sections']:
            # Check if adding this section would exceed target size
            if (current_chunk['tokens'] + section['tokens'] > target_size and 
                current_chunk['tokens'] > 0):
                # Save current chunk
                chunks.append(current_chunk)
                current_chunk = {
                    'content': '',
                    'sections': [],
                    'tokens': 0,
                    'categories': set()
                }
            
            # Add section to current chunk
            current_chunk['content'] += section['content'] + '\n\n'
            current_chunk['sections'].append(section['title'])
            current_chunk['tokens'] += section['tokens']
            current_chunk['categories'].add(section['type'])
        
        # Don't forget the last chunk
        if current_chunk['content']:
            chunks.append(current_chunk)
        
        return chunks
```

### 2.2 Extraction Engine

```python
# src/extraction_engine.py
import json
from typing import Dict, List, Optional
import openai  # or import anthropic
from tqdm import tqdm

class ExtractionEngine:
    def __init__(self, config: Dict, api_key: str):
        self.config = config
        self.api_key = api_key
        
        if config['model_config']['provider'] == 'openai':
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        # Add anthropic setup if needed
    
    def extract_full_context_categories(self, document: str, categories: List[str]) -> Dict:
        """Extract categories that require full document context."""
        results = {}
        
        for category in tqdm(categories, desc="Full context extraction"):
            prompt = self._get_full_context_prompt(document, category)
            response = self._call_llm(prompt)
            results[category] = self._parse_response(response, category)
        
        return results
    
    def extract_chunk_categories(self, chunks: List[Dict], categories: List[str]) -> Dict:
        """Extract categories from document chunks."""
        all_results = {cat: [] for cat in categories}
        
        for chunk in tqdm(chunks, desc="Processing chunks"):
            # Determine which categories to extract from this chunk
            relevant_categories = self._get_relevant_categories(chunk, categories)
            
            if relevant_categories:
                prompt = self._get_chunk_prompt(chunk['content'], relevant_categories)
                response = self._call_llm(prompt)
                chunk_results = self._parse_response(response, 'multi')
                
                # Aggregate results
                for category, values in chunk_results.items():
                    if category in all_results and values:
                        all_results[category].extend(values if isinstance(values, list) else [values])
        
        return all_results
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API."""
        try:
            if self.config['model_config']['provider'] == 'openai':
                response = self.client.chat.completions.create(
                    model=self.config['model_config']['model_name'],
                    messages=[
                        {"role": "system", "content": "You are an expert at extracting structured data from government documents."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config['model_config']['temperature'],
                    max_tokens=self.config['model_config']['max_tokens']
                )
                return response.choices[0].message.content
            # Add anthropic implementation
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "{}"
    
    def _get_relevant_categories(self, chunk: Dict, categories: List[str]) -> List[str]:
        """Determine which categories are relevant for a chunk."""
        relevance_map = {
            'programs': ['programs_waiting_to_add'],
            'eligibility': ['eligibility_determination', 'target_populations'],
            'workforce': ['workforce_support'],
            'funding': ['funding_sources'],
            'general': categories  # Extract all from general sections
        }
        
        relevant = set()
        for section_type in chunk['categories']:
            if section_type in relevance_map:
                relevant.update(relevance_map[section_type])
        
        return list(relevant.intersection(set(categories)))
    
    def _parse_response(self, response: str, category: str) -> any:
        """Parse LLM response into structured data."""
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # Fallback parsing logic
            return self._fallback_parse(response, category)
    
    def _fallback_parse(self, response: str, category: str) -> any:
        """Fallback parsing if JSON parsing fails."""
        # Implement regex-based or line-based parsing
        if category in ['trauma_informed_delivery']:
            return 'yes' in response.lower()
        else:
            # Extract bullet points or numbered lists
            lines = response.strip().split('\n')
            return [line.strip('- •*').strip() for line in lines if line.strip()]
```

### 2.3 Prompts Module

```python
# src/prompts.py

EXTRACTION_SCHEMA = {
    "programs_waiting_to_add": {
        "type": "list",
        "description": "Programs not currently reimbursable but pending clearinghouse evaluation"
    },
    "target_populations": {
        "type": "list_of_objects",
        "description": "Groups explicitly described as intended recipients",
        "object_schema": {
            "population": "string",
            "characteristics": "list"
        }
    },
    "eligibility_determination": {
        "type": "object",
        "schema": {
            "methods": "list",
            "screening_tools": "list",
            "decision_process": "string"
        }
    },
    "effectiveness_outcomes": {
        "type": "list_of_objects",
        "object_schema": {
            "metric": "string",
            "target": "string"
        }
    },
    "monitoring_accountability": {
        "type": "list",
        "description": "CQI processes, fidelity monitoring, data systems"
    },
    "workforce_support": {
        "type": "object",
        "schema": {
            "training_plans": "list",
            "credentialing_requirements": "list"
        }
    },
    "funding_sources": {
        "type": "categorized_list",
        "categories": ["federal", "state", "local", "private"]
    },
    "trauma_informed_delivery": {
        "type": "boolean",
        "evidence_required": True
    },
    "equity_disparity_reduction": {
        "type": "object",
        "schema": {
            "addresses_equity": "boolean",
            "targeted_groups": "list",
            "approaches": "list"
        }
    },
    "structural_determinants": {
        "type": "object",
        "schema": {
            "addresses_determinants": "boolean",
            "types_of_supports": "categorized_list"
        }
    }
}

def get_full_context_prompt(document: str, category: str) -> str:
    """Generate prompt for full-context extraction."""
    
    category_prompts = {
        "effectiveness_outcomes": f"""
Analyze this entire state prevention plan document to extract system-level effectiveness outcomes.

IMPORTANT: 
- Focus on SYSTEM-LEVEL outcomes (e.g., reunification rates, placement stability)
- DO NOT include program-specific metrics
- Look for stated goals, targets, or benchmarks

Document:
{document}

Extract all effectiveness outcomes mentioned. For each outcome, include:
1. The metric name
2. Any target value or benchmark if specified
3. The timeframe if mentioned

Return as JSON:
{{
    "effectiveness_outcomes": [
        {{
            "metric": "metric name",
            "target": "target value or null",
            "timeframe": "timeframe or null"
        }}
    ]
}}
""",
        
        "monitoring_accountability": f"""
Analyze this document to identify all monitoring and accountability mechanisms.

Look for:
- Continuous Quality Improvement (CQI) processes
- Fidelity monitoring approaches
- Data collection and review systems
- Oversight structures
- Review frequencies

Document:
{document}

Return as JSON:
{{
    "monitoring_accountability": [
        {{
            "mechanism": "type of monitoring",
            "description": "detailed description",
            "frequency": "if specified"
        }}
    ]
}}
""",
        
        "equity_disparity_reduction": f"""
Analyze how this state addresses equity and reduces disparities in their prevention plan.

Identify:
- Any mention of racial, ethnic, or cultural disparities
- Rural service considerations
- LGBTQ+ family considerations
- Specific strategies to address inequities
- Data collection on disparities

Document:
{document}

Return as JSON:
{{
    "addresses_equity": true/false,
    "targeted_groups": ["group1", "group2"],
    "approaches": ["approach1", "approach2"],
    "equity_goals": ["goal1", "goal2"]
}}
""",
        
        "structural_determinants": f"""
Identify whether and how the state addresses structural determinants of child welfare involvement.

Look for services or referrals related to:
- Housing assistance/stability
- Childcare access
- Healthcare access
- Income/employment support
- Food security
- Transportation
- Education support

Document:
{document}

Return as JSON:
{{
    "addresses_determinants": true/false,
    "types_of_supports": {{
        "housing": ["program1", "program2"],
        "childcare": ["program1"],
        "healthcare": ["program1"],
        "income_support": ["program1"],
        "food_security": ["program1"],
        "transportation": ["program1"],
        "education": ["program1"],
        "other": ["type: program"]
    }}
}}
"""
    }
    
    return category_prompts.get(category, "")

def get_chunk_prompt(chunk: str, categories: List[str]) -> str:
    """Generate prompt for chunk-based extraction."""
    
    category_instructions = {
        "programs_waiting_to_add": """
Programs mentioned as:
- Pending clearinghouse review/evaluation
- To be added in the future
- Under consideration
- Awaiting approval
""",
        "target_populations": """
Specific groups targeted for services such as:
- Families at risk of foster care
- Families with substance use issues
- Specific age groups
- Prior child welfare involvement
Include any qualifying characteristics mentioned
""",
        "eligibility_determination": """
How eligibility is determined:
- Screening tools used (with names)
- Assessment processes
- Decision criteria
- Who makes eligibility decisions
""",
        "workforce_support": """
Workforce development including:
- Training requirements or plans
- Professional development
- Credentialing/certification requirements
- Supervision structures
""",
        "funding_sources": """
All funding sources mentioned:
- Federal (Title IV-E, Medicaid, TANF, etc.)
- State appropriations
- Local/county funds
- Private funding or grants
Include specific program names when mentioned
""",
        "trauma_informed_delivery": """
Any mention of:
- Trauma-informed care/practice/approach
- Trauma training
- Trauma-responsive services
Mark as true if ANY mention exists
"""
    }
    
    instructions = "\n".join([f"\n{cat}:\n{category_instructions.get(cat, '')}" 
                             for cat in categories])
    
    return f"""
Extract the following information from this section of a state prevention plan:

{instructions}

Section content:
{chunk}

IMPORTANT:
- Only extract information explicitly stated in this section
- Return null/empty for any category not found
- Be precise and include specific names/tools when mentioned

Return as JSON with only the requested categories.
"""
```

### 2.4 Main Execution Script

```python
# main.py
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.document_processor import DocumentProcessor
from src.extraction_engine import ExtractionEngine
from src.validators import ResultValidator

load_dotenv()

def process_state_document(file_path: str, config: Dict) -> Dict:
    """Process a single state FFPSA document."""
    
    print(f"\nProcessing: {file_path}")
    
    # Initialize components
    processor = DocumentProcessor(config)
    engine = ExtractionEngine(config, os.getenv('API_KEY'))
    validator = ResultValidator(config)
    
    # Read document
    with open(file_path, 'r', encoding='utf-8') as f:
        document = f.read()
    
    # Extract state name from filename
    state_name = Path(file_path).stem.split('_')[0]
    
    # Phase 1: Analyze structure
    print("Analyzing document structure...")
    structure = processor.analyze_structure(document)
    print(f"Found {len(structure['sections'])} sections, {structure['total_tokens']} tokens")
    
    # Phase 2: Full context extraction
    print("\nExtracting full-context categories...")
    full_context_results = engine.extract_full_context_categories(
        document, 
        config['extraction_categories']['full_context']
    )
    
    # Phase 3: Chunk-based extraction
    print("\nCreating smart chunks...")
    chunks = processor.create_smart_chunks(document, structure)
    print(f"Created {len(chunks)} chunks")
    
    print("Extracting chunk-based categories...")
    chunk_results = engine.extract_chunk_categories(
        chunks,
        config['extraction_categories']['chunk_based']
    )
    
    # Phase 4: Merge results
    print("\nMerging results...")
    final_results = {
        'state': state_name,
        'document_date': extract_document_date(document),
        'extraction_date': datetime.now().isoformat(),
        **full_context_results,
        **chunk_results
    }
    
    # Phase 5: Validate and clean
    print("Validating results...")
    final_results = validator.validate_and_clean(final_results)
    
    # Phase 6: Add confidence scores
    final_results['extraction_confidence'] = validator.calculate_confidence(final_results)
    
    return final_results

def extract_document_date(document: str) -> str:
    """Extract document date from content."""
    import re
    
    # Common date patterns in government documents
    date_patterns = [
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, document[:5000])  # Check first part of doc
        if match:
            return match.group(0)
    
    return "Unknown"

def main():
    """Main execution function."""
    
    # Load configuration
    with open('config/extraction_config.json', 'r') as f:
        config = json.load(f)
    
    # Setup paths
    input_dir = Path('data/input/state_plans')
    output_dir = Path('data/output/extracted')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all documents
    results = []
    for file_path in input_dir.glob('*.md'):
        try:
            result = process_state_document(str(file_path), config)
            
            # Save individual result
            output_path = output_dir / f"{result['state']}_extracted.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            print(f"✓ Completed: {result['state']}")
            
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            continue
    
    # Save combined results
    combined_path = output_dir / f"all_states_extracted_{datetime.now().strftime('%Y%m%d')}.json"
    with open(combined_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Extraction complete! Processed {len(results)} documents")
    print(f"Results saved to: {combined_path}")

if __name__ == "__main__":
    main()
```

### 2.5 Validator Module

```python
# src/validators.py
from typing import Dict, List, Any
import json

class ResultValidator:
    def __init__(self, config: Dict):
        self.config = config
        self.required_fields = [
            'programs_waiting_to_add',
            'target_populations',
            'eligibility_determination',
            'effectiveness_outcomes',
            'monitoring_accountability',
            'workforce_support',
            'funding_sources',
            'trauma_informed_delivery',
            'equity_disparity_reduction',
            'structural_determinants'
        ]
    
    def validate_and_clean(self, results: Dict) -> Dict:
        """Validate and clean extraction results."""
        cleaned = results.copy()
        
        # Ensure all required fields exist
        for field in self.required_fields:
            if field not in cleaned:
                cleaned[field] = self._get_default_value(field)
        
        # Remove duplicates from lists
        for key, value in cleaned.items():
            if isinstance(value, list):
                cleaned[key] = self._deduplicate_list(value)
            elif isinstance(value, dict):
                cleaned[key] = self._clean_dict(value)
        
        # Validate boolean fields
        boolean_fields = ['trauma_informed_delivery']
        for field in boolean_fields:
            if field in cleaned and not isinstance(cleaned[field], bool):
                cleaned[field] = bool(cleaned[field])
        
        return cleaned
    
    def _deduplicate_list(self, lst: List) -> List:
        """Remove duplicates while preserving order."""
        seen = set()
        deduped = []
        
        for item in lst:
            # Convert dict to hashable type for comparison
            if isinstance(item, dict):
                item_key = json.dumps(item, sort_keys=True)
            else:
                item_key = item
            
            if item_key not in seen:
                seen.add(item_key)
                deduped.append(item)
        
        return deduped
    
    def _clean_dict(self, d: Dict) -> Dict:
        """Clean dictionary values."""
        cleaned = {}
        for key, value in d.items():
            if isinstance(value, list):
                cleaned[key] = self._deduplicate_list(value)
            elif value is not None:  # Remove null values
                cleaned[key] = value
        return cleaned
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field."""
        defaults = {
            'programs_waiting_to_add': [],
            'target_populations': [],
            'eligibility_determination': {
                'methods': [],
                'screening_tools': [],
                'decision_process': ''
            },
            'effectiveness_outcomes': [],
            'monitoring_accountability': [],
            'workforce_support': {
                'training_plans': [],
                'credentialing_requirements': []
            },
            'funding_sources': {
                'federal': [],
                'state': [],
                'local': [],
                'private': []
            },
            'trauma_informed_delivery': False,
            'equity_disparity_reduction': {
                'addresses_equity': False,
                'targeted_groups': [],
                'approaches': []
            },
            'structural_determinants': {
                'addresses_determinants': False,
                'types_of_supports': {}
            }
        }
        return defaults.get(field, None)
    
    def calculate_confidence(self, results: Dict) -> Dict:
        """Calculate confidence scores for extraction."""
        high_confidence = 0
        low_confidence = 0
        flagged_for_review = []
        
        for field in self.required_fields:
            if field not in results:
                flagged_for_review.append(field)
                low_confidence += 1
            elif isinstance(results[field], list) and len(results[field]) == 0:
                low_confidence += 1
            elif isinstance(results[field], dict):
                if not any(results[field].values()):
                    low_confidence += 1
                else:
                    high_confidence += 1
            else:
                high_confidence += 1
        
        return {
            'high_confidence_extractions': high_confidence,
            'low_confidence_extractions': low_confidence,
            'flagged_for_review': flagged_for_review,
            'confidence_score': high_confidence / len(self.required_fields)
        }
```

## Phase 3: Testing and Validation

### 3.1 Test Script

```python
# tests/test_extraction.py
import json
from pathlib import Path

def test_single_document():
    """Test extraction on a single document."""
    
    # Use a sample document
    test_file = "data/input/state_plans/california_prevention_plan.md"
    
    # Run extraction
    from main import process_state_document
    
    with open('config/extraction_config.json', 'r') as f:
        config = json.load(f)
    
    result = process_state_document(test_file, config)
    
    # Validate result structure
    assert 'state' in result
    assert 'extraction_confidence' in result
    assert result['extraction_confidence']['confidence_score'] > 0.5
    
    # Print sample results
    print("\n=== Sample Extraction Results ===")
    print(f"State: {result['state']}")
    print(f"Confidence Score: {result['extraction_confidence']['confidence_score']:.2f}")
    print(f"\nPrograms Waiting: {len(result.get('programs_waiting_to_add', []))}")
    print(f"Target Populations: {len(result.get('target_populations', []))}")
    print(f"Trauma-Informed: {result.get('trauma_informed_delivery', False)}")
    
    # Save for manual review
    with open('tests/test_output.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\nTest completed! Review test_output.json for full results.")

if __name__ == "__main__":
    test_single_document()
```

## Phase 4: Deployment and Scaling

### 4.1 Batch Processing Script

```python
# batch_process.py
import concurrent.futures
from pathlib import Path
import json

def batch_process_states(max_workers=3):
    """Process multiple states in parallel."""
    
    input_files = list(Path('data/input/state_plans').glob('*.md'))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for file_path in input_files:
            future = executor.submit(process_state_document, str(file_path), config)
            futures.append((file_path, future))
        
        results = []
        for file_path, future in futures:
            try:
                result = future.result()
                results.append(result)
                print(f"✓ {file_path.stem}")
            except Exception as e:
                print(f"✗ {file_path.stem}: {e}")
    
    return results
```

### 4.2 Quality Assurance Checklist

```python
# qa_checklist.py

QA_CHECKLIST = {
    "completeness": [
        "All 10 categories extracted",
        "No empty results without justification",
        "Document date identified"
    ],
    "accuracy": [
        "Spot check 5 extractions against source",
        "Verify boolean fields are actually boolean",
        "Check for obvious duplicates"
    ],
    "consistency": [
        "Same format across all states",
        "Consistent categorization of funding sources",
        "Standardized population descriptions"
    ],
    "technical": [
        "No JSON parsing errors",
        "All API calls successful",
        "Token limits respected"
    ]
}
```

## Phase 5: Analysis and Reporting

### 5.1 Analysis Script

```python
# analyze_results.py
import pandas as pd
import json
from pathlib import Path

def analyze_extractions():
    """Analyze extracted data across all states."""
    
    # Load all results
    results_file = Path('data/output/extracted/all_states_extracted.json')
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(data)
    
    # Basic statistics
    print("\n=== Extraction Statistics ===")
    print(f"Total states processed: {len(df)}")
    print(f"Average confidence score: {df['extraction_confidence'].apply(lambda x: x['confidence_score']).mean():.2f}")
    
    # Trauma-informed adoption
    trauma_informed_count = df['trauma_informed_delivery'].sum()
    print(f"\nStates with trauma-informed delivery: {trauma_informed_count}/{len(df)}")
    
    # Equity focus
    equity_count = df['equity_disparity_reduction'].apply(lambda x: x['addresses_equity']).sum()
    print(f"States addressing equity: {equity_count}/{len(df)}")
    
    # Most common funding sources
    all_funding = []
    for _, row in df.iterrows():
        federal_funding = row['funding_sources'].get('federal', [])
        all_funding.extend(federal_funding)
    
    funding_counts = pd.Series(all_funding).value_counts()
    print("\n=== Top Federal Funding Sources ===")
    print(funding_counts.head(10))
    
    # Export analysis
    df.to_csv('data/output/analysis_summary.csv', index=False)
    print("\nAnalysis exported to analysis_summary.csv")
```

## Execution Timeline

1. **Week 1**: Setup and single document testing
2. **Week 2**: Refine prompts based on test results
3. **Week 3**: Process all 50+ state documents
4. **Week 4**: Quality assurance and analysis

## Cost Estimate

- **Development**: 40-60 hours
- **API Costs**: ~$10-15 per document
- **Total for 50 states**: ~$500-750

This represents significant savings compared to 40-50 hours of manual coding per document.
