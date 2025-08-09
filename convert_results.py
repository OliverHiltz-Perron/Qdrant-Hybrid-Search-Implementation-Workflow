#!/usr/bin/env python3
"""Convert extraction results to CSV and human-readable formats."""

import argparse
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import sys


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary into single level.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator between keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to string representation
            if v and isinstance(v[0], dict):
                # List of complex objects - convert to count and sample
                items.append((f"{new_key}_count", len(v)))
                items.append((f"{new_key}_sample", str(v[0]) if v else ""))
            else:
                # Simple list - join as string
                items.append((new_key, '; '.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)


def extract_key_metrics(data: Dict) -> Dict:
    """Extract key metrics from extraction data.
    
    Args:
        data: Extraction result dictionary
        
    Returns:
        Dictionary of key metrics
    """
    metrics = {
        'state': data.get('metadata', {}).get('state', 'Unknown'),
        'document_date': data.get('metadata', {}).get('document_date', ''),
        'pages': data.get('metadata', {}).get('total_pages', 0),
        'confidence_score': data.get('extraction_confidence', {}).get('confidence_score', 0),
        'categories_extracted': data.get('extraction_confidence', {}).get('categories_extracted', 0),
    }
    
    # Extract key data from each category
    extracted = data.get('extracted_data', {})
    
    # Programs waiting
    programs = extracted.get('programs_waiting_to_add', {})
    metrics['programs_waiting_count'] = programs.get('total_count', 0)
    
    # Target populations
    populations = extracted.get('target_populations', {})
    metrics['populations_count'] = len(populations.get('populations', []))
    metrics['primary_population_focus'] = populations.get('primary_focus', '')
    
    # Funding
    funding = extracted.get('funding_sources', {})
    metrics['federal_funding_sources'] = len(funding.get('federal_sources', []))
    metrics['state_funding_sources'] = len(funding.get('state_sources', []))
    metrics['uses_braided_funding'] = funding.get('braided_funding', False)
    
    # Key indicators
    metrics['trauma_informed'] = extracted.get('trauma_informed_delivery', {}).get('uses_trauma_informed_approach', False)
    metrics['addresses_equity'] = extracted.get('equity_disparity_reduction', {}).get('addresses_equity', False)
    metrics['addresses_structural_determinants'] = extracted.get('structural_determinants', {}).get('addresses_structural_factors', False)
    
    # Monitoring
    monitoring = extracted.get('monitoring_accountability', {})
    metrics['has_oversight_structure'] = bool(monitoring.get('oversight_structure', ''))
    metrics['public_reporting'] = monitoring.get('reporting', {}).get('public_reporting', False)
    
    return metrics


def create_detailed_csv(results: List[Dict], output_path: str) -> None:
    """Create detailed CSV with all extraction data.
    
    Args:
        results: List of extraction results
        output_path: Path for CSV output
    """
    rows = []
    
    for result in results:
        if not result.get('success', True):
            continue
            
        # Start with metadata
        row = {
            'state': result.get('metadata', {}).get('state', 'Unknown'),
            'filename': result.get('metadata', {}).get('filename', ''),
            'document_date': result.get('metadata', {}).get('document_date', ''),
            'total_pages': result.get('metadata', {}).get('total_pages', 0),
            'confidence_score': result.get('extraction_confidence', {}).get('confidence_score', 0),
        }
        
        # Flatten all extracted data
        extracted = result.get('extracted_data', {})
        for category, data in extracted.items():
            if isinstance(data, dict):
                flattened = flatten_dict(data, parent_key=category)
                row.update(flattened)
        
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Sort columns for better organization
    if 'state' in df.columns:
        df = df.sort_values('state')
    
    # Save to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Detailed CSV saved to: {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")


def create_summary_csv(results: List[Dict], output_path: str) -> None:
    """Create summary CSV with key metrics only.
    
    Args:
        results: List of extraction results
        output_path: Path for CSV output
    """
    rows = []
    
    for result in results:
        if not result.get('success', True):
            continue
            
        metrics = extract_key_metrics(result)
        rows.append(metrics)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Sort by state
    if 'state' in df.columns:
        df = df.sort_values('state')
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nSummary CSV saved to: {output_path}")
    print(f"Total states: {len(df)}")


def create_human_readable_report(results: List[Dict], output_path: str) -> None:
    """Create human-readable text report.
    
    Args:
        results: List of extraction results
        output_path: Path for text output
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("FFPSA STATE PREVENTION PLANS - EXTRACTION SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        # Overall statistics
        successful = [r for r in results if r.get('success', True)]
        f.write(f"Total Documents Processed: {len(results)}\n")
        f.write(f"Successful Extractions: {len(successful)}\n")
        f.write(f"Failed Extractions: {len(results) - len(successful)}\n\n")
        
        # Key findings
        trauma_count = sum(1 for r in successful if r.get('extracted_data', {}).get('trauma_informed_delivery', {}).get('uses_trauma_informed_approach'))
        equity_count = sum(1 for r in successful if r.get('extracted_data', {}).get('equity_disparity_reduction', {}).get('addresses_equity'))
        structural_count = sum(1 for r in successful if r.get('extracted_data', {}).get('structural_determinants', {}).get('addresses_structural_factors'))
        
        f.write("KEY FINDINGS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"States with Trauma-Informed Approaches: {trauma_count}/{len(successful)} ({trauma_count/len(successful)*100:.1f}%)\n")
        f.write(f"States Addressing Equity: {equity_count}/{len(successful)} ({equity_count/len(successful)*100:.1f}%)\n")
        f.write(f"States Addressing Structural Determinants: {structural_count}/{len(successful)} ({structural_count/len(successful)*100:.1f}%)\n\n")
        
        # State-by-state summary
        f.write("STATE-BY-STATE SUMMARY:\n")
        f.write("=" * 80 + "\n\n")
        
        for result in sorted(successful, key=lambda x: x.get('metadata', {}).get('state', '')):
            state = result.get('metadata', {}).get('state', 'Unknown')
            f.write(f"State: {state}\n")
            f.write("-" * 40 + "\n")
            
            # Metadata
            metadata = result.get('metadata', {})
            f.write(f"Document: {metadata.get('filename', 'Unknown')}\n")
            f.write(f"Date: {metadata.get('document_date', 'Not found')}\n")
            f.write(f"Pages: {metadata.get('total_pages', 0)}\n")
            f.write(f"Confidence Score: {result.get('extraction_confidence', {}).get('confidence_score', 0)}/10\n\n")
            
            # Key data points
            data = result.get('extracted_data', {})
            
            # Programs
            programs = data.get('programs_waiting_to_add', {})
            f.write(f"Programs Waiting to Add: {programs.get('total_count', 0)}\n")
            if programs.get('programs'):
                for i, prog in enumerate(programs['programs'][:3], 1):
                    f.write(f"  {i}. {prog.get('name', 'Unknown')}\n")
                if len(programs['programs']) > 3:
                    f.write(f"  ... and {len(programs['programs']) - 3} more\n")
            
            # Populations
            pops = data.get('target_populations', {})
            f.write(f"\nTarget Populations: {len(pops.get('populations', []))}\n")
            if pops.get('primary_focus'):
                f.write(f"Primary Focus: {pops['primary_focus']}\n")
            
            # Funding
            funding = data.get('funding_sources', {})
            f.write(f"\nFunding Sources:\n")
            f.write(f"  Federal: {len(funding.get('federal_sources', []))}\n")
            f.write(f"  State: {len(funding.get('state_sources', []))}\n")
            f.write(f"  Braided Funding: {'Yes' if funding.get('braided_funding') else 'No'}\n")
            
            # Key indicators
            f.write(f"\nKey Indicators:\n")
            trauma = data.get('trauma_informed_delivery', {})
            f.write(f"  Trauma-Informed: {'Yes' if trauma.get('uses_trauma_informed_approach') else 'No'}\n")
            
            equity = data.get('equity_disparity_reduction', {})
            f.write(f"  Addresses Equity: {'Yes' if equity.get('addresses_equity') else 'No'}\n")
            
            structural = data.get('structural_determinants', {})
            f.write(f"  Addresses Structural Determinants: {'Yes' if structural.get('addresses_structural_factors') else 'No'}\n")
            
            # Exact quotes (if available)
            f.write(f"\nSample Quotes:\n")
            quote_found = False
            for category in ['programs_waiting_to_add', 'equity_disparity_reduction', 'trauma_informed_delivery']:
                if category in data and 'exact_quotes' in data[category] and data[category]['exact_quotes']:
                    quote = data[category]['exact_quotes'][0]
                    f.write(f"  {category.replace('_', ' ').title()}:\n")
                    f.write(f"  \"{quote.get('quote', '')[:200]}...\"\n")
                    quote_found = True
                    break
            if not quote_found:
                f.write("  No quotes extracted\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
        
        # Failed extractions
        if len(results) > len(successful):
            f.write("FAILED EXTRACTIONS:\n")
            f.write("-" * 40 + "\n")
            for result in results:
                if not result.get('success', True):
                    f.write(f"File: {result.get('metadata', {}).get('filename', 'Unknown')}\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n\n")
    
    print(f"\nHuman-readable report saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert FFPSA extraction results to CSV and human-readable formats"
    )
    
    parser.add_argument(
        "input",
        help="Input JSON file (e.g., all_states_extracted.json)"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        default="data/output/reports",
        help="Output directory for converted files"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Create detailed CSV with all fields"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Create summary CSV with key metrics only"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Create human-readable text report"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Create all output formats"
    )
    
    args = parser.parse_args()
    
    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
    data = None
    
    for encoding in encodings:
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            if encoding == encodings[-1]:  # Last encoding attempt
                print(f"Error: Failed to read JSON file with any encoding.")
                print(f"Tried encodings: {', '.join(encodings)}")
                print(f"Last error: {e}")
                sys.exit(1)
            continue
    
    # Handle both single result and list of results
    if isinstance(data, dict):
        results = [data]
    else:
        results = data
    
    print(f"Loaded {len(results)} extraction results")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate requested outputs
    if args.all or (not args.detailed and not args.summary and not args.report):
        # Default: create all outputs
        args.detailed = True
        args.summary = True
        args.report = True
    
    if args.detailed:
        detailed_path = output_dir / "extraction_detailed.csv"
        create_detailed_csv(results, str(detailed_path))
    
    if args.summary:
        summary_path = output_dir / "extraction_summary.csv"
        create_summary_csv(results, str(summary_path))
    
    if args.report:
        report_path = output_dir / "extraction_report.txt"
        create_human_readable_report(results, str(report_path))
    
    print(f"\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()