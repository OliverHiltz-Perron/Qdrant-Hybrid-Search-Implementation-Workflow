"""Unit tests for PromptManager"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from prompt_manager import PromptManager


class TestPromptManager:
    """Test cases for PromptManager class"""
    
    def test_initialization(self, tmp_path):
        """Test PromptManager initialization"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        manager = PromptManager(prompts_dir)
        assert manager.prompts_dir == prompts_dir
        assert isinstance(manager.prompts_cache, dict)
    
    def test_get_prompt_success(self, tmp_path):
        """Test successful prompt retrieval"""
        prompts_dir = tmp_path / "prompts" / "LLM"
        prompts_dir.mkdir(parents=True)
        
        # Create test prompt file
        prompt_file = prompts_dir / "TestTask_LLM_Prompt.md"
        prompt_content = "This is a test prompt for {task}"
        prompt_file.write_text(prompt_content)
        
        manager = PromptManager(tmp_path / "prompts")
        prompt = manager.get_prompt("TestTask", "LLM")
        
        assert prompt == prompt_content
    
    def test_get_prompt_cached(self, tmp_path):
        """Test prompt caching"""
        prompts_dir = tmp_path / "prompts" / "LLM"
        prompts_dir.mkdir(parents=True)
        
        prompt_file = prompts_dir / "TestTask_LLM_Prompt.md"
        prompt_file.write_text("Cached prompt")
        
        manager = PromptManager(tmp_path / "prompts")
        
        # First call
        prompt1 = manager.get_prompt("TestTask", "LLM")
        # Second call should use cache
        prompt2 = manager.get_prompt("TestTask", "LLM")
        
        assert prompt1 == prompt2 == "Cached prompt"
        assert "TestTask_LLM" in manager.prompts_cache
    
    def test_get_prompt_file_not_found(self, tmp_path):
        """Test handling of missing prompt file"""
        manager = PromptManager(tmp_path / "prompts")
        
        with pytest.raises(FileNotFoundError):
            manager.get_prompt("NonExistent", "LLM")
    
    def test_list_available_prompts(self, tmp_path):
        """Test listing available prompts"""
        prompts_dir = tmp_path / "prompts" / "LLM"
        prompts_dir.mkdir(parents=True)
        
        # Create test prompt files
        tasks = ["FundingSources", "PreventionPrograms", "TargetPopulations"]
        for task in tasks:
            prompt_file = prompts_dir / f"{task}_LLM_Prompt.md"
            prompt_file.write_text(f"Prompt for {task}")
        
        manager = PromptManager(tmp_path / "prompts")
        available = manager.list_available_prompts("LLM")
        
        assert set(available) == set(tasks)
    
    def test_list_available_prompts_empty(self, tmp_path):
        """Test listing prompts when directory is empty"""
        prompts_dir = tmp_path / "prompts" / "LLM"
        prompts_dir.mkdir(parents=True)
        
        manager = PromptManager(tmp_path / "prompts")
        available = manager.list_available_prompts("LLM")
        
        assert available == []
    
    def test_clear_cache(self, tmp_path):
        """Test clearing the prompt cache"""
        prompts_dir = tmp_path / "prompts" / "LLM"
        prompts_dir.mkdir(parents=True)
        
        prompt_file = prompts_dir / "TestTask_LLM_Prompt.md"
        prompt_file.write_text("Test prompt")
        
        manager = PromptManager(tmp_path / "prompts")
        manager.get_prompt("TestTask", "LLM")
        
        assert len(manager.prompts_cache) > 0
        
        manager.clear_cache()
        assert len(manager.prompts_cache) == 0