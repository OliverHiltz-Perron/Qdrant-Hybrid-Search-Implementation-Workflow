# Title IV-E Prevention Plan: Funding Sources Extraction

## Task

You are an expert in Title IV-E prevention services funding. You will review provided text chunks from a State's Title IV-E prevention plan and extract all funding sources that support prevention services.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Funding information may be split across multiple chunks
- Some referenced funding may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Search for Direct Funding References

Look for explicit mentions of funding sources, money, or financial support in the chunks, including:

- Federal program names (Title IV-E, Title IV-B, TANF, Medicaid, etc.)
- State funding terms (appropriation, general fund, state match)
- Dollar amounts or budget references
- Grant programs
- Private or foundation funding

### Step 2: Search for Key Terms

Scan chunks for these terms and their variations:

- "fund", "funding", "finance", "revenue", "budget"
- "grant", "dollars", "payment", "reimbursement"
- "federal", "state", "local", "private"
- "match", "matching", "cost-sharing"

### Step 3: Extract Complete Information

When you find funding sources:

- Extract ALL funding sources mentioned (expect multiple)
- Use the exact name as written in the document
- Include dollar amounts if specified
- Note if it's current funding or planned/proposed

## Extraction Rules

### INCLUDE These Funding Sources:

- Federal grants and programs (even if administered through states)
- State appropriations and budget allocations
- Required matching funds
- Insurance reimbursements for prevention services
- Private grants or foundation funding
- County or local government contributions
- Any funding specifically for Title IV-E prevention services

### EXCLUDE These Items:

- Non-monetary support (training, technical assistance)
- Potential funding not yet secured
- Cost savings or cost avoidance
- Client fees unless reinvested in services

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
  "funding_sources": "string (semicolon-separated list or 'None')",
  "reference": "string (chunk numbers only)",
  "additional_notes": "string (optional - important context or missing information)"
}
```

## Examples

**Example 1 - Multiple Sources Found (Typical State):**

```json
{
  "funding_sources": "Title IV-E Prevention Services; Title IV-B; Medicaid; TANF; State General Fund appropriation ($1,000,000 annually); Maternal, Infant and Early Childhood Home Visiting (MIECHV); Community-Based Child Abuse Prevention (CBCAP); Substance Abuse and Mental Health Services Administration (SAMHSA) grants; Required state match; American Rescue Plan Act funds; Private foundation grants",
  "reference": "Chunks: 12, 15, 18, 23, 28, 35, 45",
  "additional_notes": null
}
```

**Example 2 - Limited Sources:**

```json
{
  "funding_sources": "Title IV-E; Title IV-B; State match funding",
  "reference": "Chunks: 3, 7",
  "additional_notes": "State appropriation amount not specified in provided chunks"
}
```

**Example 3 - No Sources Found:**

```json
{
  "funding_sources": "None",
  "reference": "N/A",
  "additional_notes": null
}
```
