# Title IV-E Prevention Plan: Equity and Disparity Reduction Extraction

## Task

You are an expert in child welfare equity policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract information about disparities and efforts to address them.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Disparity/Equity Content

Look for:

- Acknowledgment of disparities, inequities, or disproportionality
- Data showing overrepresentation of specific groups
- Commitments to address disparities
- Equity goals or objectives

### Step 2: Key Terms to Search

- "equity", "disparity", "disproportionality", "overrepresentation"
- Population group names (racial, ethnic, LGBTQ+, rural, etc.)
- "address", "reduce", "mitigate" when near disparity terms

### Step 3: Extract Information

Capture:

- Whether disparities are acknowledged and addressed
- Which populations experience disparities (with data if provided)
- What strategies are planned to address disparities

## Extraction Rules

### Include:

- Explicit acknowledgment of disparities
- Specific populations affected by disparities
- Disparity data or statistics if provided
- Concrete strategies to address disparities
- Equity offices, committees, or initiatives

### Exclude:

- General diversity statements without specific action
- Data collection methods
- Unrelated population descriptions

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
  "disparities_addressed": "string (Yes/No)",
  "disparity_description": "string (how disparities are acknowledged/described)",
  "affected_populations": "string (semicolon-separated list of populations)",
  "strategies": "string (semicolon-separated list of strategies)",
  "reference": "string (chunk numbers only)",
  "additional_notes": "string (optional - important context)"
}
```

## Examples

**Example 1 - Comprehensive Equity Approach:**

```json
{
  "disparities_addressed": "Yes",
  "disparity_description": "State acknowledges Black children make up 21.5% of foster system but only 5.6% of general population and are 2.8 times more likely to be reported for maltreatment than white children. Native American children enter foster care at rate of 8.6 per 1,000",
  "affected_populations": "Black/African American children; Native American/AI/AN children; Latino children; LGBTQ+ youth",
  "strategies": "Creation of Office of Equity; Cultural adaptations of evidence-based practices; Tribal consultation policy; Implicit bias training; Community-based culturally appropriate services",
  "reference": "Chunks: 8, 11, 15, 18",
  "additional_notes": null
}
```

**Example 2 - Limited Equity Focus:**

```json
{
  "disparities_addressed": "Yes",
  "disparity_description": "Plan mentions need to ensure equitable service delivery",
  "affected_populations": "None specified",
  "strategies": "Cultural competency training for providers",
  "reference": "Chunks: 3, 7",
  "additional_notes": "Plan acknowledges equity but lacks specific disparity data or targeted populations"
}
```

**Example 3 - No Equity Content:**

```json
{
  "disparities_addressed": "No",
  "disparity_description": "None",
  "affected_populations": "None",
  "strategies": "None",
  "reference": "N/A",
  "additional_notes": "No equity or disparity content found in provided chunks"
}
```
