# Force Python to ignore warnings by setting the PYTHONWARNINGS environment variable
import os
os.environ["PYTHONWARNINGS"] = "ignore"

# Now import everything else
import argparse
import time
from datetime import datetime
import nest_asyncio
import warnings

# Set a placeholder OpenAI API key to prevent prompts for the key
# This is needed because some LlamaIndex dependencies might try to use OpenAI
os.environ["OPENAI_API_KEY"] = "placeholder-key-not-used"

from dotenv import load_dotenv
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader

# Apply nest_asyncio patch early
nest_asyncio.apply()

# Additional warning suppression for any warnings that might come later
warnings.filterwarnings("ignore")

def process_single_pdf(pdf_path, parser, output_dir):
    """
    Process a single PDF file and save it as markdown.
    Returns True if successful, False otherwise.
    """
    try:
        start_time = time.time()
        
        # Create SimpleDirectoryReader for single file
        reader = SimpleDirectoryReader(
            input_files=[pdf_path], 
            file_extractor={".pdf": parser}
        )
        
        # Load and parse the document
        print(f"  Loading document...")
        documents = reader.load_data()
        
        if not documents:
            print(f"  WARNING: No content extracted from {pdf_path}")
            return False
        
        # Extract content and concatenate
        content_chunks = []
        for doc in documents:
            content_chunks.append(doc.get_content())
        
        full_content = "\n\n".join(content_chunks)
        
        # Generate output filename
        base_name = os.path.basename(pdf_path)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_filename = f"{base_name_no_ext}.md"
        output_filepath = os.path.join(output_dir, output_filename)
        
        # Write markdown file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        elapsed_time = time.time() - start_time
        print(f"  ✓ Successfully converted to {output_filename} ({elapsed_time:.2f}s)")
        return True
        
    except Exception as e:
        print(f"  ✗ ERROR processing {pdf_path}: {str(e)}")
        return False

def main():
    """
    Main function to batch convert all PDFs in the State Plans folder to markdown.
    """
    # Set default paths
    default_input = "State Plans for Analysis"
    default_output = "State_Plans_Markdown"
    
    # Argument parsing
    cli_parser = argparse.ArgumentParser(
        description="Batch convert state plan PDFs to Markdown using LlamaParse."
    )
    cli_parser.add_argument(
        "-i", "--input", 
        default=default_input,
        help=f"Path to the input directory containing PDFs (default: {default_input})"
    )
    cli_parser.add_argument(
        "-o", "--output", 
        default=default_output,
        help=f"Path to the output directory for Markdown files (default: {default_output})"
    )
    args = cli_parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"State Plans PDF to Markdown Batch Converter")
    print(f"{'='*60}")
    print(f"Input directory:  {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load API key
    load_dotenv()
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        print("ERROR: LLAMA_CLOUD_API_KEY not found in environment variables or .env file.")
        print("Please create a .env file with LLAMA_CLOUD_API_KEY=your_key or set the environment variable.")
        return
    
    # Initialize LlamaParse
    print("Initializing LlamaParse...")
    try:
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=False  # Disable verbose to reduce clutter during batch processing
        )
        print("LlamaParse initialized successfully.\n")
    except Exception as e:
        print(f"ERROR initializing LlamaParse: {e}")
        return
    
    # Create output directory
    try:
        os.makedirs(args.output, exist_ok=True)
        print(f"Output directory '{args.output}' ready.\n")
    except OSError as e:
        print(f"ERROR creating output directory '{args.output}': {e}")
        return
    
    # Get all PDF files
    pdf_files = []
    if os.path.isdir(args.input):
        for file in sorted(os.listdir(args.input)):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(args.input, file))
    else:
        print(f"ERROR: Input directory '{args.input}' not found.")
        return
    
    if not pdf_files:
        print(f"No PDF files found in '{args.input}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process.\n")
    
    # Process each PDF
    successful = 0
    failed = 0
    total_start_time = time.time()
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_path)}")
        
        if process_single_pdf(pdf_path, parser, args.output):
            successful += 1
        else:
            failed += 1
        
        # Add small delay to avoid rate limiting
        if i < len(pdf_files):
            time.sleep(0.5)
    
    # Summary
    total_elapsed = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"CONVERSION COMPLETE")
    print(f"{'='*60}")
    print(f"Total files processed: {len(pdf_files)}")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {failed}")
    print(f"Total time: {total_elapsed:.2f} seconds")
    print(f"Average time per file: {total_elapsed/len(pdf_files):.2f} seconds")
    print(f"Output directory: {os.path.abspath(args.output)}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()