"""
Prompt Manager for RAG Pipeline
Handles all 4 prompt types: BM25, RAG, Reranker, and LLM
Provides unified interface for loading prompts by task type
"""

import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

class PromptManager:
    """Manages all prompt types for each task"""
    
    def __init__(self, prompts_dir: Path = None):
        """Initialize with prompts directory"""
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "Prompts"
        self.prompts_dir = prompts_dir
        
        # Task type mappings (supports various naming conventions)
        self.task_mappings = {
            'candidatedefinition': 'CandidateDefinition',
            'candidate_definition': 'CandidateDefinition',
            'eligibilitydetermination': 'EligibilityDetermination',
            'eligibility_determination': 'EligibilityDetermination',
            'nonreimbursableprograms': 'NonReimbursablePrograms',
            'non_reimbursable_programs': 'NonReimbursablePrograms',
            'fundingsources': 'FundingSources',
            'funding_sources': 'FundingSources',
            'preventionprograms': 'PreventionPrograms',
            'prevention_programs': 'PreventionPrograms',
            'evaluationmetrics': 'EvaluationMetrics',
            'evaluation_metrics': 'EvaluationMetrics',
            'structuraldeterminants': 'StructuralDeterminants',
            'structural_determinants': 'StructuralDeterminants',
            'targetpopulations': 'TargetPopulations',
            'target_populations': 'TargetPopulations',
            'traumainformed': 'TraumaInformed',
            'trauma_informed': 'TraumaInformed',
            'tribalconsultation': 'TribalConsultation',
            'tribal_consultation': 'TribalConsultation',
            'equitydisparity': 'EquityDisparity',
            'equity_disparity': 'EquityDisparity',
            'monitoringaccountability': 'MonitoringAccountability',
            'monitoring_accountability': 'MonitoringAccountability'
        }
    
    def normalize_task_type(self, task_type: str) -> str:
        """Normalize task type to standard format"""
        # Remove common suffixes
        cleaned = task_type.replace('_LLM_Prompt', '').replace('_prompt', '').replace('.md', '')
        
        # Convert to lowercase for lookup
        lower = cleaned.lower()
        
        # Check mappings
        if lower in self.task_mappings:
            return self.task_mappings[lower]
        
        # Check if it's already a proper task name
        for proper_name in self.task_mappings.values():
            if proper_name.lower() == lower:
                return proper_name
        
        # If not found, try to construct it
        # Convert snake_case or kebab-case to PascalCase
        parts = cleaned.replace('-', '_').split('_')
        return ''.join(part.capitalize() for part in parts)
    
    def load_prompt(self, prompt_file: Path, logger: Optional[logging.Logger] = None) -> str:
        """Load a single prompt file"""
        if not prompt_file.exists():
            if logger:
                logger.warning(f"Prompt file not found: {prompt_file}")
            return ""
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if logger:
                logger.info(f"Loaded prompt from {prompt_file.name} ({len(content)} chars)")
            
            return content
        except Exception as e:
            if logger:
                logger.error(f"Error loading prompt {prompt_file}: {e}")
            return ""
    
    def get_all_prompts(self, task_type: str, logger: Optional[logging.Logger] = None) -> Dict[str, str]:
        """Get all 4 prompts for a task type"""
        # Normalize task type
        normalized_task = self.normalize_task_type(task_type)
        
        if logger:
            logger.info(f"Loading prompts for task: {normalized_task}")
        
        # Define all 4 prompt files with new folder structure
        prompt_files = {
            'bm25': self.prompts_dir / "BM25" / f"{normalized_task}_BM25.md",
            'rag': self.prompts_dir / "RAG" / f"{normalized_task}_RAG.md",
            'reranker': self.prompts_dir / "Reranker" / f"{normalized_task}_Reranker_Prompt.md",
            'llm': self.prompts_dir / "LLM" / f"{normalized_task}_LLM_Prompt.md"
        }
        
        # Load all prompts
        prompts = {}
        for prompt_type, prompt_file in prompt_files.items():
            prompts[prompt_type] = self.load_prompt(prompt_file, logger)
        
        # Check for required prompts
        if not prompts['llm'] and logger:
            logger.warning(f"LLM prompt not found for {normalized_task}")
        
        return prompts
    
    def get_bm25_keywords(self, task_type: str, logger: Optional[logging.Logger] = None) -> list:
        """Get BM25 keywords as a list"""
        prompts = self.get_all_prompts(task_type, logger)
        bm25_content = prompts.get('bm25', '')
        
        if not bm25_content:
            # Fallback to generating from task name
            if logger:
                logger.info(f"No BM25 prompt found, generating keywords from task name")
            
            # Generate keywords from task name
            words = []
            # Split camelCase
            import re
            parts = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', task_type)
            words.extend([p.lower() for p in parts])
            
            # Add common variations
            if 'non' in words and 'reimbursable' in words:
                words.extend(['not reimbursable', 'not claiming', 'will not claim'])
            if 'funding' in words:
                words.extend(['Title IV-E', 'budget', 'finance'])
            
            return words
        
        # Parse comma-separated keywords
        keywords = [kw.strip() for kw in bm25_content.split(',') if kw.strip()]
        return keywords
    
    def get_rag_query(self, task_type: str, logger: Optional[logging.Logger] = None) -> str:
        """Get natural language RAG query"""
        prompts = self.get_all_prompts(task_type, logger)
        rag_query = prompts.get('rag', '')
        
        if not rag_query:
            # Fallback to generating from task name
            if logger:
                logger.info(f"No RAG prompt found, generating query from task name")
            
            # Generate natural language query
            normalized = self.normalize_task_type(task_type)
            
            # Create sensible defaults
            query_map = {
                'CandidateDefinition': 'Title IV-E candidacy definition eligibility criteria foster care candidates',
                'NonReimbursablePrograms': 'programs not reimbursable not claiming Title IV-E future reimbursement',
                'FundingSources': 'Title IV-E funding sources budget financing federal state local funds',
                'EligibilityDetermination': 'eligibility determination process assessment tools screening',
                'PreventionPrograms': 'prevention programs services evidence-based interventions',
                'TargetPopulations': 'target populations served demographics age groups families',
                'EvaluationMetrics': 'evaluation metrics outcomes measurement data collection',
                'StructuralDeterminants': 'structural determinants social factors poverty housing',
                'TraumaInformed': 'trauma-informed care services approaches trauma-responsive',
                'TribalConsultation': 'tribal consultation engagement government-to-government',
                'EquityDisparity': 'equity disparities racial ethnic disproportionality',
                'MonitoringAccountability': 'monitoring accountability oversight quality assurance'
            }
            
            rag_query = query_map.get(normalized, f"{normalized} related information")
        
        return rag_query

def create_prompt_examples():
    """Create example prompt files for all task types"""
    prompts_dir = Path(__file__).parent / "Prompts"
    prompts_dir.mkdir(exist_ok=True)
    
    # Example content for each prompt type
    examples = {
        'CandidateDefinition': {
            'bm25': 'candidacy, candidate, definition, eligibility, foster care, imminent risk, Title IV-E, prevention services',
            'rag': 'What is the Title IV-E candidacy definition and eligibility criteria for children at risk of entering foster care? Include specific requirements and assessment criteria.'
        },
        'NonReimbursablePrograms': {
            'bm25': 'non-reimbursable, not claiming, will not claim, promising practice, pending clearinghouse, future reimbursement, not eligible, supported, well-supported',
            'rag': 'Which prevention programs or services are not currently eligible for Title IV-E reimbursement? Include programs pending clearinghouse review or rated as promising practices that the state will not claim.'
        },
        'FundingSources': {
            'bm25': 'funding, Title IV-E, Title IV-B, TANF, Medicaid, state funds, federal, budget, finance, block grant',
            'rag': 'What are all the funding sources for the Title IV-E prevention plan? Include federal funding streams like Title IV-E, Title IV-B, TANF, Medicaid, and any state or local funding sources.'
        }
    }
    
    # Create example files
    created_files = []
    for task_type, content in examples.items():
        # BM25 file
        bm25_file = prompts_dir / f"{task_type}_BM25.md"
        if not bm25_file.exists():
            with open(bm25_file, 'w', encoding='utf-8') as f:
                f.write(content['bm25'])
            created_files.append(bm25_file)
        
        # RAG file
        rag_file = prompts_dir / f"{task_type}_RAG.md"
        if not rag_file.exists():
            with open(rag_file, 'w', encoding='utf-8') as f:
                f.write(content['rag'])
            created_files.append(rag_file)
    
    return created_files

def main():
    """Test prompt manager functionality"""
    parser = argparse.ArgumentParser(description='Prompt Manager for RAG Pipeline')
    parser.add_argument('--task', help='Task type to load prompts for')
    parser.add_argument('--create-examples', action='store_true', help='Create example BM25 and RAG prompt files')
    parser.add_argument('--list-tasks', action='store_true', help='List all available task types')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    manager = PromptManager()
    
    if args.create_examples:
        created = create_prompt_examples()
        logger.info(f"Created {len(created)} example prompt files")
        for f in created:
            logger.info(f"  - {f.name}")
    
    elif args.list_tasks:
        logger.info("Available task types:")
        seen = set()
        for task in manager.task_mappings.values():
            if task not in seen:
                logger.info(f"  - {task}")
                seen.add(task)
    
    elif args.task:
        # Load and display prompts for a task
        prompts = manager.get_all_prompts(args.task, logger)
        
        print("\n" + "="*80)
        print(f"PROMPTS FOR TASK: {manager.normalize_task_type(args.task)}")
        print("="*80)
        
        for prompt_type, content in prompts.items():
            print(f"\n{prompt_type.upper()} PROMPT:")
            print("-"*40)
            if content:
                print(content[:200] + "..." if len(content) > 200 else content)
            else:
                print("(Not found)")
        
        # Also show parsed versions
        print("\n" + "="*80)
        print("PARSED QUERIES")
        print("="*80)
        
        keywords = manager.get_bm25_keywords(args.task, logger)
        print(f"\nBM25 Keywords: {keywords}")
        
        rag_query = manager.get_rag_query(args.task, logger)
        print(f"\nRAG Query: {rag_query}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()