"""
Multi-State Combined Pipeline with Incremental Updates and Data Standardization
Processes all states and saves results in state folders with consistent null handling
Updates state summaries incrementally during processing for checkpointing
"""

import argparse
import subprocess
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
import time
from typing import List, Dict, Set, Optional, Any
import shutil

import config

def setup_logging():
    """Setup logging for multi-state processing"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = config.LOG_DIR / f"multi_state_combined_incremental_{timestamp}.log"
    
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

def standardize_value(value: Any) -> Any:
    """
    Standardize a single value according to null handling rules.
    
    Rules:
    - Empty strings -> null
    - "Not specified", "N/A", "None", etc. -> null
    - "No X found" patterns -> null
    - String "null" -> null (actual null datatype)
    - Empty lists remain as []
    - Non-empty values remain unchanged
    """
    if value is None:
        return None
    
    # Handle strings
    if isinstance(value, str):
        # Trim whitespace
        cleaned = value.strip()
        
        # Check for empty or placeholder values (including string "null")
        if not cleaned or cleaned.lower() in [
            "not specified",
            "n/a",
            "na",
            "none",
            "null",  # Added to convert string "null" to actual null
            "not available",
            "not applicable",
            "unknown",
            ""
        ]:
            return None
        
        # Check for "No X found" patterns
        if cleaned.lower().startswith("no ") and cleaned.lower().endswith(" found"):
            return None
        
        # Check for other common patterns
        if cleaned.lower() in ["no information available", "no data", "no information"]:
            return None
            
        return value
    
    # Handle lists
    if isinstance(value, list):
        if len(value) == 0:
            return []  # Empty lists stay as empty lists
        # Recursively standardize list items
        return [standardize_value(item) for item in value]
    
    # Handle dictionaries
    if isinstance(value, dict):
        return standardize_extraction(value, logger=None)
    
    # All other types (numbers, booleans, etc.) remain unchanged
    return value

def standardize_extraction(data: Dict, logger=None) -> Dict:
    """
    Recursively standardize all values in an extraction dictionary.
    
    Args:
        data: Dictionary containing extraction data
        logger: Optional logger for debugging
        
    Returns:
        Dictionary with standardized null values
    """
    if not data:
        return {}
    
    standardized = {}
    
    # Known array fields that should never be null (always array, even if empty)
    array_fields = [
        'non_reimbursable_programs',
        'trauma_informed_programs',
        'prevention_programs',
        'stakeholders_involved',
        'engagement_methods',
        'governance_structures',
        'training_plans',
        'ongoing_support',
        'credentialing_requirements',
        'tools_used',
        'program_populations'
    ]
    
    for key, value in data.items():
        # Skip standardization for reference fields (they contain explanations)
        if key == "reference" and isinstance(value, str):
            standardized[key] = value
        # Handle null array fields - convert to empty array
        elif key in array_fields and value is None:
            standardized[key] = []
            if logger:
                logger.info(f"Converted null {key} to empty array")
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            standardized[key] = standardize_extraction(value, logger)
        elif isinstance(value, list):
            # Process lists (may contain dictionaries or simple values)
            standardized_list = []
            for item in value:
                if isinstance(item, dict):
                    standardized_dict = standardize_extraction(item, logger)
                    # Always keep the structure, even with null values
                    standardized_list.append(standardized_dict)
                else:
                    # For non-dict items, standardize the value
                    standardized_item = standardize_value(item)
                    # Only add non-null simple values
                    if standardized_item is not None:
                        standardized_list.append(standardized_item)
            
            # Always keep the array structure, even if empty or contains nulls
            standardized[key] = standardized_list
        else:
            # Process simple values
            standardized[key] = standardize_value(value)
    
    return standardized

def discover_task_types(logger) -> List[str]:
    """Discover all available task types from prompt files"""
    prompts_dir = Path("Prompts")
    if not prompts_dir.exists():
        logger.error(f"Prompts directory not found: {prompts_dir}")
        return []
    
    task_types = set()
    llm_dir = prompts_dir / "LLM"
    
    if not llm_dir.exists():
        logger.error(f"LLM prompts directory not found: {llm_dir}")
        return []
    
    for prompt_file in llm_dir.glob("*_LLM_Prompt.md"):
        task_type = prompt_file.stem.replace("_LLM_Prompt", "")
        
        required_files = [
            prompts_dir / "BM25" / f"{task_type}_BM25.md",
            prompts_dir / "RAG" / f"{task_type}_RAG.md", 
            prompts_dir / "Reranker" / f"{task_type}_Reranker_Prompt.md",
            prompts_dir / "LLM" / f"{task_type}_LLM_Prompt.md"
        ]
        
        all_exist = all(f.exists() for f in required_files)
        
        if all_exist:
            task_types.add(task_type)
            logger.info(f"Found complete prompt set for: {task_type}")
    
    return sorted(list(task_types))

def get_available_states(logger) -> List[str]:
    """Get all available state collections from Qdrant"""
    try:
        from qdrant_client import QdrantClient
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get Qdrant URL from environment
        qdrant_url = os.getenv('QDRANT_URL', 'http://127.0.0.1:6333')
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections().collections
        
        state_codes = []
        for col in collections:
            # Collections are named like "CA_PreventionPlan"
            if col.name.endswith("_PreventionPlan"):
                state_code = col.name.replace("_PreventionPlan", "")
                state_codes.append(state_code)
        
        logger.info(f"Found {len(state_codes)} state collections: {state_codes}")
        return sorted(state_codes)
        
    except Exception as e:
        logger.error(f"Failed to get state collections: {e}")
        return []

def create_state_folder_structure(base_dir: Path, state: str, logger) -> Path:
    """Create state folder and return its path"""
    state_dir = base_dir / state
    state_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created state folder: {state_dir}")
    return state_dir

def create_task_output_structure(state_dir: Path, task: str) -> Dict[str, Path]:
    """Create and return task output directory structure within state folder"""
    task_dir = state_dir / task
    task_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'dir': task_dir,
        'search': task_dir / 'search.json',
        'rerank': task_dir / 'rerank.json',
        'llm': task_dir / 'llm.json',
        'summary': task_dir / 'pipeline_summary.json'
    }

def initialize_state_summary(state_dir: Path, state: str, tasks: List[str], logger) -> Path:
    """Initialize state summary file"""
    summary_file = state_dir / 'state_summary.json'
    
    initial_data = {
        'state': state,
        'processing_start': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'total_tasks': len(tasks),
        'successful_tasks': 0,
        'failed_tasks': 0,
        'tasks': {}
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2)
    
    logger.info(f"Initialized state summary: {summary_file}")
    return summary_file

def update_state_summary(summary_file: Path, task: str, result: Dict, logger):
    """Update state summary file with task result (with standardization)"""
    # Read existing data
    with open(summary_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Update with new task result
    if result['status'] == 'success' and result.get('llm_extraction'):
        # The LLM extraction already contains all needed fields at top level
        llm_data = result['llm_extraction']
        
        # Standardize the extraction data
        if 'extraction' in llm_data and llm_data['extraction']:
            standardized_extraction = standardize_extraction(llm_data['extraction'], logger)
        else:
            standardized_extraction = {}
        
        data['tasks'][task] = {
            'status': 'success',
            'extraction': standardized_extraction,
            'chunks_processed': llm_data.get('chunks_processed', 0),
            'model_used': llm_data.get('model_used', ''),
            'extraction_timestamp': llm_data.get('extraction_timestamp', ''),
            'processing_duration': result.get('duration_seconds', 0)
        }
    else:
        data['tasks'][task] = {
            'status': result['status'],
            'error': result.get('error', 'No extraction available'),
            'processing_duration': result.get('duration_seconds', 0)
        }
    
    # Update counts
    data['successful_tasks'] = len([t for t in data['tasks'].values() if t['status'] == 'success'])
    data['failed_tasks'] = len([t for t in data['tasks'].values() if t['status'] != 'success'])
    data['last_updated'] = datetime.now().isoformat()
    
    # Write updated data
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated state summary with {task} results (standardized)")

def load_state_checkpoint(state_dir: Path, tasks: List[str], logger) -> Set[str]:
    """Load existing progress from state summary"""
    summary_file = state_dir / 'state_summary.json'
    completed_tasks = set()
    
    if summary_file.exists():
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                completed_tasks = set(data.get('tasks', {}).keys())
                logger.info(f"Loaded checkpoint: {len(completed_tasks)} tasks completed")
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
    
    return completed_tasks

def run_pipeline_for_state_task(state: str, task: str, output_paths: Dict[str, Path], 
                               logger, n_results=50, n_rerank=20, n_llm=20) -> Dict:
    """Run pipeline and organize outputs with standardization"""
    
    logger.info(f"Running {task} for {state}")
    
    cmd = [
        sys.executable,
        'pipeline_core.py',
        '--value', task,
        '--state', state,
        '--n-results', str(n_results),
        '--n-rerank', str(n_rerank),
        '--n-llm', str(n_llm)
    ]
    
    start_time = time.time()
    result = {
        'state': state,
        'task': task,
        'start_time': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = time.time() - start_time
        
        # Extract output file paths from stdout
        temp_files = {}
        for line in process.stdout.split('\n'):
            if '- Search:' in line and '.json' in line:
                temp_files['search'] = line.split(': ')[-1].strip()
            elif '- Rerank:' in line and '.json' in line:
                temp_files['rerank'] = line.split(': ')[-1].strip()
            elif '- LLM:' in line and '.json' in line:
                temp_files['llm'] = line.split(': ')[-1].strip()
            elif '- Summary:' in line and '.json' in line:
                temp_files['summary'] = line.split(': ')[-1].strip()
        
        # Move files to organized structure and standardize LLM output
        for file_type, temp_path in temp_files.items():
            if temp_path:
                # Handle both absolute and relative paths
                temp_file = Path(temp_path)
                if not temp_file.is_absolute():
                    # Check in outputs directory
                    temp_file = Path("outputs") / temp_path
                
                if temp_file.exists():
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Standardize LLM extraction data
                    if file_type == 'llm' and 'extraction' in data:
                        data['extraction'] = standardize_extraction(data['extraction'], logger)
                        logger.info(f"Standardized LLM extraction for {state}/{task}")
                    
                    with open(output_paths[file_type], 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    temp_file.unlink()
                    logger.info(f"Moved and standardized {file_type} file to {output_paths[file_type]}")
                else:
                    logger.warning(f"Could not find {file_type} file at {temp_file}")
        
        # Read standardized LLM extraction
        llm_extraction = None
        if output_paths['llm'].exists():
            with open(output_paths['llm'], 'r', encoding='utf-8') as f:
                llm_extraction = json.load(f)
        
        result.update({
            'status': 'success',
            'duration_seconds': round(duration, 2),
            'output_dir': str(output_paths['dir']),
            'llm_extraction': llm_extraction
        })
        
        logger.info(f"[SUCCESS] Completed {state}/{task} in {duration:.2f}s")
        
    except subprocess.CalledProcessError as e:
        result.update({
            'status': 'failed',
            'duration_seconds': round(time.time() - start_time, 2),
            'error': str(e),
            'stderr': e.stderr,
            'stdout': e.stdout
        })
        logger.error(f"[FAILED] {state}/{task}: {e}")
        if e.stderr:
            logger.error(f"Error stderr: {e.stderr}")
        if e.stdout:
            logger.error(f"Error stdout: {e.stdout}")
        
    except Exception as e:
        result.update({
            'status': 'error',
            'duration_seconds': round(time.time() - start_time, 2),
            'error': str(e)
        })
        logger.error(f"[ERROR] {state}/{task}: {e}")
    
    return result

def create_combined_task_summaries(output_base: Path, states_processed: List[str], 
                                  tasks_processed: List[str], logger):
    """Create combined summaries for each task across all states (with standardization)"""
    combined_dir = output_base / "_combined_by_task"
    combined_dir.mkdir(exist_ok=True)
    
    for task in tasks_processed:
        combined_data = {
            'task': task,
            'timestamp': datetime.now().isoformat(),
            'states': {}
        }
        
        for state in states_processed:
            state_summary_file = output_base / state / 'state_summary.json'
            if state_summary_file.exists():
                with open(state_summary_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    if task in state_data.get('tasks', {}):
                        task_data = state_data['tasks'][task]
                        if task_data.get('status') == 'success' and 'extraction' in task_data:
                            extraction = task_data['extraction']
                            
                            # Standardize the extraction before transforming
                            extraction = standardize_extraction(extraction, logger)
                            
                            # Transform the extraction data into the desired format
                            state_result = {}
                            
                            # Handle different task types with appropriate structure
                            if task == 'CandidateDefinition':
                                state_result['CandidateDefinition'] = {
                                    'description': extraction.get('candidacy_definition'),
                                    'reference': extraction.get('reference')
                                }
                            elif task == 'FundingSources':
                                state_result['FundingSources'] = {
                                    'sources': extraction.get('funding_sources'),
                                    'reference': extraction.get('reference')
                                }
                                if extraction.get('additional_notes'):
                                    state_result['FundingSources']['notes'] = extraction['additional_notes']
                            elif task in ['CommunityEngagement', 'EligibilityDetermination', 'PreventionPrograms',
                                         'NonReimbursablePrograms', 'TraumaInformed', 'WorkforceSupport',
                                         'TargetPopulations']:
                                # These tasks have arrays or complex structures - copy directly
                                state_result = extraction.copy()
                                # Remove the reference key from the top level as it's already in each item
                                state_result.pop('reference', None)
                            else:
                                # Generic handling for other task types (simple key-value pairs)
                                for key, value in extraction.items():
                                    if key not in ['reference', 'additional_notes']:
                                        state_result[key] = {
                                            'description': value if value is not None else None,
                                            'reference': extraction.get('reference')
                                        }
                                if extraction.get('additional_notes'):
                                    state_result['Notes'] = extraction['additional_notes']
                            
                            combined_data['states'][state] = state_result
        
        # Save combined task file
        combined_file = combined_dir / f"{task}_combined.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2)
        logger.info(f"Created standardized combined task summary: {combined_file}")

def create_overall_summary(output_base: Path, states_processed: List[str], 
                          tasks_processed: List[str], logger) -> Dict:
    """Create overall summary from all state summaries"""
    overall = {
        'pipeline': 'multi_state_combined_incremental_standardized',
        'last_updated': datetime.now().isoformat(),
        'states_processed': states_processed,
        'tasks_processed': tasks_processed,
        'total_expected_runs': len(states_processed) * len(tasks_processed),
        'states': {}
    }
    
    total_successful = 0
    total_failed = 0
    
    for state in states_processed:
        state_summary_file = output_base / state / 'state_summary.json'
        if state_summary_file.exists():
            with open(state_summary_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                overall['states'][state] = {
                    'successful_tasks': state_data.get('successful_tasks', 0),
                    'failed_tasks': state_data.get('failed_tasks', 0),
                    'total_tasks': state_data.get('total_tasks', 0)
                }
                total_successful += state_data.get('successful_tasks', 0)
                total_failed += state_data.get('failed_tasks', 0)
    
    overall['overall_statistics'] = {
        'total_successful_runs': total_successful,
        'total_failed_runs': total_failed,
        'completion_percentage': round(100 * (total_successful + total_failed) / overall['total_expected_runs'], 1) if overall['total_expected_runs'] > 0 else 0
    }
    
    # Save overall summary
    summary_file = output_base / 'overall_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, indent=2)
    
    logger.info(f"Created overall summary: {summary_file}")
    
    # Also create combined task summaries
    create_combined_task_summaries(output_base, states_processed, tasks_processed, logger)
    
    return overall

def main():
    parser = argparse.ArgumentParser(
        description='Process all states with incremental updates, state-based folder organization, and data standardization',
        epilog='''Example:
  python multi_state_combined_pipeline_incremental_standardized.py --states CA TX FL
  
Output Structure:
  output_dir/
    CA/
      CandidateDefinition/
        search.json
        rerank.json
        llm.json (standardized with null values)
        pipeline_summary.json
      state_summary.json
    TX/
      ...
    _combined_by_task/
      CandidateDefinition_combined.json
      ...
    overall_summary.json
    
Standardization Rules:
  - Empty strings -> null
  - "Not specified", "N/A" -> null
  - "No X found" patterns -> null
  - Consistent null handling across all outputs'''
    )
    
    parser.add_argument('--states', nargs='+', help='Specific states to process (default: all)')
    parser.add_argument('--tasks', nargs='+', help='Specific tasks to process (default: all)')
    parser.add_argument('--output-dir', type=str, default='multi_state_output_standardized',
                       help='Base output directory (default: multi_state_output_standardized)')
    parser.add_argument('--resume', action='store_true', help='Resume from existing progress')
    parser.add_argument('--n-results', type=int, default=50)
    parser.add_argument('--n-rerank', type=int, default=20)
    parser.add_argument('--n-llm', type=int, default=20)
    
    args = parser.parse_args()
    
    # Setup
    logger = setup_logging()
    output_base = Path(args.output_dir)
    output_base.mkdir(exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"MULTI-STATE COMBINED PIPELINE (STANDARDIZED)")
    print(f"{'='*80}\n")
    
    # Discover available states and tasks
    available_states = get_available_states(logger)
    available_tasks = discover_task_types(logger)
    
    if not available_states or not available_tasks:
        logger.error("No states or tasks available!")
        sys.exit(1)
    
    # Filter requested states/tasks
    states_to_process = args.states if args.states else available_states
    states_to_process = [s for s in states_to_process if s in available_states]
    
    tasks_to_process = args.tasks if args.tasks else available_tasks
    tasks_to_process = [t for t in tasks_to_process if t in available_tasks]
    
    if not states_to_process or not tasks_to_process:
        logger.error("No valid states or tasks to process!")
        sys.exit(1)
    
    total_runs = len(states_to_process) * len(tasks_to_process)
    completed_runs = 0
    
    # Count already completed if resuming
    if args.resume:
        for state in states_to_process:
            state_dir = output_base / state
            if state_dir.exists():
                completed_tasks = load_state_checkpoint(state_dir, tasks_to_process, logger)
                completed_runs += len(completed_tasks)
    
    print(f"\nProcessing {len(states_to_process)} states × {len(tasks_to_process)} tasks")
    print(f"Total runs: {total_runs}")
    if args.resume and completed_runs > 0:
        print(f"Already completed: {completed_runs}")
        print(f"Remaining: {total_runs - completed_runs}")
    print(f"Output directory: {output_base.absolute()}")
    print(f"Data standardization: ENABLED (null handling)\n")
    
    # Process all combinations
    run_count = completed_runs
    start_time = time.time()
    
    for state in states_to_process:
        print(f"\n{'='*60}")
        print(f"STATE: {state}")
        print(f"{'='*60}")
        
        # Create state folder
        state_dir = create_state_folder_structure(output_base, state, logger)
        
        # Initialize or load state summary
        if args.resume:
            completed_tasks = load_state_checkpoint(state_dir, tasks_to_process, logger)
        else:
            completed_tasks = set()
        
        state_summary_file = initialize_state_summary(state_dir, state, tasks_to_process, logger)
        state_has_work = False
        
        for task in tasks_to_process:
            # Skip if already completed
            if args.resume and task in completed_tasks:
                logger.info(f"Skipping {state}/{task} - already completed")
                continue
            
            state_has_work = True
            run_count += 1
            print(f"\n[{run_count}/{total_runs}] Processing: {state} / {task}")
            
            # Create task output structure
            output_paths = create_task_output_structure(state_dir, task)
            
            # Run pipeline
            result = run_pipeline_for_state_task(
                state, task, output_paths, logger,
                args.n_results, args.n_rerank, args.n_llm
            )
            
            # Update state summary immediately (with standardization)
            update_state_summary(state_summary_file, task, result, logger)
            
            # Create/update overall summary every 5 runs
            if run_count % 5 == 0 or run_count == total_runs:
                create_overall_summary(output_base, states_to_process[:states_to_process.index(state)+1], 
                                     tasks_to_process, logger)
            
            # Brief pause
            if run_count < total_runs:
                time.sleep(2)
        
        if not state_has_work:
            print(f"All tasks already completed for {state}")
    
    # Final summary
    total_duration = time.time() - start_time
    final_summary = create_overall_summary(output_base, states_to_process, tasks_to_process, logger)
    
    print(f"\n{'='*80}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*80}")
    print(f"\nProcessing Summary:")
    print(f"  - States: {len(states_to_process)}")
    print(f"  - Tasks: {len(tasks_to_process)}")
    print(f"  - Total runs: {run_count}")
    print(f"  - Duration: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
    
    print(f"\nFinal Statistics:")
    print(f"  - Successful: {final_summary['overall_statistics']['total_successful_runs']}")
    print(f"  - Failed: {final_summary['overall_statistics']['total_failed_runs']}")
    print(f"  - Completion: {final_summary['overall_statistics']['completion_percentage']}%")
    
    print(f"\nOutput Structure:")
    print(f"  - State folders: {output_base}/[state]/")
    print(f"  - Task results: {output_base}/[state]/[task]/")
    print(f"  - State summaries: {output_base}/[state]/state_summary.json")
    print(f"  - Combined by task: {output_base}/_combined_by_task/[task]_combined.json")
    print(f"  - Overall summary: {output_base}/overall_summary.json")
    print(f"\nAll outputs saved to: {output_base.absolute()}")
    print(f"Data standardization applied: All empty/placeholder values converted to null")

if __name__ == "__main__":
    main()