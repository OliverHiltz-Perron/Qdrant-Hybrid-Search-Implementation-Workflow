"""
LLM Processor using Instructor for structured output validation
Implements retry logic and Pydantic validation as per Validation.md requirements
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import instructor
from openai import OpenAI
from pydantic import ValidationError, BaseModel
import time

from config import config
from validation_models import TASK_MODELS
from prompt_manager import PromptManager


def setup_instructor_client(logger) -> instructor.Instructor:
    """Initialize OpenAI client with Instructor patching"""
    base_client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Patch the client with instructor for structured outputs
    client = instructor.from_openai(base_client)
    
    logger.info("Initialized Instructor-patched OpenAI client")
    return client


def process_with_llm_instructor(
    chunks: List[Dict],
    task_type: str,
    state_code: str,
    prompt_manager: PromptManager,
    logger,
    max_retries: int = 3
) -> Dict:
    """
    Process chunks with LLM using Instructor for validation and retries
    
    Args:
        chunks: List of document chunks to process
        task_type: Type of extraction task
        state_code: State code being processed
        prompt_manager: PromptManager instance for getting prompts
        logger: Logger instance
        max_retries: Maximum number of retries for validation failures
        
    Returns:
        Dictionary containing extraction results with metadata
    """
    logger.info(f"Processing {len(chunks)} chunks with Instructor-based LLM for {task_type}")
    
    # Get LLM prompt
    prompts = prompt_manager.get_all_prompts(task_type, logger)
    llm_prompt = prompts.get('llm', '')
    if not llm_prompt:
        logger.error(f"No LLM prompt found for task: {task_type}")
        raise ValueError(f"No LLM prompt found for task: {task_type}")
    
    # Get validation model
    if task_type not in TASK_MODELS:
        logger.error(f"No validation model found for task: {task_type}")
        raise ValueError(f"No validation model found for task: {task_type}")
    
    validator_model = TASK_MODELS[task_type]
    
    # Prepare chunks content
    chunks_content = []
    for i, chunk in enumerate(chunks):
        chunk_text = f"[Chunk {i+1} - {chunk['chunk_id']}]\n"
        chunk_text += f"Section: {chunk['metadata']['section_path']}\n"
        chunk_text += f"Content:\n{chunk['content']}\n"
        chunk_text += "-" * 80 + "\n"
        chunks_content.append(chunk_text)
    
    full_chunks_text = "\n".join(chunks_content)
    
    # Create the full prompt
    full_prompt = f"{llm_prompt}\n\nState: {state_code}\n\nChunks to analyze:\n\n{full_chunks_text}"
    
    # Calculate token usage (approximate)
    approx_tokens = len(full_prompt.split()) * 1.3
    logger.info(f"Approximate prompt tokens: {int(approx_tokens)}")
    
    if approx_tokens > 120000:
        logger.warning(f"Prompt may be too long ({int(approx_tokens)} tokens). Consider reducing chunks.")
    
    # Initialize Instructor client
    client = setup_instructor_client(logger)
    
    # Prepare messages with caching
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are a helpful assistant that extracts structured information from government documents. Follow the exact schema requirements and use null for missing data, not placeholder strings.",
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": full_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        }
    ]
    
    # Attempt extraction with retries using Instructor
    start_time = time.time()
    last_error = None
    
    try:
        # Use instructor's built-in retry mechanism
        logger.info(f"Calling OpenAI with Instructor validation (max retries: {max_retries})")
        
        response = client.chat.completions.create(
            model=config.GPT_MODEL,
            response_model=validator_model,  # Instructor will validate against this model
            messages=messages,
            temperature=0.1,  # As per Validation.md requirement
            max_tokens=4000,
            max_retries=max_retries,  # Instructor's built-in retry
        )
        
        # Log cache usage if available
        if hasattr(response, '_raw_response'):
            raw = response._raw_response
            if hasattr(raw, 'usage') and hasattr(raw.usage, 'prompt_tokens_details'):
                if hasattr(raw.usage.prompt_tokens_details, 'cached_tokens'):
                    cached_tokens = raw.usage.prompt_tokens_details.cached_tokens
                    total_prompt_tokens = raw.usage.prompt_tokens
                    if total_prompt_tokens > 0:
                        logger.info(f"Cache hit: {cached_tokens}/{total_prompt_tokens} tokens cached ({cached_tokens*100/total_prompt_tokens:.1f}%)")
        
        # Response is already validated by Instructor
        llm_output = response.model_dump()
        
        logger.info(f"LLM extraction completed and validated successfully in {time.time() - start_time:.2f}s")
        
        # Add metadata
        llm_result = {
            "state_code": state_code,
            "task_type": task_type,
            "extraction_timestamp": datetime.now().isoformat(),
            "model_used": config.GPT_MODEL,
            "chunks_processed": len(chunks),
            "chunk_ids": [chunk['chunk_id'] for chunk in chunks],
            "extraction": llm_output,
            "validation_status": "success",
            "processing_time": time.time() - start_time
        }
        
        return llm_result
        
    except ValidationError as ve:
        # This should rarely happen with Instructor's retries
        logger.error(f"Validation failed after {max_retries} retries: {ve}")
        last_error = str(ve)
        
    except Exception as e:
        logger.error(f"Error during Instructor LLM processing: {e}")
        last_error = str(e)
    
    # If we get here, all attempts failed - return empty structure
    logger.warning(f"All attempts failed. Last error: {last_error}. Returning empty structure.")
    
    # Return empty structure based on task type
    empty_structures = {
        "TraumaInformed": {"trauma_informed_programs": []},
        "PreventionPrograms": {"prevention_programs": []},
        "CommunityEngagement": {
            "stakeholders_involved": [],
            "engagement_methods": [],
            "governance_structures": []
        },
        "NonReimbursablePrograms": {"non_reimbursable_programs": [{
            "program_name": None,
            "non_reimbursable_reason": None,
            "future_timeline": None,
            "reference": "No non-reimbursable programs found in provided chunks"
        }]},
        "TargetPopulations": {
            "overall_plan_population": {"description": None, "reference": None},
            "program_populations": []
        },
        "WorkforceSupport": {
            "training_plans": [],
            "ongoing_support": [],
            "credentialing_requirements": []
        },
        "EligibilityDetermination": {
            "determination_process": {"description": None, "reference": None},
            "tools_used": [],
            "determination_authority": None
        },
        "FundingSources": {
            "funding_sources": None,
            "reference": None,
            "additional_notes": None
        },
        "CandidateDefinition": {
            "candidacy_definition": None,
            "reference": None,
            "additional_notes": None
        }
    }
    
    llm_output = empty_structures.get(task_type, {"description": None, "reference": None})
    
    # Add metadata with error info
    llm_result = {
        "state_code": state_code,
        "task_type": task_type,
        "extraction_timestamp": datetime.now().isoformat(),
        "model_used": config.GPT_MODEL,
        "chunks_processed": len(chunks),
        "chunk_ids": [chunk['chunk_id'] for chunk in chunks],
        "extraction": llm_output,
        "validation_status": "failed",
        "error": f"All attempts failed: {last_error}",
        "processing_time": time.time() - start_time
    }
    
    return llm_result