#!/usr/bin/env python3
"""
Process all states data from combined JSON files and embed to Qdrant.
This script takes the combined task JSON files and creates embeddings for each state's data.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, 
    Distance, 
    PointStruct,
    SparseVector,
    NamedSparseVector,
    SparseVectorParams,
    SparseIndexParams,
    Filter,
    FieldCondition,
    MatchValue
)
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import numpy as np
from tqdm import tqdm
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============== CHUNKING IMPLEMENTATION (from chunk_state_semantic_enhanced.py) ===============

class FallbackSemanticChunker:
    """Fallback semantic chunker if chonkie is not available"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 chunk_size: int = 512, 
                 similarity_threshold: float = 0.5):
        self.model = SentenceTransformer(model_name)
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.chunk_size = chunk_size
        self.similarity_threshold = similarity_threshold
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with spacy or nltk
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_semantically(self, text: str, headers: List[Tuple[int, str, str]], 
                          min_chunk_size: int = 200, max_chunk_size: int = 3000) -> List[Dict]:
        """Create semantic chunks based on sentence similarity with size constraints"""
        sentences = self.chunk_by_sentences(text)
        
        if not sentences:
            return []
        
        # Encode all sentences
        embeddings = self.model.encode(sentences)
        
        # Group sentences into chunks based on similarity
        chunks = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0].reshape(1, -1)
        current_position = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity with current chunk
            sentence_embedding = embeddings[i].reshape(1, -1)
            similarity = cosine_similarity(current_embedding, sentence_embedding)[0][0]
            
            # Calculate current chunk size in tokens
            current_text = ' '.join(current_chunk)
            current_tokens = len(self.tokenizer.encode(current_text))
            
            # Calculate size if we add this sentence
            potential_text = ' '.join(current_chunk + [sentences[i]])
            potential_tokens = len(self.tokenizer.encode(potential_text))
            
            # Decision logic with min/max constraints
            should_add_to_chunk = False
            
            if current_tokens < min_chunk_size:
                # Must add more to reach minimum
                should_add_to_chunk = True
            elif potential_tokens > max_chunk_size:
                # Would exceed maximum, must start new chunk
                should_add_to_chunk = False
            elif similarity >= self.similarity_threshold and potential_tokens <= self.chunk_size:
                # Within bounds and similar enough
                should_add_to_chunk = True
            
            if should_add_to_chunk and potential_tokens <= max_chunk_size:
                current_chunk.append(sentences[i])
                # Update embedding as mean of all sentences in chunk
                chunk_embeddings = embeddings[i-len(current_chunk)+1:i+1]
                current_embedding = np.mean(chunk_embeddings, axis=0).reshape(1, -1)
            else:
                # Save current chunk if it meets minimum size
                chunk_text = ' '.join(current_chunk)
                chunk_tokens = len(self.tokenizer.encode(chunk_text))
                
                if chunk_tokens >= min_chunk_size:
                    chunks.append({
                        'text': chunk_text,
                        'start_position': current_position,
                        'sentences': len(current_chunk),
                        'token_count': chunk_tokens
                    })
                    current_position += len(chunk_text) + 1
                else:
                    # Chunk too small, try to merge with next
                    print(f"Warning: Chunk with {chunk_tokens} tokens is below minimum {min_chunk_size}")
                
                # Start new chunk
                current_chunk = [sentences[i]]
                current_embedding = embeddings[i].reshape(1, -1)
        
        # Add final chunk if it meets minimum size
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_tokens = len(self.tokenizer.encode(chunk_text))
            
            if chunk_tokens >= min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'start_position': current_position,
                    'sentences': len(current_chunk),
                    'token_count': chunk_tokens
                })
            elif chunks:
                # Try to merge with previous chunk if too small
                print(f"Warning: Final chunk with {chunk_tokens} tokens is below minimum, merging with previous")
                chunks[-1]['text'] += ' ' + chunk_text
                chunks[-1]['sentences'] += len(current_chunk)
                chunks[-1]['token_count'] = len(self.tokenizer.encode(chunks[-1]['text']))
        
        return chunks

def extract_headers_and_hierarchy(content: str) -> List[Tuple[int, str, str]]:
    """Extract headers with their hierarchy from markdown content"""
    headers = []
    lines = content.split('\n')
    position = 0
    
    for line in lines:
        match = re.match(r'^(#+)\s+(.+)$', line.strip())
        if match:
            header_level = match.group(1)
            header_text = match.group(2).strip()
            headers.append((position, header_level, header_text))
        position += len(line) + 1
    
    return headers

def find_section_hierarchy_for_position(position: int, headers: List[Tuple[int, str, str]]) -> Dict[int, str]:
    """Find the complete section hierarchy for a given position"""
    section_hierarchy = {}
    
    for header_pos, header_level, header_text in headers:
        if header_pos > position:
            break
        
        level = len(header_level)
        section_hierarchy[level] = header_text
        
        # Clear deeper levels when a higher level is encountered
        keys_to_remove = [k for k in section_hierarchy.keys() if k > level]
        for key in keys_to_remove:
            del section_hierarchy[key]
    
    return section_hierarchy

def format_section_path(section_hierarchy: Dict[int, str]) -> str:
    """Format section hierarchy into a readable path"""
    if not section_hierarchy:
        return "Document Start"
    
    sorted_levels = sorted(section_hierarchy.items())
    path_parts = [item[1] for item in sorted_levels]
    
    # Limit to 3 levels for readability
    if len(path_parts) > 3:
        path_parts = path_parts[:3]
    
    return " > ".join(path_parts)

def enrich_chunk_with_headers(chunk_text: str, chunk_position: int, headers: List[Tuple[int, str, str]]) -> Dict:
    """Enrich a chunk with header information"""
    section_hierarchy = find_section_hierarchy_for_position(chunk_position, headers)
    section_path = format_section_path(section_hierarchy)
    
    # Get primary section (deepest level)
    if section_hierarchy:
        deepest_level = max(section_hierarchy.keys())
        primary_section = section_hierarchy[deepest_level]
    else:
        primary_section = "Document Start"
    
    # Create enriched text with header context
    header_context = f"[Document Section: {section_path}]\n"
    header_context += f"[Primary Topic: {primary_section}]\n"
    header_context += "---\n"
    
    enriched_text = header_context + chunk_text
    
    return {
        'section_path': section_path,
        'primary_section': primary_section,
        'section_hierarchy': section_hierarchy,
        'enriched_text': enriched_text
    }

def chunk_with_semantic_similarity(text: str, metadata: dict, headers: List[Tuple[int, str, str]], 
                                 logger, chunk_size: int = 512, 
                                 min_chunk_size: int = 200,
                                 max_chunk_size: int = 3000,
                                 similarity_threshold: float = 0.5) -> List[Dict]:
    """Create semantic chunks using sentence similarity with size constraints"""
    logger.info("Using fallback semantic chunking with sentence-transformers")
    logger.info(f"Token constraints: min={min_chunk_size}, target={chunk_size}, max={max_chunk_size}")
    
    chunker = FallbackSemanticChunker(
        chunk_size=chunk_size,
        similarity_threshold=similarity_threshold
    )
    
    # Get semantic chunks with size constraints
    raw_chunks = chunker.chunk_semantically(text, headers, min_chunk_size, max_chunk_size)
    
    # Enrich chunks with headers
    formatted_chunks = []
    tokenizer = tiktoken.encoding_for_model("gpt-4")
    
    for i, chunk_data in enumerate(raw_chunks):
        # Find position in original text
        chunk_position = chunk_data['start_position']
        
        # Enrich with headers
        header_info = enrich_chunk_with_headers(
            chunk_data['text'], 
            chunk_position, 
            headers
        )
        
        # Calculate final token count
        final_token_count = len(tokenizer.encode(header_info['enriched_text']))
        
        chunk_dict = {
            'chunk_id': f"semantic_chunk_{i:06d}",
            'content': header_info['enriched_text'],
            'metadata': {
                'chunk_index': i,
                'total_chunks': len(raw_chunks),
                'chunk_size': len(chunk_data['text']),
                'token_count': final_token_count,
                'sentence_count': chunk_data['sentences'],
                'section_path': header_info['section_path'],
                'primary_section': header_info['primary_section'],
                'section_hierarchy': header_info['section_hierarchy'],
                'position_in_doc': chunk_position,
                'method': 'semantic_similarity',
                'similarity_threshold': similarity_threshold,
                **metadata
            },
            'embedding': None  # Will be filled by embed_to_qdrant
        }
        
        formatted_chunks.append(chunk_dict)
    
    return formatted_chunks

# =============== QDRANT STORAGE IMPLEMENTATION (from embed_to_qdrant.py) ===============

def generate_dense_embeddings(chunks: List[Dict], logger):
    """Generate OpenAI embeddings for chunks that don't have them"""
    logger.info("Generating dense embeddings for chunks without embeddings...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    chunks_to_embed = []
    chunk_indices = []
    
    # Identify chunks needing embeddings
    for i, chunk in enumerate(chunks):
        if not chunk.get('embedding') or chunk['embedding'] is None:
            chunks_to_embed.append(chunk['content'])
            chunk_indices.append(i)
    
    if not chunks_to_embed:
        logger.info("All chunks already have embeddings")
        return
    
    logger.info(f"Generating embeddings for {len(chunks_to_embed)} chunks...")
    
    # Process in batches
    batch_size = 100
    for i in tqdm(range(0, len(chunks_to_embed), batch_size), desc="Embedding batches"):
        batch = chunks_to_embed[i:i+batch_size]
        
        try:
            response = client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=batch
            )
            
            # Assign embeddings back to chunks
            for j, embedding_data in enumerate(response.data):
                chunk_idx = chunk_indices[i + j]
                chunks[chunk_idx]['embedding'] = embedding_data.embedding
                
        except Exception as e:
            logger.error(f"Error generating embeddings for batch {i//batch_size}: {e}")
            raise
    
    logger.info("Dense embeddings generated successfully")

def generate_sparse_embeddings(chunks: List[Dict], logger):
    """Generate BM25 sparse embeddings for chunks"""
    logger.info("Generating sparse embeddings for all chunks...")
    
    # Initialize BM25 model
    model = SparseTextEmbedding(
        model_name="Qdrant/bm25",
        cache_dir=str(config.BASE_DIR / "models")
    )
    
    # Extract texts
    texts = [chunk['content'] for chunk in chunks]
    
    # Generate sparse embeddings
    sparse_embeddings = list(model.embed(texts))
    
    # Convert to Qdrant format
    for chunk, sparse_embedding in zip(chunks, sparse_embeddings):
        # Convert to indices and values format
        indices = sparse_embedding.indices.tolist()
        values = sparse_embedding.values.tolist()
        chunk['sparse_embedding'] = {
            'indices': indices,
            'values': values
        }
    
    logger.info(f"Generated sparse embeddings for {len(chunks)} chunks")

def initialize_qdrant(logger):
    """Initialize Qdrant client with extended timeout"""
    # Get URL from environment or use default
    qdrant_url = os.getenv('QDRANT_URL', 'http://127.0.0.1:6333')
    logger.info(f"Connecting to Qdrant at {qdrant_url}")
    
    try:
        # Initialize with URL from environment
        client = QdrantClient(
            url=qdrant_url,
            timeout=120  # 2 minutes timeout
        )
        # Test connection
        client.get_collections()
        logger.info("Successfully connected to Qdrant")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running with: docker run -p 6333:6333 -v ~/qdrant_storage:/qdrant/storage qdrant/qdrant")
        raise

def create_collection(client, state_code, logger):
    """Create or recreate Qdrant collection with hybrid search configuration"""
    collection_name = config.get_collection_name(state_code)
    
    try:
        # Check if collection exists
        existing_collections = [col.name for col in client.get_collections().collections]
        
        if collection_name in existing_collections:
            logger.info(f"Collection '{collection_name}' exists. Deleting for fresh import...")
            client.delete_collection(collection_name)
            # Wait a moment for deletion to complete
            time.sleep(2)
        
        # Create new collection with hybrid configuration
        logger.info(f"Creating collection: {collection_name}")
        logger.info("This may take up to 2 minutes for hybrid search configuration...")
        
        # Get embedding dimension from config model
        embedding_dim = 1536  # text-embedding-3-small dimension
        
        # Try creating with timeout
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            },
            timeout=120  # 2 minutes timeout
        )
        
        logger.info(f"Successfully created collection with hybrid search support")
        return collection_name
        
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        logger.info("Possible solutions:")
        logger.info("1. Restart Qdrant: docker restart <container-name>")
        logger.info("2. Check Qdrant logs: docker logs <container-name>")
        logger.info("3. Increase Docker memory allocation")
        raise

def store_in_qdrant(client, collection_name, chunks, logger):
    """Store chunks with both dense and sparse vectors in Qdrant"""
    logger.info(f"Storing {len(chunks)} chunks in Qdrant collection: {collection_name}")
    
    # Prepare points for insertion
    points = []
    
    for i, chunk in enumerate(chunks):
        # Create unique ID
        point_id = i
        
        # Prepare payload (metadata + content)
        payload = {
            'chunk_id': chunk['chunk_id'],
            'content': chunk['content'],
            **chunk['metadata']
        }
        
        # Create point with both dense and sparse vectors
        point = PointStruct(
            id=point_id,
            vector={
                "dense": chunk['embedding'],
                "sparse": models.SparseVector(
                    indices=chunk['sparse_embedding']['indices'],
                    values=chunk['sparse_embedding']['values']
                )
            },
            payload=payload
        )
        
        points.append(point)
    
    # Batch upload with progress bar
    batch_size = 100
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading to Qdrant"):
        batch = points[i:i+batch_size]
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch
            )
        except Exception as e:
            logger.error(f"Error uploading batch {i//batch_size}: {e}")
            raise
    
    # Verify upload
    collection_info = client.get_collection(collection_name)
    logger.info(f"Successfully stored {collection_info.points_count} points in Qdrant")
    logger.info(f"Collection status: {collection_info.status}")

# =============== MAIN PROCESSING FUNCTION ===============

def process_state(state_code: str, data_dir: Path, client: QdrantClient, logger, run_dir: Path):
    """Process a single state: chunk and store in Qdrant"""
    logger.info(f"Processing state: {state_code}")
    
    # Step 1: Load document
    possible_files = [
        data_dir / f"{state_code}_PreventionPlan.md",
        data_dir / f"{state_code}_Prevention_Plan.md",
        data_dir / f"{state_code}.md",
        data_dir / f"{state_code.lower()}_prevention_plan.md"
    ]
    
    document_file = None
    for file_path in possible_files:
        if file_path.exists():
            document_file = file_path
            break
    
    if not document_file:
        logger.warning(f"No document found for state: {state_code}")
        return False
    
    logger.info(f"Loading document from: {document_file}")
    
    with open(document_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {
        'filename': document_file.name,
        'state': state_code,
        'state_abbr': state_code,
        'source': 'file',
        'file_path': str(document_file)
    }
    
    # Step 2: Extract headers
    headers = extract_headers_and_hierarchy(content)
    logger.info(f"Found {len(headers)} headers in document")
    
    # Step 3: Create semantic chunks
    chunks = chunk_with_semantic_similarity(
        content, 
        metadata, 
        headers, 
        logger,
        chunk_size=512,
        min_chunk_size=200,
        max_chunk_size=3000,
        similarity_threshold=0.5
    )
    logger.info(f"Created {len(chunks)} semantic chunks")
    
    # Step 4: Generate embeddings
    generate_dense_embeddings(chunks, logger)
    generate_sparse_embeddings(chunks, logger)
    
    # Step 5: Create collection and store in Qdrant
    collection_name = create_collection(client, state_code, logger)
    store_in_qdrant(client, collection_name, chunks, logger)
    
    # Step 6: Save chunks to dedicated chunks directory
    # Save chunks to state-specific file in the run directory
    output_file = run_dir / f"{state_code}_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'state_code': state_code,
            'total_chunks': len(chunks),
            'processing_timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'chunks': chunks
        }, f, indent=2)
    
    logger.info(f"Saved chunks to: {output_file}")
    logger.info(f"Completed processing for state: {state_code}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Process all state documents: chunk semantically and store in Qdrant'
    )
    parser.add_argument(
        '--data-dir', 
        type=str, 
        default="C:/Users/olive/OneDrive/Desktop/FFPSA_backup/data",
        help='Directory containing state markdown files'
    )
    parser.add_argument(
        '--states', 
        nargs='+', 
        help='Specific state codes to process (default: all states)'
    )
    parser.add_argument(
        '--skip-existing', 
        action='store_true',
        help='Skip states that already have collections in Qdrant'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = config.LOG_DIR / f"process_all_states_qdrant_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting batch processing of all states to Qdrant")
    logger.info(f"Logging to: {log_file}")
    
    # Initialize Qdrant client
    try:
        client = initialize_qdrant(logger)
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        return
    
    # Get list of states to process
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    if args.states:
        # Process specific states
        state_codes = args.states
    else:
        # Find all state files
        state_files = []
        for pattern in ["*_PreventionPlan.md", "*_Prevention_Plan.md"]:
            state_files.extend(data_dir.glob(pattern))
        
        # Extract state codes
        state_codes = []
        for file in state_files:
            # Extract state code from filename
            match = re.match(r'^([A-Z]{2})_', file.name)
            if match:
                state_codes.append(match.group(1))
        
        state_codes = sorted(list(set(state_codes)))
    
    logger.info(f"Found {len(state_codes)} states to process: {state_codes}")
    
    # Check existing collections if skip option is enabled
    if args.skip_existing:
        existing_collections = [col.name for col in client.get_collections().collections]
        initial_count = len(state_codes)
        state_codes = [sc for sc in state_codes if config.get_collection_name(sc) not in existing_collections]
        skipped_count = initial_count - len(state_codes)
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} states that already exist in Qdrant")
    
    # Create chunks output directory for this run
    chunks_dir = config.BASE_DIR / "chunks_output"
    chunks_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = chunks_dir / f"qdrant_chunks_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    logger.info(f"Saving all chunks to: {run_dir}")
    
    # Process each state
    successful = 0
    failed = 0
    
    for state_code in tqdm(state_codes, desc="Processing states"):
        try:
            if process_state(state_code, data_dir, client, logger, run_dir):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Failed to process state {state_code}: {e}")
            failed += 1
            # Continue with next state
            continue
    
    # Summary
    logger.info("="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Total states processed: {successful + failed}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    if failed > 0:
        logger.info("Failed states require manual review - check logs for details")
    
    logger.info(f"\nOutput locations:")
    logger.info(f"- Chunks saved to: {run_dir}")
    logger.info(f"- Logs saved to: {log_file}")
    logger.info(f"- Qdrant collections: {config.get_collection_name('<STATE>')}")

if __name__ == "__main__":
    main()