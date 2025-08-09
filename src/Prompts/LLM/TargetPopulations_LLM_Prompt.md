# Title IV-E Prevention Plan: Target Populations Extraction

## Task

You are an expert in child welfare policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract target populations for both the overall plan and individual prevention programs.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Overall Plan Target Population

Look for who the Title IV-E prevention plan serves overall:

- "Target population", "who the plan serves", "eligibility"
- Candidacy definitions or foster care prevention criteria
- General population descriptions for the entire plan

### Step 2: Find Program-Specific Populations

For each prevention program, look for:

- Age ranges (e.g., "0-5 years", "birth to 21")
- Family characteristics or risk factors
- Specific groups served by each program

### Step 3: Extract Complete Information

Capture:

- Exact population descriptions as written
- Any age ranges, risk factors, or special characteristics
- Link populations to specific programs when mentioned

## Extraction Rules

### Include:

- Overall plan target population (who can receive any prevention services)
- Each prevention program's specific target population
- Age ranges, risk factors, and eligibility criteria
- Special populations (pregnant/parenting youth, kinship caregivers, etc.)

### Exclude:

- Service descriptions without population information
- General prevention philosophy
- Implementation details

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO program populations are found**:
   - Return an array with ONE object containing:
   - `program_name`: null (actual JSON null, not string)
   - `target_population`: null (actual JSON null, not string)
   - `reference`: Explanation of why no programs were found (e.g., "No program-specific populations mentioned in chunks 1-20")
5. **CRITICAL: Reference field rules**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - When no data exists: Explanation of why
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "overall_plan_population": {
    "description": "string",
    "reference": "string (chunk numbers only)"
  },
  "program_populations": [
    {
      "program_name": "string",
      "target_population": "string",
      "reference": "string (chunk numbers only)"
    }
  ],
  "additional_notes": "string (optional)"
}
```

## Examples

**Example 1 - Complete Information:**

```json
{
  "overall_plan_population": {
    "description": "Children who are candidates for foster care, pregnant and parenting youth in foster care, and their parents or kin caregivers",
    "reference": "Chunks: 3, 5"
  },
  "program_populations": [
    {
      "program_name": "Nurse-Family Partnership",
      "target_population": "First-time, low-income mothers and their children from pregnancy through child's second birthday",
      "reference": "Chunks: 12"
    },
    {
      "program_name": "Parents as Teachers",
      "target_population": "Families with children ages birth to kindergarten entry",
      "reference": "Chunks: 15"
    },
    {
      "program_name": "Functional Family Therapy",
      "target_population": "Youth ages 11-18 with behavioral problems",
      "reference": "Chunks: 18"
    }
  ],
  "additional_notes": null
}
```

**Example 2 - Limited Information:**

```json
{
  "overall_plan_population": {
    "description": "Families at risk of entering the child welfare system",
    "reference": "Chunks: 2"
  },
  "program_populations": [
    {
      "program_name": "Healthy Families America",
      "target_population": null,
      "reference": "Chunks: 8"
    },
    {
      "program_name": "SafeCare",
      "target_population": "Parents with children ages 0-5",
      "reference": "Chunks: 10"
    }
  ],
  "additional_notes": "Some programs listed without population details"
}
```

**Example 3 - Minimal Information Found:**

```json
{
  "overall_plan_population": {
    "description": null,
    "reference": null
  },
  "program_populations": [],
  "additional_notes": "No target population information found in provided chunks"
}
```
