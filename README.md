# FFPSA Prevention Plan Analysis Pipeline

## Advancing Policy Analysis Through Retrieval-Augmented Generation

A comprehensive RAG (Retrieval-Augmented Generation) pipeline for systematically extracting structured data from Title IV-E Prevention Services state plans across 42 US states, transforming thousands of pages of complex policy documentation into analyzable insights.

### 🎯 Research Innovation

This project implements a methodology that addresses critical challenges in policy analysis:

- **Scale**: Processing 2,000+ pages across 42 state documents
- **Complexity**: Extracting structured data from 14 distinct policy categories
- **Variability**: Handling diverse terminology (e.g., "kinship care" vs. "relative caregivers")
- **Accuracy**: Maintaining consistency through automated validation and quality assurance

Unlike traditional manual analysis that would require months of expert review, this pipeline reduces analysis time by ~95% while improving consistency and enabling previously impossible cross-jurisdictional comparisons.

## 📋 Overview

This system implements the methodology described in "Advancing Policy Analysis Through Retrieval-Augmented Generation" (Perron et al., 2025), using a sophisticated two-phase approach:

1. **Semantic Retrieval Phase**: Identifies relevant content using embeddings and hybrid search
2. **Focused Extraction Phase**: Applies LLMs to transform text into structured, validated data

The pipeline processes Family First Prevention Services Act (FFPSA) Title IV-E prevention plans to extract standardized information across 14 policy categories, enabling comprehensive analysis of how states implement child welfare prevention services.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT PREPARATION                         │
├─────────────────────────────────────────────────────────────────┤
│ PDF Documents → Markdown → Semantic Chunking → Embeddings      │
│                                    ↓                            │
│              Vector Database (Qdrant) + BM25 Index             │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL & EXTRACTION                       │
├─────────────────────────────────────────────────────────────────┤
│ Query Expansion → Hybrid Search (70% Vector + 30% BM25)         │
│         ↓                                                       │
│ Cross-Encoder Reranking → Top-K Selection                       │
│         ↓                                                       │
│ GPT-4.1 Schema-Based Extraction → Pydantic Validation           │
│         ↓                                                       │
│ Structured JSON Output with Quality Metrics                     │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Key Features

### Advanced RAG Implementation

- **Semantic Document Chunking**: Preserves policy context across chunk boundaries
- **Hybrid Search Architecture**:
  - 70% Dense vector search for semantic understanding
  - 30% Sparse BM25 for exact term matching
- **Cross-Encoder Reranking**: Improves retrieval precision by 20-40%
- **State-Specific Processing**: Maintains jurisdictional context

### Robust Extraction & Validation

- **Schema-Based Extraction**: 14 Pydantic models ensure data consistency
- **Instructor Library Integration**: Type-safe LLM outputs
- **Multi-Stage Validation**: Faithfulness, relevancy, and completeness checks
- **Incremental Processing**: Resume capability for large-scale analysis

### Quality Assurance

- **RAGAS Metrics**: Automated evaluation without ground truth
- **Confidence Scoring**: Flags low-confidence extractions for review
- **Audit Trail**: Complete provenance from source to extraction

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (for local Qdrant)
- OpenAI API key
- Jina API key (for reranking)
- 16GB+ RAM recommended

### Installation

1. Clone the repository:

```bash
git clone https://github.com/[yourusername]/FFPSA.git
cd FFPSA
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start Qdrant (for local development):

```bash
# First, pull the Qdrant image
docker pull qdrant/qdrant

# Then run Qdrant with persistent storage
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

### Running the Pipeline

Process specific states and tasks:

```bash
cd src
python pipeline.py --states CA FL TX --tasks FundingSources PreventionPrograms
```

Process all 42 states for specific tasks:

```bash
cd src
python pipeline.py --tasks TraumaInformed EquityDisparity
```

Full pipeline execution:

```bash
cd src
python pipeline.py  # Processes all states and all 14 tasks
```

## 📁 Project Structure

```
FFPSA/
├── src/                   # Main pipeline implementation
│   ├── pipeline.py        # Multi-state orchestrator
│   ├── pipeline_core.py   # Core RAG implementation
│   ├── llm_processor.py   # GPT-4 extraction with validation
│   ├── embed_local.py     # Document embedding pipeline
│   ├── embed_cloud.py     # Cloud deployment embeddings
│   ├── validation_models.py # 14 Pydantic schemas
│   ├── prompt_manager.py  # Prompt engineering system
│   ├── config/            # Configuration management
│   └── Prompts/           # Task-specific prompts
│       ├── LLM/           # Extraction prompts (14 categories)
│       ├── Reranker/      # Cross-encoder prompts
│       ├── BM25/          # Keyword expansion queries
│       └── RAG/           # Semantic search queries
├── states/                # Source documents (42 state plans)
├── multi_state_output_standardized/  # Structured outputs
│   ├── [STATE]/           # State-specific results
│   ├── _combined_by_task/ # Cross-state comparisons
│   └── overall_summary.json
├── tests/                 # Test suite
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Development dependencies
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── CONTRIBUTING.md        # Contribution guidelines
└── CHANGELOG.md           # Version history
```

## 📊 14 Policy Categories Analyzed

Each category uses specialized extraction schemas validated through Pydantic:

| Category                     | Focus Area                          | Key Metrics                        |
| ---------------------------- | ----------------------------------- | ---------------------------------- |
| **FundingSources**           | Funding mechanisms and allocations  | Amounts, sources, restrictions     |
| **CandidateDefinition**      | Eligibility for prevention services | Criteria, risk factors, assessment |
| **EligibilityDetermination** | Determination processes             | Procedures, timelines, appeals     |
| **EvaluationMetrics**        | Outcome measurement                 | Goals, indicators, benchmarks      |
| **PreventionPrograms**       | Service offerings                   | Types, providers, evidence-base    |
| **StructuralDeterminants**   | Social determinants of health       | Housing, poverty, education        |
| **TargetPopulations**        | Service recipients                  | Demographics, risk profiles        |
| **TraumaInformed**           | Trauma-informed approaches          | Training, practices, protocols     |
| **TribalConsultation**       | Tribal sovereignty and consultation | Processes, agreements, outcomes    |
| **EquityDisparity**          | Addressing disparities              | Data, strategies, outcomes         |
| **MonitoringAccountability** | Quality assurance                   | Systems, metrics, reporting        |
| **NonReimbursablePrograms**  | Non-IV-E funded services            | Scope, funding, coordination       |
| **CommunityEngagement**      | Stakeholder involvement             | Methods, frequency, impact         |
| **WorkforceSupport**         | Staff development and retention     | Training, compensation, wellbeing  |

## 🔄 Pipeline Workflow

### Phase 1: Document Preparation

```bash
# Process and embed documents
python embed_local.py  # Creates vector database locally
# OR
python embed_cloud.py  # Deploy to Qdrant Cloud
```

### Phase 2: Multi-State Extraction

```bash
# Run extraction with custom parameters
python pipeline.py \
  --states CA FL TX NY \
  --tasks FundingSources PreventionPrograms \
  --n-results 50 \      # Initial retrieval
  --n-rerank 20 \       # After reranking
  --n-llm 10           # For extraction
```

### Phase 3: Quality Assurance

The pipeline automatically:

- Calculates RAGAS metrics (faithfulness, relevancy, completeness)
- Flags low-confidence extractions
- Generates validation reports

## 📈 Output Format

### Structured JSON Schema

```json
{
  "state": "California",
  "task": "TraumaInformed",
  "extraction": {
    "programs": [
      {
        "name": "Trauma-Focused Cognitive Behavioral Therapy",
        "target_population": "Children aged 3-18",
        "evidence_base": "Well-Supported Practice",
        "implementation_status": "Active",
        "training_requirements": {
          "hours": 16,
          "frequency": "Annual",
          "providers": ["Licensed clinicians"]
        }
      }
    ],
    "workforce_training": {...},
    "assessment_tools": [...]
  },
  "metadata": {
    "processed_at": "2025-01-08T10:30:00Z",
    "chunks_analyzed": 15,
    "confidence_score": 0.92,
    "source_pages": [12, 34, 67, 89]
  },
  "quality_metrics": {
    "faithfulness": 0.95,
    "relevancy": 0.88,
    "completeness": 0.91
  }
}
```

## ⚙️ Configuration

Key settings in `LocalQDrant/config/config.py`:

| Parameter         | Default                | Description                      |
| ----------------- | ---------------------- | -------------------------------- |
| `EMBEDDING_MODEL` | text-embedding-3-small | OpenAI embedding model           |
| `LLM_MODEL`       | gpt-4.1                | Extraction model                 |
| `CHUNK_SIZE`      | 1000 tokens            | Semantic chunk size              |
| `CHUNK_OVERLAP`   | 200 tokens             | Overlap for context preservation |
| `VECTOR_WEIGHT`   | 0.7                    | Weight for semantic search       |
| `BM25_WEIGHT`     | 0.3                    | Weight for keyword search        |
| `SEARCH_LIMIT`    | 50                     | Initial retrieval count          |
| `RERANK_TOP_K`    | 20                     | Post-reranking selection         |
| `LLM_TOP_K`       | 10                     | Final extraction input           |

## 🔐 Environment Variables

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
JINA_API_KEY=your_jina_api_key  # For cross-encoder reranking

# Qdrant Configuration
QDRANT_URL=http://127.0.0.1:6333  # Local instance
# For cloud deployment:
# QDRANT_CLOUD_URL=https://your-cluster.aws.cloud.qdrant.io
# QDRANT_API_KEY=your_qdrant_api_key

# Optional Configuration
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=300
```

## 🧪 Testing

```bash
# Run full test suite
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Test specific policy category
python -m pytest tests/test_validation_models.py::TestFundingSources
```

## 📊 Performance Metrics

- **Processing Speed**: ~2-3 minutes per state/task combination
- **Accuracy**: 92-95% extraction accuracy (validated against manual coding)
- **Coverage**: Successfully processes 98% of document variations
- **Scalability**: Handles documents from 25-150 pages
- **Cost Efficiency**: ~$0.50-1.00 per state/task in API costs

## 🤝 Research Impact

This methodology enables:

- **Cross-jurisdictional Analysis**: Compare implementation across all 42 states
- **Longitudinal Studies**: Track policy evolution over time
- **Innovation Diffusion**: Identify how best practices spread
- **Equity Analysis**: Examine disparities in service provision
- **Real-time Monitoring**: Update analyses as policies change

## 📝 Citation

If you use this methodology or code in your research, please cite:

```bibtex
@article{perron2025advancing,
  title={Advancing Policy Analysis Through Retrieval-Augmented Generation:
         A Methodology for Extracting Structured Data from Child Welfare Policy},
  author={Perron, Brian E. and Hiltz-Perron, Oliver T. and
          Lyujun, Zhou and Eldeeb, Nehal},
  journal={Manuscript submitted for publication},
  year={2025}
}
```

## 🔗 Related Publications

- Perron et al. (2025a). "AI-enhanced social work: Developing and evaluating RAG support systems." _Journal of Social Work Education_, 61(1), 3-13.
- Perron et al. (2024). "Moving beyond ChatGPT: Local LLMs and secure analysis of confidential data." _Research on Social Work Practice_.
- Perron et al. (2025b). "A Primer on Word Embeddings: AI Techniques for Text Analysis." _Journal of the Society for Social Work and Research_, 16(2).

## 🙏 Acknowledgments

- Vector search powered by Qdrant
- Cross-encoder reranking by Jina AI
- Validation using Pydantic & Instructor

## 📞 Support

For technical issues: Open a GitHub issue

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

_This project demonstrates the transformative potential of combining human expertise with AI capabilities in policy research, maintaining the critical role of domain knowledge while leveraging computational power for systematic analysis at scale._
