"""
Standardize empty arrays in NonReimbursablePrograms to follow the prompt specification
When no data exists, should have one object with null values and explanatory reference
"""

import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def standardize_non_reimbursable_programs(state: str, base_dir: Path) -> bool:
    """
    Standardize the NonReimbursablePrograms data for a state
    Returns True if changes were made
    """
    llm_file = base_dir / state / "NonReimbursablePrograms" / "llm.json"
    
    if not llm_file.exists():
        logger.warning(f"File not found: {llm_file}")
        return False
    
    try:
        # Read the current data
        with open(llm_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if extraction exists and has non_reimbursable_programs
        if 'extraction' not in data:
            logger.warning(f"{state}: No extraction field found")
            return False
        
        extraction = data['extraction']
        
        # Check if non_reimbursable_programs exists
        if 'non_reimbursable_programs' not in extraction:
            logger.warning(f"{state}: No non_reimbursable_programs field found")
            return False
        
        programs = extraction['non_reimbursable_programs']
        
        # Check if it's an empty array that needs standardization
        if isinstance(programs, list) and len(programs) == 0:
            logger.info(f"{state}: Found empty array - standardizing to null object format")
            
            # Get chunk count from the data if available
            chunk_count = data.get('chunks_processed', 20)
            
            # Create the standardized null object
            standardized_programs = [
                {
                    "program_name": None,
                    "non_reimbursable_reason": None,
                    "future_timeline": None,
                    "reference": f"No non-reimbursable programs mentioned in chunks 1-{chunk_count}"
                }
            ]
            
            # Update the data
            data['extraction']['non_reimbursable_programs'] = standardized_programs
            
            # Add a note about standardization
            if 'standardization_notes' not in data:
                data['standardization_notes'] = []
            data['standardization_notes'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'Standardized empty array to null object format per prompt specification'
            })
            
            # Write back the updated data
            with open(llm_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{state}: Successfully standardized empty array")
            return True
        
        # Check if it already has the correct format
        elif (isinstance(programs, list) and 
              len(programs) == 1 and 
              programs[0].get('program_name') is None and
              'reference' in programs[0] and 
              'No non-reimbursable programs' in programs[0]['reference']):
            logger.info(f"{state}: Already has correct null object format")
            return False
        
        # Has actual data
        else:
            logger.info(f"{state}: Has {len(programs) if isinstance(programs, list) else 'non-list'} programs - no standardization needed")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {state}: {e}")
        return False

def main():
    """Main function to standardize all states"""
    base_dir = Path("multi_state_output_standardized")
    
    if not base_dir.exists():
        logger.error(f"Base directory not found: {base_dir}")
        return
    
    # Get all state directories
    states = [d.name for d in base_dir.iterdir() 
              if d.is_dir() and not d.name.startswith('_')]
    
    logger.info(f"Found {len(states)} states to check")
    
    # Track changes
    states_changed = []
    states_already_correct = []
    states_with_data = []
    states_with_errors = []
    
    for state in sorted(states):
        logger.info(f"\nProcessing {state}...")
        
        try:
            changed = standardize_non_reimbursable_programs(state, base_dir)
            
            if changed:
                states_changed.append(state)
            else:
                # Check why it wasn't changed
                llm_file = base_dir / state / "NonReimbursablePrograms" / "llm.json"
                if llm_file.exists():
                    with open(llm_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'extraction' in data and 'non_reimbursable_programs' in data['extraction']:
                        programs = data['extraction']['non_reimbursable_programs']
                        if isinstance(programs, list) and len(programs) == 1 and programs[0].get('program_name') is None:
                            states_already_correct.append(state)
                        elif isinstance(programs, list) and len(programs) > 0 and programs[0].get('program_name') is not None:
                            states_with_data.append(state)
                        
        except Exception as e:
            logger.error(f"Error processing {state}: {e}")
            states_with_errors.append(state)
    
    # Print summary
    print("\n" + "="*80)
    print("STANDARDIZATION SUMMARY")
    print("="*80)
    print(f"Total states processed: {len(states)}")
    print(f"States changed: {len(states_changed)}")
    print(f"States already correct: {len(states_already_correct)}")
    print(f"States with actual data: {len(states_with_data)}")
    print(f"States with errors: {len(states_with_errors)}")
    
    if states_changed:
        print(f"\nStates that were standardized: {', '.join(sorted(states_changed))}")
    
    if states_already_correct:
        print(f"\nStates already in correct format: {', '.join(sorted(states_already_correct))}")
    
    if states_with_data:
        print(f"\nStates with actual non-reimbursable programs: {len(states_with_data)} states")
    
    if states_with_errors:
        print(f"\nStates with errors: {', '.join(sorted(states_with_errors))}")
    
    # Save summary
    summary = {
        'standardization_timestamp': datetime.now().isoformat(),
        'total_states': len(states),
        'states_changed': sorted(states_changed),
        'states_already_correct': sorted(states_already_correct),
        'states_with_data': sorted(states_with_data),
        'states_with_errors': sorted(states_with_errors),
        'changes_made': len(states_changed)
    }
    
    summary_file = base_dir / "non_reimbursable_standardization_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    
    if states_changed:
        print("\n⚠️  IMPORTANT: You should now regenerate the combined files to include these changes!")
    
    return len(states_changed) > 0

if __name__ == "__main__":
    changes_made = main()
    exit(0 if not changes_made else 1)  # Exit with 1 if changes were made (to signal regeneration needed)