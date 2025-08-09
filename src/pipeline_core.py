"""
Complete End-to-End Pipeline: Search → Rerank → LLM
Processes a state through all stages with JSON output at each step
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
from openai import OpenAI
from fastembed import SparseTextEmbedding
from dotenv import load_dotenv

from qdrant_client import QdrantClient, models
from qdrant_client.models import NamedVector, NamedSparseVector, SparseVector

import config
from prompt_manager import PromptManager
from validation_models import TASK_MODELS
from pydantic import ValidationError
from llm_processor import process_with_llm_instructor

# Import reranking functionality
import requests

# Load environment variables
load_dotenv()

def setup_logging(task_name: str, state_code: str):
    """Setup logging for this script"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = config.LOG_DIR / f"complete_pipeline_{state_code}_{task_name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOGGING_CONFIG['format'],
        datefmt=config.LOGGING_CONFIG['datefmt'],
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_file}")
    return logger

def initialize_clients(logger):
    """Initialize Qdrant and OpenAI clients"""
    logger.info("Initializing clients...")
    
    # Get Qdrant URL from environment
    qdrant_url = os.getenv('QDRANT_URL', 'http://127.0.0.1:6333')
    
    # Qdrant client
    try:
        qdrant_client = QdrantClient(url=qdrant_url)
        collections = qdrant_client.get_collections()
        logger.info(f"Connected to Qdrant at {qdrant_url}. Available collections: {[col.name for col in collections.collections]}")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        raise
    
    # OpenAI client
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    logger.info("Initialized OpenAI client")
    
    return qdrant_client, openai_client

def generate_embeddings(query: str, logger) -> Tuple[List[float], any]:
    """Generate both dense and sparse embeddings for query"""
    logger.info("Generating embeddings for query...")
    
    # Dense embedding (OpenAI)
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    try:
        response = client.embeddings.create(
            input=query,
            model=config.EMBEDDING_MODEL
        )
        dense_embedding = response.data[0].embedding
        logger.info(f"Generated dense embedding of dimension {len(dense_embedding)}")
    except Exception as e:
        logger.error(f"Error generating dense embedding: {e}")
        raise
    
    # Sparse embedding (BM25)
    model = SparseTextEmbedding(
        model_name="Qdrant/bm25",
        cache_dir=str(config.BASE_DIR / "models")
    )
    
    embeddings = list(model.embed([query]))
    sparse_embedding = embeddings[0]
    logger.info(f"Generated sparse embedding with {len(sparse_embedding.indices)} non-zero values")
    
    return dense_embedding, sparse_embedding

def perform_hybrid_search(client, collection_name, dense_embedding, sparse_embedding, 
                         n_results, logger, semantic_weight=0.7, bm25_weight=0.3):
    """Perform hybrid search combining semantic and BM25"""
    logger.info(f"Performing hybrid search on collection: {collection_name}")
    logger.info(f"Weights - Semantic: {semantic_weight}, BM25: {bm25_weight}")
    
    # Prepare sparse vector for Qdrant
    sparse_vector = SparseVector(
        indices=sparse_embedding.indices.tolist(),
        values=sparse_embedding.values.tolist()
    )
    
    try:
        # Perform both searches using search_batch (like the working hybrid_search_qdrant.py)
        results = client.search_batch(
            collection_name=collection_name,
            requests=[
                # Dense (semantic) search
                models.SearchRequest(
                    vector=models.NamedVector(
                        name="dense",
                        vector=dense_embedding
                    ),
                    limit=n_results,
                    with_payload=True
                ),
                # Sparse (BM25) search
                models.SearchRequest(
                    vector=models.NamedSparseVector(
                        name="sparse",
                        vector=models.SparseVector(
                            indices=sparse_embedding.indices.tolist(),
                            values=sparse_embedding.values.tolist()
                        )
                    ),
                    limit=n_results,
                    with_payload=True
                )
            ]
        )
        
        # Combine results with weighted scoring
        combined_results = combine_search_results(
            results[0],  # semantic results
            results[1],  # BM25 results
            semantic_weight,
            bm25_weight,
            logger
        )
        
        logger.info(f"Found {len(combined_results)} combined results")
        return combined_results
        
    except Exception as e:
        logger.error(f"Error during hybrid search: {e}")
        raise

def combine_search_results(semantic_results, bm25_results, semantic_weight, bm25_weight, logger):
    """Combine semantic and BM25 results with weighted scoring"""
    # Create dictionaries for easy lookup
    semantic_scores = {point.id: point.score for point in semantic_results}
    bm25_scores = {point.id: point.score for point in bm25_results}
    
    # Get all unique IDs
    all_ids = set(semantic_scores.keys()) | set(bm25_scores.keys())
    
    # Combine scores
    combined_scores = {}
    point_data = {}
    
    # Store point data from both result sets
    for point in semantic_results:
        point_data[point.id] = point
    for point in bm25_results:
        if point.id not in point_data:
            point_data[point.id] = point
    
    # Calculate combined scores
    for point_id in all_ids:
        semantic_score = semantic_scores.get(point_id, 0.0)
        bm25_score = bm25_scores.get(point_id, 0.0)
        
        # Weighted combination
        combined_score = (semantic_score * semantic_weight) + (bm25_score * bm25_weight)
        combined_scores[point_id] = combined_score
    
    # Sort by combined score
    sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    
    # Create combined results in the same format as qdrant results
    class CombinedResult:
        def __init__(self, point_id, score, payload):
            self.id = point_id
            self.score = score
            self.payload = payload
    
    combined_results = []
    for point_id in sorted_ids:
        point = point_data[point_id]
        result = CombinedResult(
            point_id=point_id,
            score=combined_scores[point_id],
            payload=point.payload
        )
        combined_results.append(result)
    
    logger.info(f"Combined {len(semantic_results)} semantic and {len(bm25_results)} BM25 results into {len(combined_results)} unique results")
    
    return combined_results

def rerank_with_jina(query: str, rerank_query: str, documents: List[Dict], logger):
    """Rerank documents using Jina AI reranker"""
    logger.info("Starting reranking with Jina AI...")
    logger.info(f"Rerank query: {rerank_query[:100]}...")
    
    if not config.JINA_API_KEY:
        logger.warning("JINA_API_KEY not found, skipping reranking")
        return documents
    
    # Prepare documents for Jina
    jina_documents = []
    for doc in documents:
        jina_documents.append({
            'text': doc['content'],
            'index': doc['rank'] - 1  # Jina uses 0-based indexing
        })
    
    # Jina reranking API
    url = 'https://api.jina.ai/v1/rerank'
    headers = {
        'Authorization': f'Bearer {config.JINA_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': config.RERANKER_MODEL,
        'query': rerank_query,  # Use the rerank-specific query
        'documents': [doc['text'] for doc in jina_documents],
        'top_n': len(documents)  # Rerank all documents
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        rerank_results = response.json()
        logger.info(f"Reranking completed successfully")
        
        # Reorder documents based on reranking
        reranked_docs = []
        for i, result in enumerate(rerank_results['results']):
            original_idx = result['index']
            original_doc = documents[original_idx].copy()
            original_doc['rerank_score'] = result['relevance_score']
            original_doc['original_rank'] = original_doc['rank']
            original_doc['rank'] = i + 1
            reranked_docs.append(original_doc)
        
        return reranked_docs
        
    except Exception as e:
        logger.error(f"Error during reranking: {e}")
        return documents  # Return original order if reranking fails

def format_results(qdrant_results, query, state_code, stage="initial"):
    """Format Qdrant results into output format"""
    formatted_results = []
    
    for i, result in enumerate(qdrant_results):
        payload = result.payload
        
        formatted_result = {
            'rank': i + 1,
            'score': result.score,
            'chunk_id': payload.get('chunk_id', f'unknown_{i}'),
            'content': payload.get('content', ''),
            'metadata': {
                'section_path': payload.get('section_path', ''),
                'primary_section': payload.get('primary_section', ''),
                'chunk_index': payload.get('chunk_index', i),
                'token_count': payload.get('token_count', 0),
                'state': payload.get('state', state_code)
            }
        }
        
        formatted_results.append(formatted_result)
    
    return formatted_results

def process_with_llm(chunks: List[Dict], task_type: str, state_code: str, 
                    prompt_manager: PromptManager, openai_client: OpenAI, logger):
    """Process chunks with LLM to extract structured information"""
    logger.info(f"Processing {len(chunks)} chunks with LLM...")
    
    # Get LLM prompt
    prompts = prompt_manager.get_all_prompts(task_type, logger)
    llm_prompt = prompts.get('llm', '')
    if not llm_prompt:
        logger.error(f"No LLM prompt found for task: {task_type}")
        raise ValueError(f"No LLM prompt found for task: {task_type}")
    
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
    
    if approx_tokens > 120000:  # Leave some buffer
        logger.warning(f"Prompt may be too long ({int(approx_tokens)} tokens). Consider reducing chunks.")
    
    # Retry logic - attempt up to 3 times
    max_attempts = 3
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Call OpenAI with prompt caching
            logger.info(f"Calling OpenAI API with caching... (Attempt {attempt}/{max_attempts})")
            
            # Prepare messages with caching for system and context
            messages = [
                {
                    "role": "system", 
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a helpful assistant that extracts structured information from government documents.",
                            "cache_control": {"type": "ephemeral"}  # Cache the system message
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt,
                            "cache_control": {"type": "ephemeral"}  # Cache the prompt including context
                        }
                    ]
                }
            ]
            
            response = openai_client.chat.completions.create(
                model=config.GPT_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=4000,  # Reasonable default for structured extraction
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_output = json.loads(response.choices[0].message.content)
            
            # Log cache usage if available
            if hasattr(response, 'usage') and hasattr(response.usage, 'prompt_tokens_details'):
                if hasattr(response.usage.prompt_tokens_details, 'cached_tokens'):
                    cached_tokens = response.usage.prompt_tokens_details.cached_tokens
                    total_prompt_tokens = response.usage.prompt_tokens
                    logger.info(f"Cache hit: {cached_tokens}/{total_prompt_tokens} tokens cached ({cached_tokens*100/total_prompt_tokens:.1f}%)")
            
            # Validate output using Pydantic model if available
            if task_type in TASK_MODELS:
                try:
                    validator = TASK_MODELS[task_type]
                    validated_output = validator(**llm_output)
                    llm_output = validated_output.model_dump()
                    logger.info(f"LLM output validated successfully using {validator.__name__}")
                except ValidationError as ve:
                    logger.warning(f"Validation error on attempt {attempt}: {ve}")
                    if attempt < max_attempts:
                        logger.info(f"Retrying with same prompt in {attempt * 2} seconds...")
                        time.sleep(attempt * 2)
                        continue
                    else:
                        logger.error(f"Validation failed after {max_attempts} attempts. Using raw output.")
                        # Continue with unvalidated output
            else:
                logger.warning(f"No validation model found for task type: {task_type}")
            
            # Check if the response is empty or missing expected content
            if not llm_output or (isinstance(llm_output, dict) and not any(llm_output.values())):
                logger.warning(f"Empty or invalid LLM response on attempt {attempt}")
                if attempt < max_attempts:
                    logger.info(f"Retrying in {attempt * 2} seconds...")
                    time.sleep(attempt * 2)  # Exponential backoff
                    continue
                else:
                    logger.warning("All retry attempts resulted in empty responses - using default empty structure")
                    # Return empty structure based on task type
                    if task_type == "TraumaInformed":
                        llm_output = {"trauma_informed_programs": []}
                    elif task_type == "PreventionPrograms":
                        llm_output = {"prevention_programs": []}
                    elif task_type == "CommunityEngagement":
                        llm_output = {"stakeholders_involved": [], "engagement_methods": [], "governance_structures": []}
                    elif task_type == "NonReimbursablePrograms":
                        llm_output = {"non_reimbursable_programs": []}
                    elif task_type == "TargetPopulations":
                        llm_output = {"overall_plan_population": {"description": "Not found", "reference": None}, "program_populations": []}
                    elif task_type == "WorkforceSupport":
                        llm_output = {"training_plans": [], "ongoing_support": [], "credentialing_requirements": []}
                    elif task_type == "EligibilityDetermination":
                        llm_output = {"determination_process": {"description": "Not found", "reference": None}, "tools_used": [], "determination_authority": {"description": "Not found", "reference": None}}
                    else:
                        # Generic empty structure for other tasks
                        llm_output = {"description": "No information found", "reference": None}
            
            # Add metadata
            llm_result = {
                "state_code": state_code,
                "task_type": task_type,
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": config.GPT_MODEL,
                "chunks_processed": len(chunks),
                "chunk_ids": [chunk['chunk_id'] for chunk in chunks],
                "extraction": llm_output,
                "retry_attempts": attempt - 1  # Number of retries (0 if successful on first try)
            }
            
            logger.info(f"LLM extraction completed successfully on attempt {attempt}")
            return llm_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response on attempt {attempt}: {e}")
            last_error = e
            if attempt < max_attempts:
                logger.info(f"Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)
            
        except Exception as e:
            logger.error(f"Error during LLM processing on attempt {attempt}: {e}")
            last_error = e
            if attempt < max_attempts:
                logger.info(f"Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)
    
    # If we get here, all attempts failed - return empty structure
    logger.warning(f"All {max_attempts} LLM attempts failed. Last error: {last_error}. Returning empty structure.")
    
    # Return empty structure based on task type
    if task_type == "TraumaInformed":
        llm_output = {"trauma_informed_programs": []}
    elif task_type == "PreventionPrograms":
        llm_output = {"prevention_programs": []}
    elif task_type == "CommunityEngagement":
        llm_output = {"stakeholders_involved": [], "engagement_methods": [], "governance_structures": []}
    elif task_type == "NonReimbursablePrograms":
        llm_output = {"non_reimbursable_programs": []}
    elif task_type == "TargetPopulations":
        llm_output = {"overall_plan_population": {"description": "Not found", "reference": None}, "program_populations": []}
    elif task_type == "WorkforceSupport":
        llm_output = {"training_plans": [], "ongoing_support": [], "credentialing_requirements": []}
    elif task_type == "EligibilityDetermination":
        llm_output = {"determination_process": {"description": "Not found", "reference": None}, "tools_used": [], "determination_authority": {"description": "Not found", "reference": None}}
    else:
        # Generic empty structure for other tasks
        llm_output = {"description": "No information found", "reference": None}
    
    # Add metadata with error info
    llm_result = {
        "state_code": state_code,
        "task_type": task_type,
        "extraction_timestamp": datetime.now().isoformat(),
        "model_used": config.GPT_MODEL,
        "chunks_processed": len(chunks),
        "chunk_ids": [chunk['chunk_id'] for chunk in chunks],
        "extraction": llm_output,
        "retry_attempts": max_attempts,
        "error": f"All attempts failed: {last_error}"
    }
    
    return llm_result

def save_stage_output(data: Dict, stage: str, task_type: str, state_code: str, logger) -> Path:
    """Save output for a specific stage"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{stage}_{state_code}_{task_type}_{timestamp}.json"
    output_file = config.OUTPUT_DIR / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {stage} output to: {output_file}")
    return output_file

def get_all_queries(task_type: str, logger) -> Dict[str, str]:
    """Get all queries (search and rerank) for a task"""
    prompt_manager = PromptManager()
    
    logger.info(f"Loading all prompts for task: {task_type}")
    
    # Get all prompts
    prompts = prompt_manager.get_all_prompts(task_type, logger)
    
    # Combine BM25 and RAG for search query
    keywords = prompt_manager.get_bm25_keywords(task_type, logger)
    rag_query = prompt_manager.get_rag_query(task_type, logger)
    
    keyword_string = ' '.join(keywords)
    search_query = f"{rag_query} {keyword_string}"
    
    # Get reranker query
    rerank_query = prompts.get('reranker', '')
    if not rerank_query:
        logger.warning("No reranker prompt found, using search query for reranking")
        rerank_query = rag_query  # Fallback to RAG query
    
    return {
        'search_query': search_query,
        'rerank_query': rerank_query,
        'bm25_keywords': keyword_string,
        'rag_query': rag_query
    }

def main():
    parser = argparse.ArgumentParser(
        description='Complete pipeline: Search → Rerank → LLM with JSON output at each stage',
        epilog='''Example:
  python complete_pipeline_qdrant.py --value NonReimbursablePrograms --state CA
  
This will:
1. Perform hybrid search and save results
2. Rerank results and save results  
3. Process with LLM and save results
4. Save a final summary with all file paths'''
    )
    
    # Required arguments
    parser.add_argument('--value', required=True, 
                       help='Task type (e.g., NonReimbursablePrograms, FundingSources)')
    parser.add_argument('--state', required=True, help='State code (e.g., CA, TX)')
    
    # Optional arguments
    parser.add_argument('--n-results', type=int, default=config.INITIAL_SEARCH_RESULTS,
                       help=f'Number of results to retrieve (default: {config.INITIAL_SEARCH_RESULTS})')
    parser.add_argument('--n-rerank', type=int, default=config.RERANKED_RESULTS,
                       help=f'Number of results to keep after reranking (default: {config.RERANKED_RESULTS})')
    parser.add_argument('--n-llm', type=int, default=10,
                       help='Number of top results to send to LLM (default: 10)')
    parser.add_argument('--semantic-weight', type=float, default=config.DEFAULT_SEMANTIC_WEIGHT,
                       help=f'Weight for semantic search (default: {config.DEFAULT_SEMANTIC_WEIGHT})')
    parser.add_argument('--bm25-weight', type=float, default=config.DEFAULT_BM25_WEIGHT,
                       help=f'Weight for BM25 search (default: {config.DEFAULT_BM25_WEIGHT})')
    
    args = parser.parse_args()
    
    # Normalize task type
    prompt_manager = PromptManager()
    task_type = prompt_manager.normalize_task_type(args.value)
    
    # Setup logging
    logger = setup_logging(task_type, args.state)
    logger.info("="*80)
    logger.info("COMPLETE PIPELINE: SEARCH → RERANK → LLM")
    logger.info("="*80)
    logger.info(f"Task: {task_type}, State: {args.state}")
    
    try:
        # Initialize clients
        qdrant_client, openai_client = initialize_clients(logger)
        
        # Get collection name
        collection_name = config.get_collection_name(args.state)
        
        # Check if collection exists
        collections = [col.name for col in qdrant_client.get_collections().collections]
        if collection_name not in collections:
            logger.error(f"Collection '{collection_name}' not found")
            raise ValueError(f"Collection not found for state: {args.state}")
        
        # Get all queries
        queries = get_all_queries(task_type, logger)
        logger.info(f"Search query: {queries['search_query'][:100]}...")
        logger.info(f"Rerank query: {queries['rerank_query'][:100]}...")
        
        # Track all output files
        output_files = {}
        
        # ========== STAGE 1: HYBRID SEARCH ==========
        logger.info("\n" + "="*60)
        logger.info("STAGE 1: HYBRID SEARCH")
        logger.info("="*60)
        
        # Generate embeddings
        dense_embedding, sparse_embedding = generate_embeddings(queries['search_query'], logger)
        
        # Perform search
        search_start = time.time()
        qdrant_results = perform_hybrid_search(
            qdrant_client, 
            collection_name, 
            dense_embedding, 
            sparse_embedding,
            args.n_results,
            logger,
            args.semantic_weight,
            args.bm25_weight
        )
        search_time = time.time() - search_start
        
        # Format and save search results
        search_results = format_results(qdrant_results, queries['search_query'], args.state)
        search_output = {
            'stage': 'hybrid_search',
            'task_type': task_type,
            'state_code': args.state,
            'timestamp': datetime.now().isoformat(),
            'query': queries['search_query'],
            'parameters': {
                'semantic_weight': args.semantic_weight,
                'bm25_weight': args.bm25_weight,
                'results_requested': args.n_results
            },
            'timing': {
                'search_time_seconds': round(search_time, 2)
            },
            'total_results': len(search_results),
            'results': search_results
        }
        output_files['search'] = save_stage_output(search_output, 'search', task_type, args.state, logger)
        
        # ========== STAGE 2: RERANKING ==========
        logger.info("\n" + "="*60)
        logger.info("STAGE 2: RERANKING")
        logger.info("="*60)
        
        # Rerank results
        rerank_start = time.time()
        reranked_results = rerank_with_jina(
            queries['search_query'], 
            queries['rerank_query'],
            search_results, 
            logger
        )
        reranked_results = reranked_results[:args.n_rerank]
        rerank_time = time.time() - rerank_start
        
        # Save rerank results
        rerank_output = {
            'stage': 'reranking',
            'task_type': task_type,
            'state_code': args.state,
            'timestamp': datetime.now().isoformat(),
            'rerank_query': queries['rerank_query'],
            'parameters': {
                'initial_results': len(search_results),
                'results_kept': len(reranked_results),
                'reranker_model': config.RERANKER_MODEL
            },
            'timing': {
                'rerank_time_seconds': round(rerank_time, 2)
            },
            'total_results': len(reranked_results),
            'results': reranked_results
        }
        output_files['rerank'] = save_stage_output(rerank_output, 'rerank', task_type, args.state, logger)
        
        # ========== STAGE 3: LLM EXTRACTION ==========
        logger.info("\n" + "="*60)
        logger.info("STAGE 3: LLM EXTRACTION")
        logger.info("="*60)
        
        # Select top chunks for LLM
        llm_chunks = reranked_results[:args.n_llm]
        logger.info(f"Sending top {len(llm_chunks)} chunks to LLM")
        
        # Process with LLM using Instructor for validation
        llm_start = time.time()
        llm_result = process_with_llm_instructor(
            chunks=llm_chunks,
            task_type=task_type,
            state_code=args.state,
            prompt_manager=prompt_manager,
            logger=logger,
            max_retries=3  # As per Validation.md requirement
        )
        llm_time = time.time() - llm_start
        
        # Add timing to LLM result
        llm_result['timing'] = {
            'llm_processing_seconds': round(llm_time, 2)
        }
        
        # Save LLM results
        output_files['llm'] = save_stage_output(llm_result, 'llm', task_type, args.state, logger)
        
        # ========== FINAL SUMMARY ==========
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETE - SUMMARY")
        logger.info("="*60)
        
        # Create summary
        total_time = search_time + rerank_time + llm_time
        summary = {
            'pipeline': 'complete_search_rerank_llm',
            'task_type': task_type,
            'state_code': args.state,
            'completed_timestamp': datetime.now().isoformat(),
            'total_processing_time_seconds': round(total_time, 2),
            'stage_timings': {
                'search_seconds': round(search_time, 2),
                'rerank_seconds': round(rerank_time, 2),
                'llm_seconds': round(llm_time, 2)
            },
            'parameters': {
                'search_results': args.n_results,
                'rerank_results': args.n_rerank,
                'llm_chunks': args.n_llm,
                'semantic_weight': args.semantic_weight,
                'bm25_weight': args.bm25_weight
            },
            'output_files': {
                'search': str(output_files['search']),
                'rerank': str(output_files['rerank']),
                'llm': str(output_files['llm'])
            },
            'extraction_preview': {
                'task_type': task_type,
                'state': args.state,
                'items_extracted': len(llm_result['extraction'].get('items', [])) if 'items' in llm_result['extraction'] else 'N/A'
            }
        }
        
        # Save summary
        summary_file = save_stage_output(summary, 'pipeline_summary', task_type, args.state, logger)
        
        # Print summary to console
        print(f"\n{'='*80}")
        print(f"PIPELINE COMPLETE")
        print(f"{'='*80}")
        print(f"Task: {task_type}")
        print(f"State: {args.state}")
        print(f"\nPerformance:")
        print(f"  - Search: {search_time:.2f}s ({len(search_results)} results)")
        print(f"  - Rerank: {rerank_time:.2f}s ({len(reranked_results)} results)")
        print(f"  - LLM: {llm_time:.2f}s ({len(llm_chunks)} chunks)")
        print(f"  - Total: {total_time:.2f}s")
        print(f"\nOutput Files:")
        print(f"  - Search: {output_files['search'].name}")
        print(f"  - Rerank: {output_files['rerank'].name}")
        print(f"  - LLM: {output_files['llm'].name}")
        print(f"  - Summary: {summary_file.name}")
        print(f"\nAll files saved to: {config.OUTPUT_DIR}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()