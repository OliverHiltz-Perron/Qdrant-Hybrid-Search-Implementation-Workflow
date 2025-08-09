# Title IV-E Prevention Plan: Workforce Support Extraction

## Task

You are an expert in child welfare workforce development. You will review provided text chunks from a State's Title IV-E prevention plan and extract information about workforce training, support, and professional development.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Workforce Content

Look for sections mentioning:

- Workforce development, training, or support
- Staff development or professional development
- Worker qualifications or credentials
- Training plans, curricula, or competencies
- Supervision, coaching, or consultation models

### Step 2: Categorize by Type

Organize findings into:

- **Training Plans**: Formal training programs and curricula
- **Ongoing Support**: Supervision, coaching, consultation, mentoring
- **Credentialing Requirements**: Certifications, licenses, qualifications

### Step 3: Extract Complete Information

For each element found:

- What is provided (training/support type)
- Who receives it (target workforce)
- How it's delivered (method/format)
- When/how often (frequency/duration)

## Extraction Rules

### Include:

- ALL training mentioned (initial and ongoing)
- Supervision and support structures
- Credentialing and qualification requirements
- Training for both state and contracted workforce
- Future plans or intentions for workforce development

### Exclude:

- General statements without specifics
- Budget details
- Unrelated administrative procedures

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO data is found for array fields**:
   - For `training_plans`: Return array with ONE object - all fields null (actual JSON null, not string), reference explains why
   - For `ongoing_support`: Return array with ONE object - all fields null (actual JSON null, not string), reference explains why
   - For `credentialing_requirements`: Return array with ONE object - all fields null (actual JSON null, not string), reference explains why
5. **CRITICAL: Reference field rules**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - When no data exists: Explanation (e.g., "No training plans mentioned in chunks 1-20")
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "training_plans": [
    {
      "description": "string (training program details, max 100 words)",
      "target_audience": "string (who receives training)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "ongoing_support": [
    {
      "type": "string (supervision/coaching/consultation/etc.)",
      "description": "string (support details, max 75 words)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "credentialing_requirements": [
    {
      "requirement": "string (credential/qualification needed)",
      "applies_to": "string (which workers need this)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "additional_notes": "string (optional - important context or missing information)"
}
```

## Examples

**Example 1 - Comprehensive Workforce Information:**

```json
{
  "training_plans": [
    {
      "description": "All child welfare workers must complete 40 hours of pre-service training covering child development, trauma-informed care, and family engagement before handling cases",
      "target_audience": "New child welfare workers",
      "reference": "Chunks: 15, 18"
    },
    {
      "description": "Annual 24-hour in-service training requirement including 8 hours on cultural competency, 8 hours on evidence-based practices, and 8 hours on legal updates",
      "target_audience": "All child welfare staff",
      "reference": "Chunks: 18"
    },
    {
      "description": "Specialized FFPSA training curriculum covering prevention services, eligibility determination, and documentation requirements - 16 hours total",
      "target_audience": "Prevention services workers and supervisors",
      "reference": "Chunks: 22, 25"
    }
  ],
  "ongoing_support": [
    {
      "type": "Supervision",
      "description": "Weekly individual supervision for all caseworkers, bi-weekly group supervision for teams, monthly consultation with clinical experts",
      "reference": "Chunks: 28"
    },
    {
      "type": "Coaching",
      "description": "Monthly reflective coaching sessions for workers implementing evidence-based practices, quarterly fidelity observations with feedback",
      "reference": "Chunks: 30, 32"
    }
  ],
  "credentialing_requirements": [
    {
      "requirement": "Bachelor's degree in social work or related field",
      "applies_to": "All child welfare caseworkers",
      "reference": "Chunks: 12"
    },
    {
      "requirement": "Clinical license (LCSW, LMFT, or LPC)",
      "applies_to": "Mental health service providers",
      "reference": "Chunks: 12"
    }
  ],
  "additional_notes": null
}
```

**Example 2 - Limited Information:**

```json
{
  "training_plans": [
    {
      "description": "State will develop comprehensive training plan for prevention services implementation",
      "target_audience": "Child welfare workforce",
      "reference": "Chunks: 5"
    }
  ],
  "ongoing_support": [
    {
      "type": "Technical assistance",
      "description": "Ongoing technical assistance will be provided to support EBP implementation",
      "reference": "Chunks: 7"
    }
  ],
  "credentialing_requirements": null,
  "additional_notes": "Workforce section appears incomplete - specific training details may be in development"
}
```

**Example 3 - No Workforce Information Found:**

```json
{
  "training_plans": null,
  "ongoing_support": null,
  "credentialing_requirements": null,
  "additional_notes": "No workforce training or support information found in provided chunks"
}
```
