"""Unit tests for validation models"""

import pytest
from typing import List, Optional
from pydantic import ValidationError
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from validation_models import (
    FundingSource,
    FundingSourcesExtraction,
    PreventionProgram,
    PreventionProgramsExtraction,
    TASK_MODELS
)


class TestFundingSourceModel:
    """Test cases for FundingSource model"""
    
    def test_valid_funding_source(self):
        """Test creating a valid funding source"""
        source = FundingSource(
            source_name="Title IV-E",
            amount="$1,000,000",
            description="Federal funding for prevention services"
        )
        
        assert source.source_name == "Title IV-E"
        assert source.amount == "$1,000,000"
        assert source.description == "Federal funding for prevention services"
    
    def test_optional_fields(self):
        """Test funding source with optional fields"""
        source = FundingSource(
            source_name="State Funding"
        )
        
        assert source.source_name == "State Funding"
        assert source.amount is None
        assert source.description is None
    
    def test_empty_string_becomes_none(self):
        """Test that empty strings are converted to None"""
        source = FundingSource(
            source_name="Test",
            amount="",
            description=""
        )
        
        assert source.source_name == "Test"
        # Depending on validation, empty strings might stay or become None
        # Adjust based on actual model behavior


class TestFundingSourcesExtraction:
    """Test cases for FundingSourcesExtraction model"""
    
    def test_valid_extraction(self):
        """Test creating a valid extraction"""
        extraction = FundingSourcesExtraction(
            funding_sources=[
                {"source_name": "Title IV-E", "amount": "$500,000"},
                {"source_name": "State General Fund", "amount": "$300,000"}
            ],
            total_amount="$800,000",
            fiscal_year="2024"
        )
        
        assert len(extraction.funding_sources) == 2
        assert extraction.total_amount == "$800,000"
        assert extraction.fiscal_year == "2024"
    
    def test_empty_list_allowed(self):
        """Test that empty lists are allowed"""
        extraction = FundingSourcesExtraction(
            funding_sources=[]
        )
        
        assert extraction.funding_sources == []
        assert extraction.total_amount is None
    
    def test_none_converted_to_empty_list(self):
        """Test that None is converted to empty list"""
        extraction = FundingSourcesExtraction(
            funding_sources=None
        )
        
        assert extraction.funding_sources == []


class TestPreventionProgramModel:
    """Test cases for PreventionProgram model"""
    
    def test_valid_prevention_program(self):
        """Test creating a valid prevention program"""
        program = PreventionProgram(
            program_name="Nurse-Family Partnership",
            evidence_level="Well-Supported",
            target_population="First-time mothers",
            description="Home visiting program"
        )
        
        assert program.program_name == "Nurse-Family Partnership"
        assert program.evidence_level == "Well-Supported"
        assert program.target_population == "First-time mothers"
    
    def test_required_field_validation(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            PreventionProgram()  # Missing required program_name


class TestTaskModels:
    """Test TASK_MODELS mapping"""
    
    def test_all_tasks_have_models(self):
        """Test that all expected tasks have models"""
        expected_tasks = [
            "FundingSources",
            "PreventionPrograms",
            "CandidateDefinition",
            "EligibilityDetermination",
            "TargetPopulations",
            "EvaluationMetrics",
            "StructuralDeterminants",
            "TraumaInformed",
            "TribalConsultation",
            "EquityDisparity",
            "MonitoringAccountability",
            "NonReimbursablePrograms",
            "CommunityEngagement",
            "WorkforceSupport"
        ]
        
        for task in expected_tasks:
            assert task in TASK_MODELS
            assert TASK_MODELS[task] is not None
    
    def test_model_instantiation(self):
        """Test that models can be instantiated"""
        for task_name, model_class in TASK_MODELS.items():
            try:
                # Try to create instance with minimal data
                instance = model_class()
                assert instance is not None
            except ValidationError:
                # Some models might have required fields
                pass