"""Enhanced prompt templates for FFPSA prevention plan extraction."""

from typing import Dict, List

EXTRACTION_PROMPTS = {
    "programs_waiting_to_add": {
        "prompt": """Extract information about prevention programs that are NOT currently reimbursable but are intended to be added pending evaluation by the clearinghouse.

Look for programs mentioned as:
- "waiting for clearinghouse review"
- "pending approval" or "pending clearinghouse approval"  
- "to be added" or "plan to add"
- "under consideration for reimbursement"
- "not yet rated by Title IV-E Prevention Services Clearinghouse"
- "scheduled to be reviewed"
- "exploring" or "considering" for future implementation
- Programs where reimbursement is explicitly NOT being requested currently

DO NOT include programs that are already approved or currently being implemented with reimbursement.

Return as JSON:
{
    "programs": [
        {
            "name": "exact program name as mentioned",
            "quote": "the exact sentence or paragraph mentioning this program",
            "status": "current status (e.g., 'pending clearinghouse review', 'not yet rated', 'review completed but not approved')",
            "timeline": "when they plan to add it (if mentioned)",
            "reason_waiting": "why it's waiting (e.g., 'clearinghouse review', 'not meeting criteria')"
        }
    ],
    "total_count": number of programs waiting to be added
}

If no programs are waiting to be added, return {"programs": [], "total_count": 0}""",
        "type": "chunk_based"
    },
    
    "target_populations": {
        "prompt": """Extract ALL groups explicitly described as intended recipients of the prevention plan/programs.

Be comprehensive - include:
- Age-specific groups (e.g., "children ages 0-5", "youth ages 11-18")
- Risk categories (e.g., "at imminent risk of foster care", "candidates for foster care")
- Family situations (e.g., "families with prior child welfare involvement")
- Special populations (e.g., "pregnant and parenting foster youth")
- Geographic populations (e.g., "rural families", "all 75 counties")
- Specific conditions (e.g., "children with failure to thrive", "families affected by domestic violence")
- Parent characteristics (e.g., "parents who were in foster care as children")

Return as JSON:
{
    "populations": [
        {
            "group": "population name/description",
            "quote": "exact text describing this population",
            "criteria": "specific eligibility criteria or conditions for this group",
            "age_range": "age range if specified (e.g., '0-5', '11-18')",
            "program_specific": "which program serves this population (if mentioned)"
        }
    ],
    "primary_population": "main target population if explicitly stated",
    "total_populations_identified": number of distinct populations
}""",
        "type": "chunk_based"
    },
    
    "eligibility_determination": {
        "prompt": """Extract comprehensive information on how eligibility is determined for prevention services/programs.

Look for:
1. Screening/Assessment Tools:
   - Specific named tools (e.g., "FFPSA eligibility screen", "SDM", "FAST")
   - Risk assessment instruments
   - Safety assessment tools
   - Family functioning assessments

2. Decision Process:
   - Who completes assessments (e.g., "FSW", "investigator")
   - Who approves decisions (e.g., "supervisor review")
   - Timeline for determinations
   - Override provisions

3. Eligibility Criteria:
   - Specific factors that qualify someone
   - Candidacy definitions
   - Automatic qualifiers
   - Duration of eligibility

Return as JSON:
{
    "determination_method": "comprehensive description of how eligibility is determined",
    "screening_tools": ["list ALL specific tools/assessments mentioned"],
    "decision_maker": "who makes the eligibility decision (include approval hierarchy)",
    "candidacy_definition": "how 'candidate for foster care' is defined",
    "eligibility_duration": "how long eligibility lasts",
    "quotes": [
        "include 3-5 key quotes that best explain the process"
    ]
}""",
        "type": "chunk_based"
    },
    
    "effectiveness_outcomes": {
        "prompt": """Extract stated outcome goals for overall program/system effectiveness.

Focus on SYSTEM-LEVEL or PLAN-LEVEL indicators, NOT individual program metrics.

Categories to capture:
1. Primary outcomes:
   - Foster care entry reduction
   - Maltreatment recurrence reduction
   - Reunification/permanency rates
   - Placement stability

2. Secondary outcomes:
   - Family functioning improvements
   - Child well-being measures
   - System involvement reduction

3. Specific targets:
   - Percentage reductions
   - Timeline goals (e.g., "at 6, 12, 18, 24 months")
   - Baseline comparisons

Return as JSON:
{
    "outcome_goals": [
        {
            "goal": "specific outcome goal",
            "metric": "how it will be measured",
            "target": "specific target if mentioned (e.g., '20% reduction', '17-percent decline')",
            "timeline": "measurement intervals (e.g., '6, 12, 18, and 24 months')",
            "comparison_group": "if mentioned (e.g., 'propensity-matched comparison sample')",
            "quote": "exact text stating this goal"
        }
    ],
    "has_specific_targets": true/false,
    "evaluation_approach": "brief description of evaluation methodology if mentioned"
}""",
        "type": "full_context"
    },
    
    "monitoring_accountability": {
        "prompt": """Extract comprehensive information about implementation monitoring and accountability structures.

Look for ALL mentions of:
1. Monitoring Systems:
   - Continuous Quality Improvement (CQI) processes
   - Contract monitoring procedures
   - Performance reviews
   - Data collection systems

2. Fidelity Monitoring:
   - Model fidelity requirements
   - Certification/accreditation oversight
   - National model oversight (e.g., SafeCare, FFT)

3. Review Processes:
   - Frequency (monthly, quarterly, semiannual, annual)
   - Types of reviews (case reviews, OSRI, interviews)
   - Who conducts reviews

4. Accountability Structures:
   - Oversight roles (program managers, assistant directors)
   - Reporting requirements
   - Feedback loops

Return as JSON:
{
    "has_monitoring_system": true/false,
    "cqi_mentioned": true/false,
    "cqi_details": "description of CQI process if mentioned",
    "fidelity_monitoring": true/false,
    "fidelity_details": "how fidelity is monitored",
    "review_frequency": {
        "monthly": ["what's reviewed monthly"],
        "quarterly": ["what's reviewed quarterly"],
        "semiannual": ["what's reviewed semiannually"],
        "annual": ["what's reviewed annually"]
    },
    "monitoring_description": "comprehensive description of monitoring approach",
    "accountability_roles": ["list of oversight positions/entities"],
    "external_evaluator": "name/details if mentioned",
    "quotes": [
        "include 5-8 key quotes covering different aspects of monitoring"
    ]
}""",
        "type": "full_context"
    },
    
    "workforce_support": {
        "prompt": """Extract comprehensive information about workforce training/support AND provider credentialing requirements.

Part 1 - Workforce Support:
- Training initiatives (with specific names like "Family First Fits Us")
- Implementation support (coaching calls, technical assistance)
- Professional development programs
- University partnerships
- Ongoing education requirements
- Support structures (meetings, cafés, kick-offs)

Part 2 - Credentialing/Qualifications:
- Model-specific certifications (e.g., PCIT, FFT, FCT)
- Licensing requirements
- Accreditation requirements
- Training phases/timelines
- Supervisor qualifications

Return as JSON:
{
    "workforce_training": {
        "has_training_plan": true/false,
        "training_programs": [
            {
                "name": "program name",
                "description": "what it covers",
                "target_audience": "who receives this training",
                "frequency": "when/how often"
            }
        ],
        "implementation_support": ["list of support mechanisms"],
        "university_partnerships": ["list if mentioned"],
        "quotes": ["3-5 key quotes about workforce training"]
    },
    "credentialing": {
        "has_requirements": true/false,
        "requirements_by_program": {
            "program_name": ["specific requirements for this program"]
        },
        "general_requirements": ["requirements for all providers"],
        "quotes": ["2-3 key quotes about credentialing"]
    }
}""",
        "type": "chunk_based"
    },
    
    "funding_sources": {
        "prompt": """Extract ALL funding streams referenced in the plan.

Include any mention of:
- Title IV-E (including transitional payments)
- Title IV-B
- Medicaid
- TANF
- State general funds
- DCFS funds/contracts
- Local funds
- Private funds/philanthropy
- Federal grants (specify which)
- Match requirements (e.g., "15% match")
- Any other funding source

Return as JSON:
{
    "funding_sources": [
        {
            "source": "funding source name",
            "details": "any specifics (e.g., match percentages, what it funds)",
            "quote": "exact text mentioning this funding source"
        }
    ],
    "has_multiple_sources": true/false,
    "match_requirements": ["list any match requirements mentioned"]
}""",
        "type": "chunk_based"
    },
    
    "trauma_informed_delivery": {
        "prompt": """Determine if the plan mentions trauma-informed approaches to service delivery.

Look for ANY mention of:
- "trauma-informed" programs, care, practices, or evidence-based practices
- Trauma-specific interventions (TF-CBT, CPT, CPP)
- Trauma training for staff or providers
- Trauma-responsive approaches
- Trauma-focused therapies
- Programs described as addressing trauma
- Protective Factors Framework (if linked to trauma)

Return as JSON:
{
    "uses_trauma_informed_approach": true/false,
    "trauma_specific_programs": ["list specific trauma-focused programs mentioned"],
    "training_components": ["list trauma-related training mentioned"],
    "evidence_quotes": [
        "include 3-5 quotes showing trauma-informed approach"
    ]
}

Return uses_trauma_informed_approach as true if ANY mention is found.""",
        "type": "chunk_based"
    },
    
    "equity_disparity_reduction": {
        "prompt": """Determine if and how the plan addresses equity or disparity reduction.

Look for BOTH explicit and implicit approaches:

Explicit mentions:
- Racial equity, disparities, or disproportionality
- LGBTQ+ families or youth
- Cultural responsiveness or competence
- Equity goals or initiatives

Implicit approaches:
- Rural population considerations
- Poverty/economic factors in service delivery
- Parent voice/involvement (e.g., Parent Advisory Council)
- Demographic matching in evaluations
- Geographic equity (e.g., "all 75 counties")
- Special populations (teen parents, DV victims)

Return as JSON:
{
    "addresses_equity": true/false,
    "explicit_equity_focus": true/false,
    "equity_approach": "comprehensive description of how equity is addressed (explicitly or implicitly)",
    "targeted_groups": ["list all groups mentioned in equity context"],
    "strategies": ["specific strategies employed"],
    "parent_voice_mechanisms": ["ways parents are involved in planning/feedback"],
    "quotes": [
        "include 3-5 quotes showing equity considerations"
    ]
}

Note: Return addresses_equity as true if there are meaningful efforts to address disparities, even if not explicitly framed as "equity".""",
        "type": "full_context"
    },
    
    "structural_determinants": {
        "prompt": """Determine if the plan addresses structural determinants of child welfare involvement.

Look for programs, services, or referrals that address:
- Economic support (poverty, income, employment)
- Housing/homelessness (including transitional housing)
- Childcare access
- Healthcare access (physical and mental health)
- Transportation
- Food security (WIC, nutrition programs)
- Employment/job training
- Education support (for parents or children)
- Substance abuse treatment (especially if comprehensive)
- Domestic violence services
- Basic needs (diapers, clothing)

Consider BOTH:
1. Direct services provided
2. Referrals to community resources

Return as JSON:
{
    "addresses_structural_determinants": true/false,
    "direct_services": ["services provided directly by programs"],
    "referral_services": ["services accessed through referrals"],
    "support_types": ["categorized list (e.g., 'housing', 'economic support')"],
    "specific_programs": {
        "program_name": ["structural supports this program provides"]
    },
    "quotes": [
        "include 3-5 quotes showing how structural needs are addressed"
    ]
}

Return addresses_structural_determinants as true if ANY structural supports are mentioned, even if not explicitly framed as addressing "structural determinants".""",
        "type": "full_context"
    },
    
    "tribal_consultation": {
        "prompt": """Extract information about tribal consultation in the planning process.

Look for:
- Mentions of tribal consultation, collaboration, or engagement
- Specific tribes consulted
- Tribal representatives involved
- Consultation process or meetings
- Tribal sovereignty considerations
- Services for tribal families

Return as JSON:
{
    "consultation_conducted": true/false/"not mentioned",
    "tribes_consulted": ["list of specific tribes if mentioned"],
    "consultation_process": "description of how consultation occurred",
    "tribal_services": "any specific services for tribal families",
    "quotes": ["exact quotes about tribal consultation"]
}

If no mention of tribal consultation is found, return consultation_conducted as "not mentioned".""",
        "type": "chunk_based"
    },
    
    "community_engagement": {
        "prompt": """Extract information about community and stakeholder engagement in developing/implementing the plan.

Look for:
- Stakeholder groups involved (judges, attorneys, providers, parents)
- Parent/youth advisory groups
- Community meetings or forums
- Provider engagement sessions
- Feedback mechanisms
- Ongoing engagement structures

Return as JSON:
{
    "stakeholders_engaged": [
        {
            "group": "stakeholder group name",
            "role": "how they were involved",
            "quote": "text mentioning their involvement"
        }
    ],
    "engagement_methods": ["list of methods used (e.g., focus groups, meetings)"],
    "ongoing_mechanisms": ["structures for continued engagement"],
    "parent_voice": "specific ways parent voice is included",
    "has_formal_engagement": true/false
}""",
        "type": "chunk_based"
    },
    
    "prevention_programs_detail": {
        "prompt": """Extract detailed information about each prevention program being implemented.

For EACH program mentioned as currently implemented or approved, capture:
- Program name
- Target population with age ranges
- Implementation fidelity requirements
- Adaptations or modifications
- Evidence rating (well-supported, supported, promising)
- Geographic coverage
- Provider requirements

Return as JSON:
{
    "implemented_programs": [
        {
            "program_name": "exact name",
            "evidence_rating": "clearinghouse rating if mentioned",
            "target_ages": "age range served",
            "target_population": "detailed population description",
            "fidelity_requirements": "how fidelity is maintained",
            "adaptations": "any modifications to the model",
            "geographic_coverage": "where available",
            "provider_requirements": "who can deliver this",
            "key_components": ["main elements of the program"],
            "outcomes_measured": ["specific outcomes for this program"]
        }
    ],
    "total_programs": number of programs
}""",
        "type": "chunk_based"
    }
}

def get_prompt(category: str) -> Dict:
    """Get prompt configuration for a specific category.
    
    Args:
        category: The extraction category
        
    Returns:
        Dictionary with prompt and metadata
    """
    if category not in EXTRACTION_PROMPTS:
        raise ValueError(f"Unknown extraction category: {category}")
    
    return EXTRACTION_PROMPTS[category]

def get_all_categories() -> List[str]:
    """Get list of all extraction categories.
    
    Returns:
        List of category names
    """
    return list(EXTRACTION_PROMPTS.keys())

def get_categories_by_type(extraction_type: str) -> List[str]:
    """Get categories that use a specific extraction type.
    
    Args:
        extraction_type: Either 'full_context' or 'chunk_based'
        
    Returns:
        List of category names
    """
    return [
        cat for cat, config in EXTRACTION_PROMPTS.items()
        if config['type'] == extraction_type
    ]

def get_required_categories() -> List[str]:
    """Get categories that are required per the extraction rules.
    
    Returns:
        List of required category names
    """
    # Based on the extraction rules document
    return [
        "programs_waiting_to_add",
        "target_populations", 
        "eligibility_determination",
        "effectiveness_outcomes",
        "monitoring_accountability",
        "workforce_support",
        "funding_sources",
        "trauma_informed_delivery",
        "equity_disparity_reduction",
        "structural_determinants"
    ]

def get_optional_categories() -> List[str]:
    """Get categories that provide additional valuable context.
    
    Returns:
        List of optional category names
    """
    return [
        "tribal_consultation",
        "community_engagement",
        "prevention_programs_detail"
    ]