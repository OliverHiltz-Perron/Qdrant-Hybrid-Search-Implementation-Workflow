"""
Verify that all states are present in all combined JSON files
"""

import json
from pathlib import Path
from typing import Dict, List, Set

def verify_state_coverage():
    """Check that all states are in all combined files"""
    
    # Define expected states (42 total)
    expected_states = {
        'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'FL', 'GA', 'HI', 'IA', 
        'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 
        'MN', 'MO', 'MT', 'NC', 'ND', 'NE', 'NH', 'NV', 'NY', 'OH', 
        'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'UT', 'VA', 'VT', 'WA', 
        'WI', 'WV'
    }
    
    combined_dir = Path("multi_state_output_standardized/_combined_by_task")
    
    # Get all combined files
    combined_files = sorted(combined_dir.glob("*_combined.json"))
    
    print(f"Found {len(combined_files)} combined files")
    print(f"Expected {len(expected_states)} states in each file\n")
    print("=" * 80)
    
    # Track issues
    all_good = True
    summary = {}
    
    for file_path in combined_files:
        task_name = file_path.stem.replace("_combined", "")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get states in this file
            states_in_file = set(data.get('states', {}).keys())
            
            # Check for missing states
            missing_states = expected_states - states_in_file
            
            # Check for extra states (shouldn't happen)
            extra_states = states_in_file - expected_states
            
            # Store summary
            summary[task_name] = {
                'total_states': len(states_in_file),
                'missing_states': list(missing_states),
                'extra_states': list(extra_states),
                'status': 'OK' if len(missing_states) == 0 and len(extra_states) == 0 else 'ISSUE'
            }
            
            # Print results for this file
            print(f"\n{task_name}:")
            print(f"  States found: {len(states_in_file)}/{len(expected_states)}")
            
            if missing_states:
                all_good = False
                print(f"  ❌ MISSING STATES: {', '.join(sorted(missing_states))}")
            else:
                print(f"  ✓ All states present")
            
            if extra_states:
                all_good = False
                print(f"  ⚠️  UNEXPECTED STATES: {', '.join(sorted(extra_states))}")
            
            # Check if any states have null/empty data
            empty_data_states = []
            for state in states_in_file:
                state_data = data['states'][state]
                if state_data is None or (isinstance(state_data, dict) and not state_data):
                    empty_data_states.append(state)
            
            if empty_data_states:
                print(f"  ⚠️  States with empty/null data: {', '.join(sorted(empty_data_states))}")
                
        except Exception as e:
            print(f"\n{task_name}:")
            print(f"  ❌ ERROR reading file: {e}")
            all_good = False
            summary[task_name] = {'status': 'ERROR', 'error': str(e)}
    
    # Print overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    if all_good:
        print("✅ ALL GOOD: All 42 states are present in all 14 combined files!")
    else:
        print("❌ ISSUES FOUND:")
        for task, info in summary.items():
            if info['status'] != 'OK':
                print(f"\n  {task}:")
                if 'missing_states' in info and info['missing_states']:
                    print(f"    Missing: {', '.join(info['missing_states'])}")
                if 'extra_states' in info and info['extra_states']:
                    print(f"    Extra: {', '.join(info['extra_states'])}")
                if 'error' in info:
                    print(f"    Error: {info['error']}")
    
    # Create detailed report
    report = {
        'verification_timestamp': Path(__file__).stat().st_mtime if Path(__file__).exists() else None,
        'expected_states': sorted(list(expected_states)),
        'expected_state_count': len(expected_states),
        'files_checked': len(combined_files),
        'all_states_present': all_good,
        'file_summaries': summary
    }
    
    # Save report
    report_file = Path("multi_state_output_standardized/state_coverage_verification.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return all_good

if __name__ == "__main__":
    result = verify_state_coverage()
    exit(0 if result else 1)