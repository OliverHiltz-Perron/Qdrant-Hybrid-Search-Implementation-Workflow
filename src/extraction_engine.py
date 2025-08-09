"""Main extraction engine for processing documents."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from tqdm import tqdm

from .document_processor import DocumentProcessor
from .prompts import get_prompt, get_categories_by_type
from .validators import DataValidator
from .utils import merge_chunks_results, save_json


class ExtractionEngine:
    """Engine for extracting structured data from documents."""
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """Initialize extraction engine.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.document_processor = DocumentProcessor(config)
        self.validator = DataValidator()
        self.api_client = self._setup_api_client()
        
    def _setup_api_client(self):
        """Set up API client based on provider.
        
        Returns:
            API client instance
        """
        provider = self.config["model_config"]["provider"]
        api_key = self.config.get("api_key")
        
        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=api_key)
        elif provider == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def extract_from_document(self, markdown_path: str) -> Dict:
        """Extract all categories from a single document.
        
        Args:
            markdown_path: Path to markdown file
            
        Returns:
            Extraction results dictionary
        """
        self.logger.info(f"Starting extraction for: {markdown_path}")
        
        # Load document
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Extract metadata
        metadata = self.document_processor.extract_metadata(
            markdown_content, 
            Path(markdown_path).name
        )
        
        # Analyze structure
        structure = self.document_processor.analyze_structure(markdown_content)
        self.logger.info(
            f"Document structure: {structure['total_tokens']} tokens, "
            f"{structure['pages']} pages, {len(structure['headings'])} headings"
        )
        
        # Initialize results
        results = {
            "metadata": metadata,
            "extracted_data": {},
            "extraction_confidence": {
                "confidence_score": 0,
                "categories_extracted": 0,
                "notes": []
            },
            "tokens_used": 0
        }
        
        # Extract full-context categories
        full_context_categories = get_categories_by_type("full_context")
        self.logger.info(f"Extracting full-context categories: {full_context_categories}")
        
        for category in full_context_categories:
            try:
                extraction = await self._extract_category_full_context(
                    category, markdown_content
                )
                results["extracted_data"][category] = extraction["data"]
                results["tokens_used"] += extraction["tokens_used"]
                
                # Validate extraction
                is_valid, errors = self.validator.validate_extraction(
                    category, extraction["data"]
                )
                if not is_valid:
                    self.logger.warning(f"Validation errors for {category}: {errors}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {category}: {str(e)}")
                results["extraction_confidence"]["notes"].append(
                    f"Failed to extract {category}: {str(e)}"
                )
        
        # Extract chunk-based categories
        chunk_based_categories = get_categories_by_type("chunk_based")
        self.logger.info(f"Extracting chunk-based categories: {chunk_based_categories}")
        
        # Create chunks
        chunks = self.document_processor.smart_chunk(markdown_content)
        self.logger.info(f"Created {len(chunks)} chunks for chunk-based extraction")
        
        for category in chunk_based_categories:
            try:
                extraction = await self._extract_category_chunked(
                    category, chunks
                )
                results["extracted_data"][category] = extraction["data"]
                results["tokens_used"] += extraction["tokens_used"]
                
                # Validate extraction
                is_valid, errors = self.validator.validate_extraction(
                    category, extraction["data"]
                )
                if not is_valid:
                    self.logger.warning(f"Validation errors for {category}: {errors}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {category}: {str(e)}")
                results["extraction_confidence"]["notes"].append(
                    f"Failed to extract {category}: {str(e)}"
                )
        
        # Calculate confidence score
        results["extraction_confidence"]["categories_extracted"] = len(
            results["extracted_data"]
        )
        results["extraction_confidence"]["confidence_score"] = self._calculate_confidence(
            results
        )
        
        return results
    
    async def _extract_category_full_context(self, category: str, 
                                          content: str) -> Dict:
        """Extract a category using full document context.
        
        Args:
            category: Category to extract
            content: Full document content
            
        Returns:
            Extraction result with data and token usage
        """
        prompt_config = get_prompt(category)
        prompt = prompt_config["prompt"]
        
        # Prepare the API call
        messages = [
            {"role": "system", "content": """You are an expert analyst specializing in child welfare policy documents, specifically state prevention plans under the Family First Prevention Services Act (FFPSA). 

Your task is to extract specific data elements from government documents with high accuracy. Follow these guidelines:

1. Extract ONLY the information explicitly stated in the document
2. Include exact quotes to support your findings
3. If information is not found, indicate it clearly rather than inferring
4. Focus on the specific requirements in the prompt
5. Always return valid JSON that matches the requested structure
6. Be precise and avoid generalizations

You are analyzing official state prevention plans that outline how states will implement evidence-based prevention services to keep children safely at home."""},
            {"role": "user", "content": f"{prompt}\n\nDocument:\n{content}"}
        ]
        
        # Make API call
        response_data, tokens_used = await self._call_api(messages)
        
        # Parse JSON response
        try:
            # Log raw response for debugging
            self.logger.debug(f"Raw response for {category}: {response_data[:500]}...")
            
            # Check if response is empty
            if not response_data or response_data.strip() == "":
                self.logger.warning(f"Empty response for {category}")
                extracted_data = {"error": "Empty response from API"}
            else:
                extracted_data = json.loads(response_data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON for {category}: {e}")
            self.logger.debug(f"Full raw response: {response_data}")
            extracted_data = {"error": "Failed to parse response", "raw": response_data[:200]}
        
        return {
            "data": extracted_data,
            "tokens_used": tokens_used
        }
    
    async def _extract_category_chunked(self, category: str, 
                                      chunks: List[Dict]) -> Dict:
        """Extract a category using chunked approach.
        
        Args:
            category: Category to extract
            chunks: List of document chunks
            
        Returns:
            Extraction result with merged data and token usage
        """
        prompt_config = get_prompt(category)
        prompt = prompt_config["prompt"]
        
        chunk_results = []
        total_tokens = 0
        
        # Process relevant chunks
        relevant_chunks = self._find_relevant_chunks(category, chunks)
        self.logger.info(f"Processing {len(relevant_chunks)} relevant chunks for {category}")
        
        for chunk in relevant_chunks:
            messages = [
                {"role": "system", "content": """You are an expert analyst specializing in child welfare policy documents, specifically state prevention plans under the Family First Prevention Services Act (FFPSA). 

Your task is to extract specific data elements from government documents with high accuracy. Follow these guidelines:

1. Extract ONLY the information explicitly stated in the document
2. Include exact quotes to support your findings
3. If information is not found, indicate it clearly rather than inferring
4. Focus on the specific requirements in the prompt
5. Always return valid JSON that matches the requested structure
6. Be precise and avoid generalizations

You are analyzing official state prevention plans that outline how states will implement evidence-based prevention services to keep children safely at home."""},
                {"role": "user", "content": f"{prompt}\n\nDocument section:\n{chunk['content']}"}
            ]
            
            try:
                response_data, tokens_used = await self._call_api(messages)
                total_tokens += tokens_used
                
                # Parse JSON response
                extracted_data = json.loads(response_data)
                chunk_results.append(extracted_data)
                
            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk['id']} for {category}: {e}")
                continue
        
        # Merge results from all chunks
        merged_data = merge_chunks_results(chunk_results, category)
        
        return {
            "data": merged_data,
            "tokens_used": total_tokens
        }
    
    def _find_relevant_chunks(self, category: str, chunks: List[Dict]) -> List[Dict]:
        """Find chunks relevant to a specific category.
        
        Args:
            category: Category name
            chunks: All document chunks
            
        Returns:
            List of relevant chunks
        """
        # Enhanced keywords and phrases for each category
        category_keywords = {
            "programs_waiting_to_add": [
                "waiting", "pending", "clearinghouse", "review", "future", "add",
                "to be added", "plan to add", "under consideration", "not yet approved",
                "pending approval", "clearinghouse evaluation", "will be added"
            ],
            "target_populations": [
                "population", "eligible", "age", "criteria", "serve", "youth", "families",
                "at risk", "foster care", "child welfare", "families with", "children who",
                "target", "recipient", "beneficiaries", "priority population"
            ],
            "eligibility_determination": [
                "eligibility", "screening", "assessment", "determine", "criteria",
                "qualify", "eligible for", "determination", "intake", "referral",
                "threshold", "risk assessment", "decision", "who qualifies"
            ],
            "workforce_support": [
                "training", "workforce", "staff", "professional", "development", "supervision",
                "credential", "qualification", "license", "certification", "competency",
                "capacity building", "retention", "recruitment", "coaching"
            ],
            "funding_sources": [
                "funding", "budget", "federal", "state", "braided", "finance", "resources",
                "title iv-e", "title iv-b", "medicaid", "tanf", "grant", "appropriation",
                "revenue", "cost", "reimbursement", "match", "allocation"
            ],
            "trauma_informed_delivery": [
                "trauma", "informed", "approach", "practice", "healing",
                "trauma-informed", "trauma-responsive", "adverse childhood", "aces",
                "resilience", "trauma-specific", "secondary trauma"
            ],
            "effectiveness_outcomes": [
                "outcomes", "metrics", "evaluation", "effectiveness", "measure",
                "reunification", "placement stability", "foster care entry", "recurrence",
                "maltreatment", "success", "goals", "targets", "benchmarks", "indicators"
            ],
            "monitoring_accountability": [
                "monitoring", "accountability", "oversight", "quality", "compliance",
                "cqi", "continuous quality improvement", "fidelity", "quality assurance",
                "performance", "review", "audit", "implementation monitoring"
            ],
            "equity_disparity_reduction": [
                "equity", "disparity", "disparities", "cultural", "racial",
                "disproportionality", "overrepresentation", "lgbtq", "rural", "urban",
                "culturally responsive", "language access", "bias", "discrimination"
            ],
            "structural_determinants": [
                "poverty", "housing", "economic", "social", "determinants", "structural",
                "homeless", "food", "transportation", "healthcare", "employment",
                "childcare", "education", "income", "concrete support", "basic needs"
            ]
        }
        
        keywords = category_keywords.get(category, [])
        relevant_chunks = []
        
        for chunk in chunks:
            content_lower = chunk["content"].lower()
            
            # Check if chunk contains relevant keywords
            relevance_score = sum(
                1 for keyword in keywords 
                if keyword in content_lower
            )
            
            # Include chunks with high relevance
            # Lower threshold for better recall
            if relevance_score >= 1:
                relevant_chunks.append({
                    **chunk,
                    "relevance_score": relevance_score
                })
        
        # If too few relevant chunks, include section-based chunks
        if len(relevant_chunks) < 3:
            for chunk in chunks:
                if chunk not in relevant_chunks and chunk["type"] == "section":
                    section_title_lower = chunk.get("section", "").lower()
                    if any(keyword in section_title_lower for keyword in keywords):
                        relevant_chunks.append(chunk)
        
        # Sort by relevance score and return top chunks
        relevant_chunks.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return relevant_chunks[:15]  # Increased limit for better coverage
    
    async def _call_api(self, messages: List[Dict]) -> tuple[str, int]:
        """Make API call to language model.
        
        Args:
            messages: Chat messages
            
        Returns:
            Tuple of (response text, tokens used)
        """
        provider = self.config["model_config"]["provider"]
        model = self.config["model_config"]["model_name"]
        
        if provider == "openai":
            response = await asyncio.to_thread(
                self.api_client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=self.config["model_config"]["temperature"],
                max_tokens=self.config["model_config"]["max_tokens"]
            )
            
            return response.choices[0].message.content, response.usage.total_tokens
            
        elif provider == "anthropic":
            response = await asyncio.to_thread(
                self.api_client.messages.create,
                model=model,
                messages=messages,
                temperature=self.config["model_config"]["temperature"],
                max_tokens=self.config["model_config"]["max_tokens"]
            )
            
            return response.content[0].text, response.usage.total_tokens
    
    def _calculate_confidence(self, results: Dict) -> int:
        """Calculate confidence score for extraction.
        
        Args:
            results: Extraction results
            
        Returns:
            Confidence score (0-10)
        """
        score = 0
        max_score = 10
        
        # Categories extracted (4 points)
        categories_expected = 10
        categories_extracted = results["extraction_confidence"]["categories_extracted"]
        score += (categories_extracted / categories_expected) * 4
        
        # Validation passes (3 points)
        validation_passes = 0
        for category, data in results["extracted_data"].items():
            is_valid, _ = self.validator.validate_extraction(category, data)
            if is_valid:
                validation_passes += 1
        
        if categories_extracted > 0:
            score += (validation_passes / categories_extracted) * 3
        
        # Data completeness (3 points)
        empty_categories = sum(
            1 for cat, data in results["extracted_data"].items()
            if self.validator._is_empty_extraction(cat, data)
        )
        
        if categories_extracted > 0:
            non_empty_ratio = (categories_extracted - empty_categories) / categories_extracted
            score += non_empty_ratio * 3
        
        return round(score)
    
    async def batch_extract(self, markdown_dir: str, output_dir: str) -> List[Dict]:
        """Extract from multiple documents.
        
        Args:
            markdown_dir: Directory containing markdown files
            output_dir: Directory for output files
            
        Returns:
            List of extraction results
        """
        from .utils import get_markdown_files
        
        markdown_files = get_markdown_files(markdown_dir)
        self.logger.info(f"Found {len(markdown_files)} markdown files to process")
        
        results = []
        
        for md_file in tqdm(markdown_files, desc="Processing documents"):
            try:
                result = await self.extract_from_document(str(md_file))
                result["success"] = True
                
                # Save individual result
                state = result["metadata"].get("state", "unknown")
                output_path = Path(output_dir) / f"{state}_extraction.json"
                save_json(result, str(output_path))
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to process {md_file}: {e}")
                results.append({
                    "metadata": {"filename": md_file.name},
                    "success": False,
                    "error": str(e)
                })
        
        # Save combined results
        all_results_path = Path(output_dir) / "all_states_extracted.json"
        save_json(results, str(all_results_path))
        
        return results