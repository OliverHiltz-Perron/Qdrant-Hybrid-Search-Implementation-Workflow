# Title IV-E Prevention Plan: Eligibility Determination Process Extraction

## Task

You are an expert in Title IV-E prevention services policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract how eligibility for prevention services is determined.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Eligibility Determination Process

Look for:

- How eligibility is determined (steps, procedures, workflows)
- When eligibility is determined (timing in case process)
- Who determines eligibility (specific roles or positions)
- Different processes for different populations

### Step 2: Find Tools and Systems

Look for specific mentions of:

- Eligibility screens or forms
- Assessment tools used for eligibility
- System names (FACES, HMIS, SHAKA, CPSS, etc.)
- Only include if explicitly used for eligibility determination

### Step 3: Extract Complete Information

Combine information across chunks to capture:

- The complete determination process
- All tools/systems mentioned
- Specific staff roles involved

## Extraction Rules

### Include:

- Step-by-step process descriptions
- Specific tools, screens, or systems BY NAME
- Who makes the determination (roles/positions)
- Different processes for different populations
- Timing of determination

### Exclude:

- Training requirements
- General candidacy definitions (unless part of the determination process)
- Service descriptions
- Monitoring after eligibility

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO tools are found**:
   - Return an array with ONE object containing:
   - `name`: null (actual JSON null, not string)
   - `purpose`: null (actual JSON null, not string)
   - `reference`: Explanation of why no tools were found (e.g., "No eligibility determination tools mentioned in chunks 1-20")
5. **CRITICAL: Reference field rules**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - When no data exists: Explanation of why (e.g., "No tools mentioned in chunks 1-20")
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "determination_process": {
    "description": "string (complete process for determining eligibility)",
    "reference": "string (chunk numbers only)"
  },
  "tools_used": [
    {
      "name": "string (exact name of tool/system)",
      "purpose": "string (how it's used in eligibility determination)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "determination_authority": {
    "description": "string (who determines eligibility)",
    "reference": "string (chunk numbers only)"
  },
  "additional_notes": "string (optional - important context or missing information)"
}
```

## Examples

**Example 1 - Process with Multiple Tools:**

```json
{
  "determination_process": {
    "description": "For Front Door and Front Porch families, CFSA staff responsible for determining eligibility select from a series of fields that include questions and answers in FACES to document child-specific eligibility for prevention services. The selection of eligibility-related fields in FACES validates eligibility and provides a child-specific candidacy timestamp. For Front Yard families, the DHS Liaison documents child-specific eligibility for prevention services in HMIS.",
    "reference": "Chunks: 12, 15"
  },
  "tools_used": [
    {
      "name": "FACES",
      "purpose": "Contains eligibility screens with questions and answers fields to document and validate child-specific eligibility",
      "reference": "Chunks: 12"
    },
    {
      "name": "HMIS",
      "purpose": "System where DHS Liaison documents child-specific eligibility for homeless families",
      "reference": "Chunks: 15"
    }
  ],
  "determination_authority": {
    "description": "Only CFSA staff will determine child-specific eligibility for prevention services. For Front Yard families, the DHS Liaison documents eligibility.",
    "reference": "Chunks: 12, 15"
  },
  "additional_notes": null
}
```

**Example 2 - Simple Process with Note:**

```json
{
  "determination_process": {
    "description": "DCFS created a FFPSA eligibility screen to ensure workers are correctly identifying children who are FFPSA eligible. This screen can be completed in an investigation or in a case and will be done on each child in the home ages 0 through 17.",
    "reference": "Chunks: 3"
  },
  "tools_used": [
    {
      "name": "FFPSA eligibility screen",
      "purpose": "Screen completed on each child ages 0-17 to identify FFPSA eligible children",
      "reference": "Chunks: 3"
    }
  ],
  "determination_authority": {
    "description": "Case workers complete the eligibility screen",
    "reference": "Chunks: 3"
  },
  "additional_notes": "Screen is mandatory in all investigations that end with opening a new case, reopening a closed case, or connecting to a new case"
}
```

**Example 3 - Limited Information with No Tools:**

```json
{
  "determination_process": {
    "description": "Eligibility determined through assessment process",
    "reference": "Chunks: 5"
  },
  "tools_used": null,
  "determination_authority": {
    "description": "Title IV-E agency makes determinations",
    "reference": "Chunks: 5"
  },
  "additional_notes": null,
  "reference": "No specific tools identified in chunks 1-20"
}
```
