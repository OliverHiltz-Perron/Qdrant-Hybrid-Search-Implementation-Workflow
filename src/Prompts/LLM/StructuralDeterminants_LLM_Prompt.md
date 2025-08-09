# Title IV-E Prevention Plan: Structural Determinants Extraction

## Task

You are an expert in social determinants of health and child welfare policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract how the state addresses structural determinants of child welfare involvement.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Structural Determinant Content

Look for sections discussing:

- "Social Determinants of Health" (SDOH)
- "Structural determinants", "root causes", "concrete supports"
- Poverty, housing, employment, healthcare access
- Basic needs, economic assistance, wraparound services

### Step 2: Identify Specific Supports

When found, extract mentions of:

- Housing assistance or homelessness prevention
- Transportation support
- Economic or financial assistance
- Healthcare access or insurance
- Childcare assistance
- Food security or nutrition programs
- Employment services or job training
- Legal aid or immigration support

### Step 3: Note How Supports Are Provided

Capture whether supports are:

- Provided directly by child welfare
- Available through referrals or partnerships
- Part of wraparound or coordinated services

## Extraction Rules

### Include:

- Explicit mentions of addressing structural factors or root causes
- Specific concrete supports offered (housing, economic, healthcare, etc.)
- Partnerships that provide structural supports
- Wraparound services addressing basic needs

### Exclude:

- Traditional child welfare services (therapy, parenting classes)
- General prevention philosophy without specific supports
- Administrative or funding details

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: Use `null` for missing data, NOT placeholder text**:
   - If no information found, use `null` (not "Not specified", "N/A", etc.)
   - Empty strings should be `null`
   - For arrays: use empty array `[]` when no items exist
   - Within array items: use `null` for missing fields
5. **CRITICAL: Reference MUST include chunk numbers ONLY**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - List all chunks containing relevant information
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "structural_determinants_approach": "string",
  "specific_supports": "string (semicolon-separated list)",
  "reference": "string (chunk numbers only)",
  "additional_notes": "string (optional)"
}
```

## Examples

**Example 1 - Multiple Supports:**

```json
{
  "structural_determinants_approach": "Prevention at the primary level addresses general population needs through a social determinants of health approach including access to childcare, food and housing, reducing poverty and improving economic stability",
  "specific_supports": "Housing assistance; Transportation support; Wraparound services to address economic self-sufficiency; Improving access to healthcare; Childcare assistance",
  "reference": "Chunks: 12, 15, 18",
  "additional_notes": null
}
```

**Example 2 - Limited Information:**

```json
{
  "structural_determinants_approach": "Concrete community prevention supports promote self-sufficiency",
  "specific_supports": "Concrete community prevention supports",
  "reference": "Chunks: 5",
  "additional_notes": "Limited detail on specific types of concrete support"
}
```

**Example 3 - Not Found:**

```json
{
  "structural_determinants_approach": "None",
  "specific_supports": "None",
  "reference": null,
  "additional_notes": "No structural determinants or concrete supports found in provided chunks"
}
```
