# Title IV-E Prevention Plan: Prevention Programs Extraction

## Task

You are an expert in evidence-based prevention programs. You will review provided text chunks from a State's Title IV-E prevention plan and extract information about prevention programs being implemented.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Prevention Programs

Look for:

- Named programs or services being implemented
- Evidence-based programs (EBPs)
- Service array listings
- Program tables or lists

### Step 2: For Each Program, Find:

- Target population served
- Evidence rating (Well-Supported, Supported, Promising)
- Link this information to the specific program

### Step 3: Extract Complete Information

- Ensure each program has its associated population and rating
- Use exact language from the document

## Extraction Rules

### Include:

- All named prevention programs/services
- Target population for EACH program
- Evidence rating for EACH program
- Keep information grouped by program

### Exclude:

- Program implementation details
- Extensive program descriptions
- Budget information
- Fidelity monitoring details

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO programs are found**:
   - Return an array with ONE object containing:
   - `program_name`: null (actual JSON null, not string)
   - `target_population`: null (actual JSON null, not string)
   - `evidence_rating`: null (actual JSON null, not string)
   - `reference`: Explanation of why no programs were found (e.g., "No prevention programs mentioned in chunks 1-20")
5. **CRITICAL: Reference field rules**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found - When no data exists: Explanation of why (e.g., "No prevention programs mentioned in chunks 1-20")
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "prevention_programs": [
    {
      "program_name": "string",
      "target_population": "string",
      "evidence_rating": "string",
      "reference": "string (chunk numbers only)"
    }
  ],
  "additional_notes": "string (optional - important context)"
}
```

## Examples

**Example 1 - Multiple Programs:**

```json
{
  "prevention_programs": [
    {
      "program_name": "Parents as Teachers (PAT)",
      "target_population": "Families with children 0-5",
      "evidence_rating": "Well-Supported",
      "reference": "Chunks: 12, 15"
    },
    {
      "program_name": "Healthy Families America (HFA)",
      "target_population": "New and expectant parents",
      "evidence_rating": "Well-Supported",
      "reference": "Chunks: 15, 18"
    },
    {
      "program_name": "Functional Family Therapy (FFT)",
      "target_population": "Youth ages 11-18 with behavioral problems",
      "evidence_rating": "Well-Supported",
      "reference": "Chunks: 23"
    },
    {
      "program_name": "Nurse-Family Partnership (NFP)",
      "target_population": "First-time mothers",
      "evidence_rating": "Well-Supported",
      "reference": "Chunks: 28"
    }
  ],
  "additional_notes": null
}
```

**Example 2 - Limited Information:**

```json
{
  "prevention_programs": [
    {
      "program_name": "Brief Strategic Family Therapy (BSFT)",
      "target_population": "Families with youth experiencing behavioral issues",
      "evidence_rating": null,
      "reference": "Chunks: 5"
    },
    {
      "program_name": "Parent-Child Interaction Therapy (PCIT)",
      "target_population": "Parents and children ages 2-7",
      "evidence_rating": "Supported",
      "reference": "Chunks: 7"
    }
  ],
  "additional_notes": "Some programs lack complete rating information"
}
```

**Example 3 - No Programs Found:**

```json
{
  "prevention_programs": null,
  "additional_notes": null,
  "reference": "No prevention programs identified in chunks 1-20"
}
```
