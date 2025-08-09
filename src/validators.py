"""Validators for extracted data."""

import json
from typing import Dict, List, Any, Tuple
from pathlib import Path


class DataValidator:
    """Validate extracted data for completeness and accuracy."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_rules = self._load_validation_rules()
        
    def _load_validation_rules(self) -> Dict:
        """Load validation rules for each category.
        
        Returns:
            Dictionary of validation rules
        """
        return {
            "programs_waiting_to_add": {
                "required_fields": ["programs", "total_count"],
                "field_types": {
                    "programs": list,
                    "total_count": int
                }
            },
            "target_populations": {
                "required_fields": ["populations"],
                "field_types": {
                    "populations": list,
                    "primary_population": str,
                    "total_populations_identified": int
                }
            },
            "eligibility_determination": {
                "required_fields": ["determination_method", "screening_tools", "quotes"],
                "field_types": {
                    "determination_method": str,
                    "screening_tools": list,
                    "decision_maker": str,
                    "candidacy_definition": str,
                    "eligibility_duration": str,
                    "quotes": list
                }
            },
            "effectiveness_outcomes": {
                "required_fields": ["outcome_goals"],
                "field_types": {
                    "outcome_goals": list,
                    "has_specific_targets": bool,
                    "evaluation_approach": str
                }
            },
            "monitoring_accountability": {
                "required_fields": ["has_monitoring_system", "quotes"],
                "field_types": {
                    "has_monitoring_system": bool,
                    "cqi_mentioned": bool,
                    "cqi_details": str,
                    "fidelity_monitoring": bool,
                    "fidelity_details": str,
                    "review_frequency": dict,
                    "monitoring_description": str,
                    "accountability_roles": list,
                    "external_evaluator": str,
                    "quotes": list
                }
            },
            "workforce_support": {
                "required_fields": ["workforce_training", "credentialing"],
                "field_types": {
                    "workforce_training": dict,
                    "credentialing": dict
                }
            },
            "funding_sources": {
                "required_fields": ["funding_sources", "has_multiple_sources"],
                "field_types": {
                    "funding_sources": list,
                    "has_multiple_sources": bool,
                    "match_requirements": list
                }
            },
            "trauma_informed_delivery": {
                "required_fields": ["uses_trauma_informed_approach", "evidence_quotes"],
                "field_types": {
                    "uses_trauma_informed_approach": bool,
                    "trauma_specific_programs": list,
                    "training_components": list,
                    "evidence_quotes": list
                }
            },
            "equity_disparity_reduction": {
                "required_fields": ["addresses_equity", "quotes"],
                "field_types": {
                    "addresses_equity": bool,
                    "explicit_equity_focus": bool,
                    "equity_approach": str,
                    "targeted_groups": list,
                    "strategies": list,
                    "parent_voice_mechanisms": list,
                    "quotes": list
                }
            },
            "structural_determinants": {
                "required_fields": ["addresses_structural_determinants", "quotes"],
                "field_types": {
                    "addresses_structural_determinants": bool,
                    "direct_services": list,
                    "referral_services": list,
                    "support_types": list,
                    "specific_programs": dict,
                    "quotes": list
                }
            }
        }
    
    def validate_extraction(self, category: str, data: Dict) -> Tuple[bool, List[str]]:
        """Validate extracted data for a specific category.
        
        Args:
            category: The extraction category
            data: The extracted data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if category not in self.validation_rules:
            return False, [f"Unknown category: {category}"]
        
        rules = self.validation_rules[category]
        
        # Check required fields
        for field in rules["required_fields"]:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        for field, expected_type in rules["field_types"].items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    errors.append(
                        f"Invalid type for {field}: expected {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
        
        # Category-specific validations
        if category == "programs_waiting_to_add":
            if "total_count" in data and "programs" in data:
                if data["total_count"] != len(data["programs"]):
                    errors.append(
                        f"Total count mismatch: {data['total_count']} != "
                        f"{len(data['programs'])} programs"
                    )
        
        elif category == "target_populations":
            if "total_populations_identified" in data and "populations" in data:
                if data.get("total_populations_identified", 0) != len(data["populations"]):
                    errors.append(
                        f"Population count mismatch: {data.get('total_populations_identified', 0)} != "
                        f"{len(data['populations'])} populations"
                    )
        
        elif category == "funding_sources":
            # Check if at least one funding source is provided
            if "funding_sources" in data and not data["funding_sources"]:
                errors.append("No funding sources identified")
        
        elif category == "effectiveness_outcomes":
            if "has_specific_targets" in data and data["has_specific_targets"]:
                # Check if any goals have targets
                if "outcome_goals" in data:
                    has_targets = any(goal.get("target") for goal in data["outcome_goals"])
                    if not has_targets:
                        errors.append("has_specific_targets is true but no targets found in goals")
        
        elif category == "workforce_support":
            # Validate sub-dictionaries
            if "workforce_training" in data:
                if not isinstance(data["workforce_training"].get("has_training_plan"), bool):
                    errors.append("workforce_training.has_training_plan must be boolean")
                if "training_programs" in data["workforce_training"]:
                    if not isinstance(data["workforce_training"]["training_programs"], list):
                        errors.append("workforce_training.training_programs must be a list")
            if "credentialing" in data:
                if not isinstance(data["credentialing"].get("has_requirements"), bool):
                    errors.append("credentialing.has_requirements must be boolean")
        
        elif category == "monitoring_accountability":
            # Check review_frequency structure
            if "review_frequency" in data and isinstance(data["review_frequency"], dict):
                valid_frequencies = ["monthly", "quarterly", "semiannual", "annual"]
                for freq in data["review_frequency"]:
                    if freq not in valid_frequencies:
                        errors.append(f"Invalid review frequency: {freq}")
        
        return len(errors) == 0, errors
    
    def validate_all_categories(self, extracted_data: Dict) -> Dict:
        """Validate data for all categories.
        
        Args:
            extracted_data: Dictionary with all extracted category data
            
        Returns:
            Dictionary with validation results for each category
        """
        results = {}
        
        for category, data in extracted_data.items():
            if category in ["metadata", "extraction_confidence", "tokens_used", "success", "error"]:
                continue  # Skip non-category fields
                
            is_valid, errors = self.validate_extraction(category, data)
            results[category] = {
                "valid": is_valid,
                "errors": errors
            }
        
        return results
    
    def check_completeness(self, extracted_data: Dict) -> Dict:
        """Check overall completeness of extraction.
        
        Args:
            extracted_data: Dictionary with all extracted data
            
        Returns:
            Completeness report
        """
        expected_categories = list(self.validation_rules.keys())
        
        # Get extracted_data from the proper location
        if "extracted_data" in extracted_data:
            category_data = extracted_data["extracted_data"]
        else:
            category_data = extracted_data
            
        present_categories = [
            cat for cat in expected_categories 
            if cat in category_data
        ]
        missing_categories = [
            cat for cat in expected_categories 
            if cat not in category_data
        ]
        
        # Check for empty extractions
        empty_categories = []
        for cat in present_categories:
            if self._is_empty_extraction(cat, category_data[cat]):
                empty_categories.append(cat)
        
        completeness_score = len(present_categories) / len(expected_categories) if expected_categories else 0
        
        return {
            "score": completeness_score,
            "expected_categories": len(expected_categories),
            "present_categories": len(present_categories),
            "missing_categories": missing_categories,
            "empty_categories": empty_categories,
            "complete": completeness_score == 1.0 and not empty_categories
        }
    
    def _is_empty_extraction(self, category: str, data: Dict) -> bool:
        """Check if an extraction is essentially empty.
        
        Args:
            category: The category name
            data: The extracted data
            
        Returns:
            True if extraction is empty
        """
        if not data:
            return True
        
        # Category-specific empty checks
        if category == "programs_waiting_to_add":
            return data.get("total_count", 0) == 0
        
        elif category == "target_populations":
            return not data.get("populations", [])
        
        elif category == "eligibility_determination":
            return not data.get("screening_tools", []) and not data.get("determination_method")
        
        elif category == "effectiveness_outcomes":
            return not data.get("outcome_goals", [])
        
        elif category == "monitoring_accountability":
            return not data.get("has_monitoring_system", False)
        
        elif category == "workforce_support":
            workforce = data.get("workforce_training", {})
            credentialing = data.get("credentialing", {})
            return not workforce.get("has_training_plan", False) and not credentialing.get("has_requirements", False)
        
        elif category == "funding_sources":
            return not data.get("funding_sources", [])
        
        elif category in ["trauma_informed_delivery", "equity_disparity_reduction", 
                         "structural_determinants"]:
            # These have boolean indicators
            key_field = {
                "trauma_informed_delivery": "uses_trauma_informed_approach",
                "equity_disparity_reduction": "addresses_equity",
                "structural_determinants": "addresses_structural_determinants"
            }[category]
            return not data.get(key_field, False)
        
        return False
    
    def generate_quality_report(self, extracted_data: Dict, 
                              validation_results: Dict = None) -> Dict:
        """Generate a quality report for the extraction.
        
        Args:
            extracted_data: The extracted data
            validation_results: Results from validate_all_categories (optional)
            
        Returns:
            Quality report dictionary
        """
        # Get the actual extracted data
        if "extracted_data" in extracted_data:
            category_data = extracted_data["extracted_data"]
        else:
            category_data = extracted_data
            
        # Run validation if not provided
        if validation_results is None:
            validation_results = self.validate_all_categories(category_data)
            
        completeness = self.check_completeness(extracted_data)
        
        # Count validation errors
        total_errors = sum(
            len(result["errors"]) 
            for result in validation_results.values()
        )
        
        # Calculate quality score
        valid_categories = sum(
            1 for result in validation_results.values() 
            if result["valid"]
        )
        
        if validation_results:
            validation_score = valid_categories / len(validation_results)
        else:
            validation_score = 0
        
        # Combined quality score
        quality_score = (completeness["score"] + validation_score) / 2
        
        return {
            "quality_score": quality_score,
            "completeness": completeness,
            "validation_summary": {
                "total_categories": len(validation_results),
                "valid_categories": valid_categories,
                "total_errors": total_errors
            },
            "category_details": validation_results,
            "recommendations": self._generate_recommendations(
                completeness, validation_results
            )
        }
    
    def _generate_recommendations(self, completeness: Dict, 
                                validation_results: Dict) -> List[str]:
        """Generate recommendations for improving extraction quality.
        
        Args:
            completeness: Completeness check results
            validation_results: Validation results
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if completeness["missing_categories"]:
            recommendations.append(
                f"Extract missing categories: {', '.join(completeness['missing_categories'])}"
            )
        
        if completeness["empty_categories"]:
            recommendations.append(
                f"Review empty categories: {', '.join(completeness['empty_categories'])}"
            )
        
        # Find categories with most errors
        error_categories = [
            (cat, len(result["errors"])) 
            for cat, result in validation_results.items() 
            if result["errors"]
        ]
        
        if error_categories:
            error_categories.sort(key=lambda x: x[1], reverse=True)
            worst_category = error_categories[0][0]
            recommendations.append(
                f"Focus on fixing errors in: {worst_category}"
            )
        
        if completeness["score"] < 0.8:
            recommendations.append(
                "Consider re-running extraction with adjusted prompts"
            )
        
        return recommendations