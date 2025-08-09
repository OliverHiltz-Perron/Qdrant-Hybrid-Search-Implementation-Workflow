"""
Comprehensive validation models for all LLM prompts
Standardized to match each prompt's expected JSON schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# ===== SIMPLE FLAT SCHEMAS =====

class FundingSourcesResponse(BaseModel):
    """Validation model for FundingSources task"""
    funding_sources: str = Field(..., description="Semicolon-separated list of funding sources or 'None'")
    reference: str = Field(..., description="Chunk numbers only, format: 'Chunks: 23, 45, 67' or 'N/A'")
    additional_notes: Optional[str] = Field(None, description="Optional context or missing information")

class CandidateDefinitionResponse(BaseModel):
    """Validation model for CandidateDefinition task"""
    candidacy_definition: str = Field(..., description="Complete definition of candidacy")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional - only if definition references missing content")

class EvaluationMetricsResponse(BaseModel):
    """Validation model for EvaluationMetrics task"""
    outcome_goals: str = Field(..., description="Semicolon-separated list or 'None'")
    evaluation_metrics: str = Field(..., description="Semicolon-separated list or 'None'")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional - important context")

class EquityDisparityResponse(BaseModel):
    """Validation model for EquityDisparity task"""
    disparities_addressed: str = Field(..., description="Yes/No")
    disparity_description: str = Field(..., description="How disparities are acknowledged/described")
    affected_populations: str = Field(..., description="Semicolon-separated list of populations")
    strategies: str = Field(..., description="Semicolon-separated list of strategies")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional - important context")

class MonitoringAccountabilityResponse(BaseModel):
    """Validation model for MonitoringAccountability task"""
    monitoring_and_accountability: str = Field(..., description="Semicolon-separated list")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional context")

class StructuralDeterminantsResponse(BaseModel):
    """Validation model for StructuralDeterminants task"""
    structural_determinants_approach: str = Field(..., description="Description of approach")
    specific_supports: str = Field(..., description="Semicolon-separated list")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional context")

class TribalConsultationResponse(BaseModel):
    """Validation model for TribalConsultation task"""
    consultation_conducted: str = Field(..., description="Description of consultation")
    tribes_consulted: str = Field(..., description="Semicolon-separated list")
    consultation_process: str = Field(..., description="Description of process")
    reference: str = Field(..., description="Chunk numbers only")
    additional_notes: Optional[str] = Field(None, description="Optional context")

# ===== ARRAY-BASED SCHEMAS =====

class TraumaInformedProgram(BaseModel):
    """Sub-model for trauma-informed program"""
    program_name: Optional[str] = Field(None, description="Program name")
    trauma_description: Optional[str] = Field(None, description="Description of trauma-informed aspects")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class TraumaInformedResponse(BaseModel):
    """Validation model for TraumaInformed task"""
    trauma_informed_programs: List[TraumaInformedProgram] = Field(default_factory=list, description="List of trauma-informed programs, can be empty")
    
    @field_validator('trauma_informed_programs', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure the field is always a list, converting null to empty list"""
        if v is None:
            return []
        return v

class NonReimbursableProgram(BaseModel):
    """Sub-model for non-reimbursable program"""
    program_name: Optional[str] = Field(None, description="Program name")
    non_reimbursable_reason: Optional[str] = Field(None, description="Reason for non-reimbursable status")
    future_timeline: Optional[str] = Field(None, description="Future timeline or conditions")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class NonReimbursableProgramsResponse(BaseModel):
    """Validation model for NonReimbursablePrograms task"""
    non_reimbursable_programs: List[NonReimbursableProgram] = Field(..., description="List of non-reimbursable programs, must contain at least one element (null object if no data)")
    
    @field_validator('non_reimbursable_programs', mode='before')
    @classmethod
    def ensure_proper_format(cls, v):
        """Ensure proper format: array with at least one element (null object if no data)"""
        # Convert None to proper format
        if v is None:
            return [{
                "program_name": None,
                "non_reimbursable_reason": None,
                "future_timeline": None,
                "reference": "No non-reimbursable programs mentioned in provided chunks"
            }]
        # Convert empty array to proper format
        if isinstance(v, list) and len(v) == 0:
            return [{
                "program_name": None,
                "non_reimbursable_reason": None,
                "future_timeline": None,
                "reference": "No non-reimbursable programs mentioned in provided chunks"
            }]
        return v

class PreventionProgram(BaseModel):
    """Sub-model for prevention program"""
    program_name: str = Field(..., description="Program name")
    target_population: str = Field(..., description="Target population")
    evidence_rating: str = Field(..., description="Evidence rating")
    reference: str = Field(..., description="Chunk numbers only")

class PreventionProgramsResponse(BaseModel):
    """Validation model for PreventionPrograms task"""
    prevention_programs: List[PreventionProgram] = Field(default_factory=list, description="List of prevention programs, can be empty")
    additional_notes: Optional[str] = Field(None, description="Optional - important context")
    
    @field_validator('prevention_programs', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure the field is always a list, converting null to empty list"""
        if v is None:
            return []
        return v

# ===== COMPLEX NESTED SCHEMAS =====

class DeterminationProcess(BaseModel):
    """Sub-model for determination process"""
    description: str = Field(..., description="Complete process for determining eligibility")
    reference: str = Field(..., description="Chunk numbers only")

class ToolUsed(BaseModel):
    """Sub-model for tools used"""
    name: str = Field(..., description="Exact name of tool/system")
    purpose: str = Field(..., description="How it's used in eligibility determination")
    reference: str = Field(..., description="Chunk numbers only")

class DeterminationAuthority(BaseModel):
    """Sub-model for determination authority"""
    description: str = Field(..., description="Who determines eligibility")
    reference: str = Field(..., description="Chunk numbers only")

class EligibilityDeterminationResponse(BaseModel):
    """Validation model for EligibilityDetermination task"""
    determination_process: DeterminationProcess = Field(..., description="Complete process for determining eligibility")
    tools_used: List[ToolUsed] = Field(default_factory=list, description="Tools used in eligibility determination")
    determination_authority: Optional[DeterminationAuthority] = Field(None, description="Who determines eligibility")
    additional_notes: Optional[str] = Field(None, description="Optional - important context or missing information")

class OverallPlanPopulation(BaseModel):
    """Sub-model for overall plan population"""
    description: str = Field(..., description="Description of overall plan population")
    reference: str = Field(..., description="Chunk numbers only")

class ProgramPopulation(BaseModel):
    """Sub-model for program-specific population"""
    program_name: str = Field(..., description="Program name")
    target_population: str = Field(..., description="Target population for this program")
    reference: str = Field(..., description="Chunk numbers only")

class TargetPopulationsResponse(BaseModel):
    """Validation model for TargetPopulations task"""
    overall_plan_population: OverallPlanPopulation = Field(..., description="Overall plan population")
    program_populations: List[ProgramPopulation] = Field(default_factory=list, description="Program-specific populations")
    additional_notes: Optional[str] = Field(None, description="Optional context")

# ===== COMMUNITY ENGAGEMENT SCHEMA =====

class StakeholderInvolved(BaseModel):
    """Sub-model for stakeholder involved"""
    name: Optional[str] = Field(None, description="Organization or group name")
    type: Optional[str] = Field(None, description="Type: youth/families/providers/courts/etc.")
    role: Optional[str] = Field(None, description="Their involvement in process")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class EngagementMethod(BaseModel):
    """Sub-model for engagement method"""
    method: Optional[str] = Field(None, description="Meeting/survey/committee/etc.")
    description: Optional[str] = Field(None, description="Details of engagement, max 75 words")
    frequency: Optional[str] = Field(None, description="One-time/monthly/ongoing/etc.")
    phase: Optional[str] = Field(None, description="Planning/implementation/both")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class GovernanceStructure(BaseModel):
    """Sub-model for governance structure"""
    name: Optional[str] = Field(None, description="Committee/board name")
    purpose: Optional[str] = Field(None, description="Role in Title IV-E implementation")
    membership: Optional[str] = Field(None, description="Composition/representation")
    authority: Optional[str] = Field(None, description="Decision-making power")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class CommunityEngagementResponse(BaseModel):
    """Validation model for CommunityEngagement task"""
    stakeholders_involved: List[StakeholderInvolved] = Field(default_factory=list, description="List of stakeholders")
    engagement_methods: List[EngagementMethod] = Field(default_factory=list, description="List of engagement methods")
    governance_structures: List[GovernanceStructure] = Field(default_factory=list, description="List of governance structures")
    
    @field_validator('stakeholders_involved', 'engagement_methods', 'governance_structures', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure the field is always a list, converting null to empty list"""
        if v is None:
            return []
        return v

# ===== WORKFORCE SUPPORT SCHEMA =====

class TrainingPlan(BaseModel):
    """Sub-model for training plan"""
    target_audience: Optional[str] = Field(None, description="Who receives training")
    training_content: Optional[str] = Field(None, description="What training covers")
    delivery_method: Optional[str] = Field(None, description="How training is delivered")
    frequency: Optional[str] = Field(None, description="How often training occurs")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class OngoingSupport(BaseModel):
    """Sub-model for ongoing support"""
    type: Optional[str] = Field(None, description="Type of support")
    description: Optional[str] = Field(None, description="Description of support")
    recipient: Optional[str] = Field(None, description="Who receives support")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class CredentialingRequirement(BaseModel):
    """Sub-model for credentialing requirement"""
    role: Optional[str] = Field(None, description="Role/position")
    requirements: Optional[str] = Field(None, description="Required credentials/qualifications")
    certification_body: Optional[str] = Field(None, description="Who certifies/approves")
    reference: Optional[str] = Field(None, description="Chunk numbers only")

class WorkforceSupportResponse(BaseModel):
    """Validation model for WorkforceSupport task"""
    training_plans: List[TrainingPlan] = Field(default_factory=list, description="List of training plans")
    ongoing_support: List[OngoingSupport] = Field(default_factory=list, description="List of ongoing support")
    credentialing_requirements: List[CredentialingRequirement] = Field(default_factory=list, description="List of credentialing requirements")
    
    @field_validator('training_plans', 'ongoing_support', 'credentialing_requirements', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure the field is always a list, converting null to empty list"""
        if v is None:
            return []
        return v

# ===== TASK MODEL MAPPING =====

TASK_MODELS = {
    'FundingSources': FundingSourcesResponse,
    'CandidateDefinition': CandidateDefinitionResponse,
    'EligibilityDetermination': EligibilityDeterminationResponse,
    'EvaluationMetrics': EvaluationMetricsResponse,
    'PreventionPrograms': PreventionProgramsResponse,
    'StructuralDeterminants': StructuralDeterminantsResponse,
    'TargetPopulations': TargetPopulationsResponse,
    'TraumaInformed': TraumaInformedResponse,
    'TribalConsultation': TribalConsultationResponse,
    'EquityDisparity': EquityDisparityResponse,
    'MonitoringAccountability': MonitoringAccountabilityResponse,
    'NonReimbursablePrograms': NonReimbursableProgramsResponse,
    'CommunityEngagement': CommunityEngagementResponse,
    'WorkforceSupport': WorkforceSupportResponse,
    # Handle case variations
    'Communityengagement': CommunityEngagementResponse,
    'Workforcesupport': WorkforceSupportResponse,
}

def get_validation_model(task_type: str):
    """Get the appropriate validation model for a task type"""
    # Clean up task type (remove _LLM_Prompt suffix if present)
    clean_task_type = task_type.replace('_LLM_Prompt', '')
    
    # Try exact match first
    if clean_task_type in TASK_MODELS:
        return TASK_MODELS[clean_task_type]
    
    # Try case-insensitive match
    for key, model in TASK_MODELS.items():
        if key.lower() == clean_task_type.lower():
            return model
    
    # Try partial match
    for key, model in TASK_MODELS.items():
        if key.lower() in clean_task_type.lower() or clean_task_type.lower() in key.lower():
            return model
    
    raise ValueError(f"No validation model found for task type: {task_type}")

# ===== VALIDATION HELPERS =====

def validate_reference_format(reference: str) -> bool:
    """Validate that reference follows the correct format"""
    if reference in ['N/A', 'null', None]:
        return True
    return reference.startswith('Chunks: ') or reference.startswith('Chunk: ')

def validate_semicolon_list(value: str) -> bool:
    """Validate semicolon-separated list format"""
    if value == 'None':
        return True
    # Should not end with semicolon unless it's the only character
    if value.endswith(';') and len(value) > 1:
        return False
    return True