"""
Regenerate _combined.json files from individual state LLM outputs
This script reads all state/task LLM outputs and recreates the combined JSON files
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_all_tasks(base_dir: Path) -> Set[str]:
    """Discover all unique task types from the state directories"""
    tasks = set()
    
    # List all state directories
    for state_dir in base_dir.iterdir():
        if state_dir.is_dir() and not state_dir.name.startswith('_'):
            # List all task directories within each state
            for task_dir in state_dir.iterdir():
                if task_dir.is_dir():
                    tasks.add(task_dir.name)
    
    return tasks

def get_all_states(base_dir: Path) -> List[str]:
    """Get all state codes that have output directories"""
    states = []
    
    for state_dir in base_dir.iterdir():
        if state_dir.is_dir() and not state_dir.name.startswith('_'):
            states.append(state_dir.name)
    
    return sorted(states)

def read_llm_output(state: str, task: str, base_dir: Path) -> Dict:
    """Read the LLM output for a specific state and task"""
    llm_file = base_dir / state / task / "llm.json"
    
    if not llm_file.exists():
        logger.warning(f"LLM file not found: {llm_file}")
        return None
    
    try:
        with open(llm_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Return just the extraction part
            if 'extraction' in data:
                return data['extraction']
            else:
                logger.warning(f"No extraction field in {llm_file}")
                return None
    except Exception as e:
        logger.error(f"Error reading {llm_file}: {e}")
        return None

def create_combined_file(task: str, base_dir: Path, output_dir: Path):
    """Create a combined JSON file for a specific task across all states"""
    logger.info(f"Creating combined file for task: {task}")
    
    # Get all states
    states = get_all_states(base_dir)
    
    # Collect data from all states for this task
    combined_data = {
        "task": task,
        "timestamp": datetime.now().isoformat(),
        "states": {}
    }
    
    states_with_data = 0
    for state in states:
        llm_data = read_llm_output(state, task, base_dir)
        if llm_data is not None:
            combined_data["states"][state] = llm_data
            states_with_data += 1
            logger.info(f"  Added data for {state}")
    
    # Save the combined file
    output_file = output_dir / f"{task}_combined.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  Saved {output_file} with data from {states_with_data} states")
    return states_with_data

def main():
    """Main function to regenerate all combined files"""
    # Define paths
    base_dir = Path("multi_state_output_standardized")
    output_dir = base_dir / "_combined_by_task"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Get all unique tasks
    tasks = get_all_tasks(base_dir)
    logger.info(f"Found {len(tasks)} unique tasks: {sorted(tasks)}")
    
    # Get all states
    states = get_all_states(base_dir)
    logger.info(f"Found {len(states)} states: {states}")
    
    # Create combined file for each task
    summary = {}
    for task in sorted(tasks):
        states_count = create_combined_file(task, base_dir, output_dir)
        summary[task] = states_count
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("REGENERATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total tasks processed: {len(tasks)}")
    logger.info(f"Total states checked: {len(states)}")
    logger.info("\nStates with data per task:")
    for task, count in sorted(summary.items()):
        logger.info(f"  {task}: {count} states")
    
    # Create an overall summary file
    overall_summary = {
        "regeneration_timestamp": datetime.now().isoformat(),
        "total_tasks": len(tasks),
        "total_states": len(states),
        "tasks": sorted(tasks),
        "states": states,
        "data_coverage": summary
    }
    
    summary_file = base_dir / "regeneration_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall_summary, f, indent=2)
    
    logger.info(f"\nSummary saved to: {summary_file}")

if __name__ == "__main__":
    main()