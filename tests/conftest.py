"""Pytest configuration and fixtures"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import project modules
import config


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock = MagicMock()
    mock.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"test": "response"}'))]
    )
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing"""
    mock = MagicMock()
    mock.get_collections.return_value = MagicMock(collections=[])
    mock.search.return_value = []
    return mock


@pytest.fixture
def sample_chunk():
    """Sample chunk data for testing"""
    return {
        "text": "This is a sample chunk of text for testing purposes.",
        "metadata": {
            "state": "CA",
            "section": "FundingSources",
            "chunk_id": "test_001",
            "start_position": 0,
            "end_position": 50
        }
    }


@pytest.fixture
def sample_state_data():
    """Sample state data for testing"""
    return {
        "state": "CA",
        "title": "California Prevention Plan",
        "sections": {
            "funding_sources": "Title IV-E funding information...",
            "prevention_programs": "Evidence-based programs...",
            "target_populations": "Children and families at risk..."
        }
    }


@pytest.fixture
def test_config(tmp_path):
    """Test configuration with temporary directories"""
    return {
        "BASE_DIR": tmp_path,
        "DATA_DIR": tmp_path / "states",
        "OUTPUT_DIR": tmp_path / "output",
        "LOG_DIR": tmp_path / "logs",
        "CHUNK_DIR": tmp_path / "chunks",
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "LLM_MODEL": "gpt-3.5-turbo",
        "CHUNK_SIZE": 500,
        "CHUNK_OVERLAP": 50,
        "SEARCH_LIMIT": 10,
        "RERANK_TOP_K": 5
    }


@pytest.fixture
def env_setup(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("JINA_API_KEY", "test_jina_key")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    

@pytest.fixture
def mock_prompt_manager():
    """Mock prompt manager for testing"""
    mock = MagicMock()
    mock.get_prompt.return_value = "Test prompt for {task}"
    mock.list_available_prompts.return_value = ["FundingSources", "PreventionPrograms"]
    return mock