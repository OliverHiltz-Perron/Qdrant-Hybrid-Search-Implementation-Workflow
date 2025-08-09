# Title IV-E Prevention Plan: Monitoring and Accountability Extraction

## Task

You are an expert in child welfare program monitoring. You will review provided text chunks from a State's Title IV-E prevention plan and extract information about monitoring systems and accountability structures.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Monitoring Content

Look for sections discussing:

- Monitoring, fidelity, quality improvement (CQI)
- Accountability, oversight, governance
- Data collection, reporting, review processes

### Step 2: Extract Monitoring Details

When found, capture:

- What is monitored and how
- Who conducts monitoring
- Frequency of monitoring activities

### Step 3: Note All Elements

Include all types:

- Implementation monitoring
- Fidelity monitoring
- Quality improvement processes
- Oversight structures

## Extraction Rules

### Include:

- All monitoring methods and processes
- Fidelity checking procedures
- Quality improvement activities
- Accountability and oversight structures
- Data collection and reporting requirements

### Exclude:

- General quality statements without specifics
- Budget or fiscal monitoring
- Unrelated administrative procedures

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
  "monitoring_and_accountability": "string (semicolon-separated list)",
  "reference": "string (chunk numbers only)",
  "additional_notes": "string (optional)"
}
```

## Examples

**Example 1 - Multiple Elements:**

```json
{
  "monitoring_and_accountability": "Quarterly site visits by state staff; Annual fidelity assessments using program-specific tools; Monthly CQI team meetings to review performance data; Prevention Services Oversight Committee meets quarterly; Provider self-assessments every 6 months",
  "reference": "Chunks: 9, 15, 18, 24",
  "additional_notes": null
}
```

**Example 2 - Basic Information:**

```json
{
  "monitoring_and_accountability": "Regular monitoring of prevention programs; State uses continuous quality improvement process",
  "reference": "Chunks: 6, 11",
  "additional_notes": null
}
```

**Example 3 - Not Found:**

```json
{
  "monitoring_and_accountability": "None",
  "reference": null,
  "additional_notes": "No monitoring or accountability information found in provided chunks"
}
```
