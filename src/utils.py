"""Utility functions for the FFPSA extraction system."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ffpsa_extraction")


def load_config(config_path: str = "config/extraction_config.json") -> Dict:
    """Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Load environment variables
    load_dotenv()
    
    # Add API key from environment
    api_key_env = "OPENAI_API_KEY" if config["model_config"]["provider"] == "openai" else "ANTHROPIC_API_KEY"
    config["api_key"] = "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"
    
    if not config["api_key"]:
        raise ValueError(f"API key not found in environment: {api_key_env}")
    
    return config


def save_json(data: Any, filepath: str, pretty: bool = True) -> None:
    """Save data as JSON file with proper encoding.
    
    Args:
        data: Data to save
        filepath: Output file path
        pretty: Whether to format JSON for readability
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clean the data by converting to string and back to handle encoding issues
    cleaned_data = json.loads(json.dumps(data, ensure_ascii=True))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=True)
        else:
            json.dump(cleaned_data, f, ensure_ascii=True)


def load_json(filepath: str) -> Any:
    """Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def get_markdown_files(directory: str) -> List[Path]:
    """Get all markdown files in a directory.
    
    Args:
        directory: Directory path
        
    Returns:
        List of Path objects for markdown files
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise ValueError(f"Directory not found: {directory}")
    
    return sorted(dir_path.glob("*.md"))


def estimate_cost(total_tokens: int, model: str = "gpt-4-turbo-preview") -> float:
    """Estimate API cost based on token usage.
    
    Args:
        total_tokens: Total tokens used
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Approximate pricing (update as needed)
    pricing = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},  # per 1K tokens
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # much cheaper
        "gpt-4.1-mini": {"input": 0.00015, "output": 0.0006},  # same as 4o-mini
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015}
    }
    
    if model not in pricing:
        return 0.0
    
    # Rough estimate: 70% input, 30% output
    input_tokens = int(total_tokens * 0.7)
    output_tokens = int(total_tokens * 0.3)
    
    cost = (
        (input_tokens / 1000) * pricing[model]["input"] +
        (output_tokens / 1000) * pricing[model]["output"]
    )
    
    return round(cost, 2)


def create_extraction_summary(results: List[Dict]) -> Dict:
    """Create summary statistics from extraction results.
    
    Args:
        results: List of extraction results
        
    Returns:
        Summary dictionary
    """
    summary = {
        "total_documents": len(results),
        "successful_extractions": sum(1 for r in results if r.get("success", False)),
        "failed_extractions": sum(1 for r in results if not r.get("success", False)),
        "states_processed": list(set(r.get("metadata", {}).get("state", "Unknown") for r in results)),
        "total_tokens_used": sum(r.get("tokens_used", 0) for r in results),
        "extraction_date": datetime.now().isoformat()
    }
    
    # Category completeness
    category_counts = {}
    for result in results:
        if result.get("success"):
            for category in result.get("extracted_data", {}).keys():
                if category not in ["metadata", "extraction_confidence"]:
                    category_counts[category] = category_counts.get(category, 0) + 1
    
    summary["category_completeness"] = {
        cat: f"{count}/{len(results)}" 
        for cat, count in category_counts.items()
    }
    
    # Average confidence scores
    confidence_scores = [
        r.get("extraction_confidence", {}).get("confidence_score", 0)
        for r in results
        if r.get("success")
    ]
    
    if confidence_scores:
        summary["average_confidence"] = round(sum(confidence_scores) / len(confidence_scores), 2)
    
    return summary


def merge_chunks_results(chunk_results: List[Dict], category: str) -> Dict:
    """Merge results from multiple chunks for a category using enhanced prompts structure.
    
    Args:
        chunk_results: List of extraction results from different chunks
        category: The category being extracted
        
    Returns:
        Merged result
    """
    if not chunk_results:
        return {}
    
    # Category-specific merging strategies for enhanced prompts
    if category == "programs_waiting_to_add":
        # Merge programs list, avoiding duplicates
        all_programs = []
        seen_programs = set()
        
        for result in chunk_results:
            for program in result.get("programs", []):
                program_id = program.get("name", "").lower()
                if program_id and program_id not in seen_programs:
                    all_programs.append(program)
                    seen_programs.add(program_id)
        
        return {
            "programs": all_programs,
            "total_count": len(all_programs)
        }
    
    elif category == "target_populations":
        # Merge populations list
        all_populations = []
        seen_pops = set()
        primary_population = None
        
        for result in chunk_results:
            for pop in result.get("populations", []):
                # Use both group and age_range as unique identifier
                pop_id = f"{pop.get('group', '').lower()}_{pop.get('age_range', '')}"
                if pop_id and pop_id not in seen_pops:
                    all_populations.append(pop)
                    seen_pops.add(pop_id)
            
            if not primary_population and result.get("primary_population"):
                primary_population = result["primary_population"]
        
        return {
            "populations": all_populations,
            "primary_population": primary_population or "",
            "total_populations_identified": len(all_populations)
        }
    
    elif category == "eligibility_determination":
        # Merge eligibility information
        all_tools = []
        all_quotes = []
        determination_method = ""
        decision_maker = ""
        candidacy_definition = ""
        eligibility_duration = ""
        
        for result in chunk_results:
            all_tools.extend([t for t in result.get("screening_tools", []) if t not in all_tools])
            all_quotes.extend([q for q in result.get("quotes", []) if q not in all_quotes])
            
            if not determination_method and result.get("determination_method"):
                determination_method = result["determination_method"]
            if not decision_maker and result.get("decision_maker"):
                decision_maker = result["decision_maker"]
            if not candidacy_definition and result.get("candidacy_definition"):
                candidacy_definition = result["candidacy_definition"]
            if not eligibility_duration and result.get("eligibility_duration"):
                eligibility_duration = result["eligibility_duration"]
        
        # Limit quotes to best 5
        return {
            "determination_method": determination_method,
            "screening_tools": all_tools,
            "decision_maker": decision_maker,
            "candidacy_definition": candidacy_definition,
            "eligibility_duration": eligibility_duration,
            "quotes": all_quotes[:5]
        }
    
    elif category == "effectiveness_outcomes":
        # Already full-context, but handle if needed
        all_goals = []
        seen_goals = set()
        has_specific_targets = False
        evaluation_approach = ""
        
        for result in chunk_results:
            if result.get("has_specific_targets"):
                has_specific_targets = True
            if not evaluation_approach and result.get("evaluation_approach"):
                evaluation_approach = result["evaluation_approach"]
                
            for goal in result.get("outcome_goals", []):
                goal_id = goal.get("goal", "").lower()
                if goal_id and goal_id not in seen_goals:
                    all_goals.append(goal)
                    seen_goals.add(goal_id)
        
        return {
            "outcome_goals": all_goals,
            "has_specific_targets": has_specific_targets,
            "evaluation_approach": evaluation_approach
        }
    
    elif category == "monitoring_accountability":
        # Merge monitoring information
        has_monitoring = False
        cqi_mentioned = False
        cqi_details = ""
        fidelity_monitoring = False
        fidelity_details = ""
        monitoring_desc = ""
        external_evaluator = ""
        accountability_roles = []
        all_quotes = []
        review_frequency = {
            "monthly": [],
            "quarterly": [],
            "semiannual": [],
            "annual": []
        }
        
        for result in chunk_results:
            if result.get("has_monitoring_system"):
                has_monitoring = True
            if result.get("cqi_mentioned"):
                cqi_mentioned = True
            if not cqi_details and result.get("cqi_details"):
                cqi_details = result["cqi_details"]
            if result.get("fidelity_monitoring"):
                fidelity_monitoring = True
            if not fidelity_details and result.get("fidelity_details"):
                fidelity_details = result["fidelity_details"]
            if not monitoring_desc and result.get("monitoring_description"):
                monitoring_desc = result["monitoring_description"]
            if not external_evaluator and result.get("external_evaluator"):
                external_evaluator = result["external_evaluator"]
                
            # Merge review frequencies
            if "review_frequency" in result:
                for freq, items in result["review_frequency"].items():
                    if freq in review_frequency:
                        review_frequency[freq].extend([i for i in items if i not in review_frequency[freq]])
                        
            accountability_roles.extend([r for r in result.get("accountability_roles", []) if r not in accountability_roles])
            all_quotes.extend([q for q in result.get("quotes", []) if q not in all_quotes])
        
        return {
            "has_monitoring_system": has_monitoring,
            "cqi_mentioned": cqi_mentioned,
            "cqi_details": cqi_details,
            "fidelity_monitoring": fidelity_monitoring,
            "fidelity_details": fidelity_details,
            "review_frequency": review_frequency,
            "monitoring_description": monitoring_desc,
            "accountability_roles": accountability_roles,
            "external_evaluator": external_evaluator,
            "quotes": all_quotes[:8]  # Limit to 8 quotes
        }
    
    elif category == "workforce_support":
        # Merge workforce and credentialing info
        has_training = False
        training_programs = []
        implementation_support = []
        university_partnerships = []
        training_quotes = []
        
        has_credentials = False
        requirements_by_program = {}
        general_requirements = []
        cred_quotes = []
        
        for result in chunk_results:
            workforce = result.get("workforce_training", {})
            if workforce.get("has_training_plan"):
                has_training = True
                
            # Merge training programs
            for program in workforce.get("training_programs", []):
                if not any(p.get("name") == program.get("name") for p in training_programs):
                    training_programs.append(program)
                    
            implementation_support.extend([s for s in workforce.get("implementation_support", []) if s not in implementation_support])
            university_partnerships.extend([u for u in workforce.get("university_partnerships", []) if u not in university_partnerships])
            training_quotes.extend([q for q in workforce.get("quotes", []) if q not in training_quotes])
            
            credentialing = result.get("credentialing", {})
            if credentialing.get("has_requirements"):
                has_credentials = True
                
            # Merge requirements by program
            for prog, reqs in credentialing.get("requirements_by_program", {}).items():
                if prog not in requirements_by_program:
                    requirements_by_program[prog] = []
                requirements_by_program[prog].extend([r for r in reqs if r not in requirements_by_program[prog]])
                
            general_requirements.extend([r for r in credentialing.get("general_requirements", []) if r not in general_requirements])
            cred_quotes.extend([q for q in credentialing.get("quotes", []) if q not in cred_quotes])
        
        return {
            "workforce_training": {
                "has_training_plan": has_training,
                "training_programs": training_programs,
                "implementation_support": implementation_support,
                "university_partnerships": university_partnerships,
                "quotes": training_quotes[:5]
            },
            "credentialing": {
                "has_requirements": has_credentials,
                "requirements_by_program": requirements_by_program,
                "general_requirements": general_requirements,
                "quotes": cred_quotes[:3]
            }
        }
    
    elif category == "funding_sources":
        # Merge funding sources
        all_sources = []
        seen_sources = set()
        match_requirements = []
        
        for result in chunk_results:
            for source in result.get("funding_sources", []):
                source_name = source.get("source", "").lower()
                if source_name and source_name not in seen_sources:
                    all_sources.append(source)
                    seen_sources.add(source_name)
                    
            match_requirements.extend([m for m in result.get("match_requirements", []) if m not in match_requirements])
        
        return {
            "funding_sources": all_sources,
            "has_multiple_sources": len(all_sources) > 1,
            "match_requirements": match_requirements
        }
    
    elif category == "trauma_informed_delivery":
        # Merge trauma-informed info
        uses_trauma = False
        trauma_programs = []
        training_components = []
        all_quotes = []
        
        for result in chunk_results:
            if result.get("uses_trauma_informed_approach"):
                uses_trauma = True
            trauma_programs.extend([p for p in result.get("trauma_specific_programs", []) if p not in trauma_programs])
            training_components.extend([t for t in result.get("training_components", []) if t not in training_components])
            all_quotes.extend([q for q in result.get("evidence_quotes", []) if q not in all_quotes])
        
        return {
            "uses_trauma_informed_approach": uses_trauma,
            "trauma_specific_programs": trauma_programs,
            "training_components": training_components,
            "evidence_quotes": all_quotes[:5]
        }
    
    elif category == "equity_disparity_reduction":
        # Already full-context, but handle if needed
        addresses_equity = False
        explicit_equity = False
        approach = ""
        groups = []
        strategies = []
        parent_voice = []
        quotes = []
        
        for result in chunk_results:
            if result.get("addresses_equity"):
                addresses_equity = True
            if result.get("explicit_equity_focus"):
                explicit_equity = True
            if not approach and result.get("equity_approach"):
                approach = result["equity_approach"]
            groups.extend([g for g in result.get("targeted_groups", []) if g not in groups])
            strategies.extend([s for s in result.get("strategies", []) if s not in strategies])
            parent_voice.extend([p for p in result.get("parent_voice_mechanisms", []) if p not in parent_voice])
            quotes.extend([q for q in result.get("quotes", []) if q not in quotes])
        
        return {
            "addresses_equity": addresses_equity,
            "explicit_equity_focus": explicit_equity,
            "equity_approach": approach,
            "targeted_groups": groups,
            "strategies": strategies,
            "parent_voice_mechanisms": parent_voice,
            "quotes": quotes[:5]
        }
    
    elif category == "structural_determinants":
        # Already full-context, but handle if needed
        addresses_structural = False
        direct_services = []
        referral_services = []
        support_types = []
        specific_programs = {}
        quotes = []
        
        for result in chunk_results:
            if result.get("addresses_structural_determinants"):
                addresses_structural = True
            direct_services.extend([d for d in result.get("direct_services", []) if d not in direct_services])
            referral_services.extend([r for r in result.get("referral_services", []) if r not in referral_services])
            support_types.extend([s for s in result.get("support_types", []) if s not in support_types])
            
            # Merge specific programs
            for prog, supports in result.get("specific_programs", {}).items():
                if prog not in specific_programs:
                    specific_programs[prog] = []
                specific_programs[prog].extend([s for s in supports if s not in specific_programs[prog]])
                
            quotes.extend([q for q in result.get("quotes", []) if q not in quotes])
        
        return {
            "addresses_structural_determinants": addresses_structural,
            "direct_services": direct_services,
            "referral_services": referral_services,
            "support_types": support_types,
            "specific_programs": specific_programs,
            "quotes": quotes[:5]
        }
    
    else:
        # Default: return first non-empty result
        for result in chunk_results:
            if result:
                return result
        return {}


def merge_dict_recursive(dict1: Dict, dict2: Dict) -> Dict:
    """Recursively merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dict_recursive(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            # Merge lists without duplicates
            for item in value:
                if item not in result[key]:
                    result[key].append(item)
        else:
            result[key] = value
    
    return result


def format_extraction_for_display(extraction: Dict) -> str:
    """Format extraction results for human-readable display.
    
    Args:
        extraction: Extraction results dictionary
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Metadata
    metadata = extraction.get("metadata", {})
    lines.append(f"State: {metadata.get('state', 'Unknown')}")
    lines.append(f"Document: {metadata.get('filename', 'Unknown')}")
    lines.append(f"Date: {metadata.get('document_date', 'Not found')}")
    lines.append("=" * 50)
    
    # Categories
    for category, data in extraction.get("extracted_data", {}).items():
        if category in ["metadata", "extraction_confidence"]:
            continue
            
        lines.append(f"\n{category.upper().replace('_', ' ')}:")
        lines.append("-" * 30)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and value:
                    lines.append(f"{key}: {len(value)} items")
                elif isinstance(value, bool):
                    lines.append(f"{key}: {'Yes' if value else 'No'}")
                elif value:
                    lines.append(f"{key}: {str(value)[:100]}...")
        
        lines.append("")
    
    # Confidence
    confidence = extraction.get("extraction_confidence", {})
    lines.append(f"\nConfidence Score: {confidence.get('confidence_score', 'N/A')}/10")
    lines.append(f"Categories Extracted: {confidence.get('categories_extracted', 'N/A')}")
    
    return "\n".join(lines)


def validate_environment() -> bool:
    """Validate that required environment variables are set.
    
    Returns:
        True if all required variables are set
    """
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY", "LLAMA_CLOUD_API_KEY"]
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("Please add them to your .env file")
        return False
    
    return True