#!/usr/bin/env python3
"""Main entry point for FFPSA data extraction."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from src.extraction_engine import ExtractionEngine
from src.validators import DataValidator
from src.utils import (
    setup_logging, load_config, save_json, 
    create_extraction_summary, format_extraction_for_display,
    estimate_cost
)


async def extract_single_document(
    markdown_path: str,
    output_dir: str,
    config_path: str = "config/extraction_config.json"
) -> None:
    """Extract data from a single markdown document.
    
    Args:
        markdown_path: Path to markdown file
        output_dir: Output directory for results
        config_path: Path to configuration file
    """
    # Setup
    logger = setup_logging()
    config = load_config(config_path)
    
    # Initialize engine
    engine = ExtractionEngine(config, logger)
    
    # Extract data
    logger.info(f"Extracting from: {markdown_path}")
    result = await engine.extract_from_document(markdown_path)
    
    # Validate results
    validator = DataValidator()
    validation_results = validator.validate_all_categories(
        result.get("extracted_data", {})
    )
    quality_report = validator.generate_quality_report(
        result, validation_results
    )
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    state = result["metadata"].get("state", "unknown")
    save_json(result, str(output_path / f"{state}_extraction.json"))
    save_json(quality_report, str(output_path / f"{state}_quality_report.json"))
    
    # Display summary
    print("\n" + "="*60)
    print(format_extraction_for_display(result))
    print("\n" + "="*60)
    print(f"Quality Score: {quality_report['quality_score']:.2f}")
    print(f"Tokens Used: {result['tokens_used']:,}")
    print(f"Estimated Cost: ${estimate_cost(result['tokens_used'], config['model_config']['model_name'])}")
    
    if quality_report["recommendations"]:
        print("\nRecommendations:")
        for rec in quality_report["recommendations"]:
            print(f"  - {rec}")


async def extract_batch(
    input_dir: str,
    output_dir: str,
    config_path: str = "config/extraction_config.json"
) -> None:
    """Extract data from all markdown documents in a directory.
    
    Args:
        input_dir: Directory containing markdown files
        output_dir: Output directory for results
        config_path: Path to configuration file
    """
    # Setup
    logger = setup_logging()
    config = load_config(config_path)
    
    # Initialize engine
    engine = ExtractionEngine(config, logger)
    
    # Process all documents
    logger.info(f"Starting batch extraction from: {input_dir}")
    results = await engine.batch_extract(input_dir, output_dir)
    
    # Create summary
    summary = create_extraction_summary(results)
    save_json(summary, str(Path(output_dir) / "extraction_summary.json"))
    
    # Validate all results
    validator = DataValidator()
    quality_reports = []
    
    for result in results:
        if result.get("success"):
            validation_results = validator.validate_all_categories(
                result.get("extracted_data", {})
            )
            quality_report = validator.generate_quality_report(
                result, validation_results
            )
            quality_reports.append({
                "state": result["metadata"].get("state", "unknown"),
                "quality_score": quality_report["quality_score"]
            })
    
    # Display summary
    print("\n" + "="*60)
    print("BATCH EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total Documents: {summary['total_documents']}")
    print(f"Successful: {summary['successful_extractions']}")
    print(f"Failed: {summary['failed_extractions']}")
    print(f"States Processed: {', '.join(sorted(summary['states_processed']))}")
    print(f"Total Tokens Used: {summary['total_tokens_used']:,}")
    print(f"Estimated Total Cost: ${estimate_cost(summary['total_tokens_used'], config['model_config']['model_name'])}")
    
    if summary.get("average_confidence"):
        print(f"Average Confidence: {summary['average_confidence']}/10")
    
    print("\nQuality Scores by State:")
    for report in sorted(quality_reports, key=lambda x: x["quality_score"], reverse=True)[:10]:
        print(f"  {report['state']}: {report['quality_score']:.2f}")
    
    print(f"\nFull results saved to: {output_dir}")


def analyze_results(output_dir: str) -> None:
    """Analyze extraction results and generate reports.
    
    Args:
        output_dir: Directory containing extraction results
    """
    from src.utils import load_json
    import pandas as pd
    
    # Load combined results
    results_path = Path(output_dir) / "all_states_extracted.json"
    if not results_path.exists():
        print(f"No results found at: {results_path}")
        return
    
    results = load_json(str(results_path))
    
    # Create analysis
    print("\n" + "="*60)
    print("EXTRACTION ANALYSIS")
    print("="*60)
    
    # Success rate
    successful = [r for r in results if r.get("success")]
    print(f"\nSuccess Rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    
    # Category completeness
    category_counts = {}
    for result in successful:
        for category in result.get("extracted_data", {}).keys():
            if category not in ["metadata", "extraction_confidence"]:
                category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\nCategory Extraction Rates:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}/{len(successful)} ({count/len(successful)*100:.1f}%)")
    
    # Key findings
    print("\nKey Findings:")
    
    # Trauma-informed delivery
    trauma_count = sum(
        1 for r in successful 
        if r.get("extracted_data", {}).get("trauma_informed_delivery", {}).get("uses_trauma_informed_approach")
    )
    print(f"  - States with trauma-informed delivery: {trauma_count}/{len(successful)} ({trauma_count/len(successful)*100:.1f}%)")
    
    # Equity focus
    equity_count = sum(
        1 for r in successful 
        if r.get("extracted_data", {}).get("equity_disparity_reduction", {}).get("addresses_equity")
    )
    print(f"  - States addressing equity: {equity_count}/{len(successful)} ({equity_count/len(successful)*100:.1f}%)")
    
    # Structural determinants
    structural_count = sum(
        1 for r in successful 
        if r.get("extracted_data", {}).get("structural_determinants", {}).get("addresses_structural_factors")
    )
    print(f"  - States addressing structural determinants: {structural_count}/{len(successful)} ({structural_count/len(successful)*100:.1f}%)")
    
    # Export detailed analysis
    analysis_path = Path(output_dir) / "detailed_analysis.csv"
    
    # Create DataFrame for analysis
    rows = []
    for result in successful:
        row = {
            "state": result["metadata"].get("state", "Unknown"),
            "document_date": result["metadata"].get("document_date", ""),
            "pages": result["metadata"].get("total_pages", 0),
            "confidence_score": result.get("extraction_confidence", {}).get("confidence_score", 0)
        }
        
        # Add key indicators
        data = result.get("extracted_data", {})
        row["trauma_informed"] = data.get("trauma_informed_delivery", {}).get("uses_trauma_informed_approach", False)
        row["addresses_equity"] = data.get("equity_disparity_reduction", {}).get("addresses_equity", False)
        row["addresses_structural"] = data.get("structural_determinants", {}).get("addresses_structural_factors", False)
        
        # Count programs and populations
        row["programs_count"] = data.get("programs_waiting_to_add", {}).get("total_count", 0)
        row["populations_count"] = len(data.get("target_populations", {}).get("populations", []))
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(analysis_path, index=False)
    print(f"\nDetailed analysis exported to: {analysis_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured data from FFPSA state prevention plans"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Single document extraction
    single_parser = subparsers.add_parser(
        "extract-single", 
        help="Extract data from a single document"
    )
    single_parser.add_argument(
        "markdown_path", 
        help="Path to markdown file"
    )
    single_parser.add_argument(
        "-o", "--output-dir",
        default="data/output/extracted",
        help="Output directory (default: data/output/extracted)"
    )
    single_parser.add_argument(
        "-c", "--config",
        default="config/extraction_config.json",
        help="Configuration file path"
    )
    
    # Batch extraction
    batch_parser = subparsers.add_parser(
        "extract-batch",
        help="Extract data from all documents in a directory"
    )
    batch_parser.add_argument(
        "-i", "--input-dir",
        default="State_Plans_Markdown",
        help="Input directory containing markdown files"
    )
    batch_parser.add_argument(
        "-o", "--output-dir",
        default="data/output/extracted",
        help="Output directory"
    )
    batch_parser.add_argument(
        "-c", "--config",
        default="config/extraction_config.json",
        help="Configuration file path"
    )
    
    # Analysis
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze extraction results"
    )
    analyze_parser.add_argument(
        "-o", "--output-dir",
        default="data/output/extracted",
        help="Directory containing extraction results"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run appropriate command
    if args.command == "extract-single":
        asyncio.run(extract_single_document(
            args.markdown_path,
            args.output_dir,
            args.config
        ))
    elif args.command == "extract-batch":
        asyncio.run(extract_batch(
            args.input_dir,
            args.output_dir,
            args.config
        ))
    elif args.command == "analyze":
        analyze_results(args.output_dir)


if __name__ == "__main__":
    main()