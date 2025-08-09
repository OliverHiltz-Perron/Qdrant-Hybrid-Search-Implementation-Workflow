# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows
- Comprehensive test suite with pytest
- Project documentation (README, CONTRIBUTING)
- Python packaging configuration (pyproject.toml, setup.py)
- Environment variable template (.env.example)

### Changed
- Reorganized project structure for GitHub
- Updated .gitignore for better coverage
- Moved requirements.txt to project root

### Security
- Removed exposed API keys from repository
- Added credentials to .gitignore

## [1.0.0] - 2024-01-01

### Added
- Initial release of FFPSA Pipeline
- RAG pipeline for processing state prevention plans
- Support for 42 US states
- 14 task category extractions
- Hybrid search with Qdrant
- LLM extraction with GPT-4
- Structured validation with Pydantic
- Incremental processing capabilities
- Comprehensive logging system

### Features
- Semantic document chunking
- BM25 + dense vector hybrid search
- Jina AI reranking
- Instructor library validation
- Batch processing support
- Cloud and local Qdrant support

[Unreleased]: https://github.com/yourusername/ffpsa-pipeline/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/ffpsa-pipeline/releases/tag/v1.0.0