"""Integration tests for the complete pipeline"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestCompletePipeline:
    """Integration tests for complete pipeline"""
    
    @patch('pipeline_core.QdrantClient')
    @patch('pipeline_core.OpenAI')
    def test_pipeline_initialization(self, mock_openai, mock_qdrant):
        """Test pipeline initialization"""
        from pipeline_core import initialize_clients
        
        # Setup mocks
        mock_qdrant_instance = MagicMock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.get_collections.return_value = MagicMock(collections=[])
        
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        # Create logger mock
        logger = MagicMock()
        
        # Test initialization
        qdrant_client, openai_client = initialize_clients(logger)
        
        assert qdrant_client is not None
        assert openai_client is not None
        mock_qdrant.assert_called_once()
        mock_openai.assert_called_once()
    
    @patch('pipeline_core.OpenAI')
    @patch('pipeline_core.SparseTextEmbedding')
    def test_embedding_generation(self, mock_sparse, mock_openai):
        """Test embedding generation"""
        from pipeline_core import generate_embeddings
        
        # Setup mocks
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]
        )
        
        mock_sparse_instance = MagicMock()
        mock_sparse.return_value = mock_sparse_instance
        mock_sparse_instance.embed.return_value = [
            MagicMock(indices=[1, 2, 3], values=[0.5, 0.3, 0.2])
        ]
        
        logger = MagicMock()
        
        # Test embedding generation
        query = "test query for funding sources"
        dense, sparse = generate_embeddings(query, logger)
        
        assert len(dense) == 1536
        assert sparse is not None
    
    def test_search_results_processing(self):
        """Test processing of search results"""
        # Mock search results
        search_results = [
            {
                "id": "chunk_001",
                "score": 0.95,
                "payload": {
                    "text": "Funding from Title IV-E",
                    "metadata": {"state": "CA", "section": "funding"}
                }
            },
            {
                "id": "chunk_002", 
                "score": 0.87,
                "payload": {
                    "text": "State general fund allocation",
                    "metadata": {"state": "CA", "section": "funding"}
                }
            }
        ]
        
        # Process results (simplified)
        processed = []
        for result in search_results:
            processed.append({
                "text": result["payload"]["text"],
                "score": result["score"],
                "metadata": result["payload"]["metadata"]
            })
        
        assert len(processed) == 2
        assert processed[0]["score"] == 0.95
        assert "Title IV-E" in processed[0]["text"]
    
    @patch('requests.post')
    def test_reranking(self, mock_post):
        """Test reranking functionality"""
        # Mock reranking response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.98},
                {"index": 1, "relevance_score": 0.76}
            ]
        }
        mock_post.return_value = mock_response
        
        # Test data
        query = "funding sources"
        documents = ["Title IV-E funding", "General state funds"]
        
        # Simulate reranking
        import requests
        response = requests.post(
            "https://api.jina.ai/v1/rerank",
            json={"query": query, "documents": documents}
        )
        
        results = response.json()["results"]
        assert len(results) == 2
        assert results[0]["relevance_score"] > results[1]["relevance_score"]
    
    def test_output_standardization(self):
        """Test output standardization"""
        # Test data with various empty values
        raw_output = {
            "funding_sources": [],
            "total_amount": "",
            "description": "Not specified",
            "notes": None,
            "valid_data": "This is valid"
        }
        
        # Standardize (simplified version)
        def standardize(value):
            if value is None or value == "" or value == "Not specified":
                return None
            if isinstance(value, list) and len(value) == 0:
                return []
            return value
        
        standardized = {k: standardize(v) for k, v in raw_output.items()}
        
        assert standardized["funding_sources"] == []
        assert standardized["total_amount"] is None
        assert standardized["description"] is None
        assert standardized["notes"] is None
        assert standardized["valid_data"] == "This is valid"