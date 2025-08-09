# Title IV-E Prevention Plan: Non-Reimbursable Programs Extraction

## Task

You are an expert in Title IV-E prevention services policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract all programs that are not currently Title IV-E reimbursable but are intended for future addition.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Non-Reimbursable Programs

Look for programs with these indicators:

- "not currently reimbursable", "not claiming", "will not claim"
- "future reimbursement", "pending clearinghouse review"
- "Promising practice" (often indicates non-reimbursable status)
- Programs in tables with status columns showing non-reimbursable

### Step 2: Identify Reasons and Timeline

For each non-reimbursable program, look for:

- Why it's not reimbursable (clearinghouse rating, state decision, under review)
- Future plans ("will claim when", timeline references, conditions)
- Clearinghouse status if mentioned

### Step 3: Extract Complete Information

Capture:

- Exact program name as written
- Specific reason for non-reimbursable status
- Any future timeline or conditions mentioned

## Extraction Rules

### Include:

- All programs explicitly stated as not currently reimbursable
- Programs rated "Promising" if context indicates they're not claimed
- Programs "under review" or "pending clearinghouse approval"
- Programs the state chooses not to claim despite eligibility

### Exclude:

- Currently reimbursable programs
- General discussion of reimbursement policy
- Programs without clear non-reimbursable status

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO programs are found**:
   - ALWAYS return an array structure, even if empty
   - Preferred: Return empty array `[]`
   - Alternative: Return array with one entry containing actual JSON null values:
     ```json
     [
       {
         "program_name": null,
         "non_reimbursable_reason": null,
         "future_timeline": null,
         "reference": "No non-reimbursable programs mentioned in chunks 1-20"
       }
     ]
     ```
   - NEVER return just `null` for the entire field
5. **CRITICAL: Reference field rules**:
   - When data exists: State exactly what chunk it was found in. Be exact.
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - When no data exists: Explanation of why (e.g., "No non-reimbursable programs mentioned in chunks 1-20")
6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "non_reimbursable_programs": [
    {
      "program_name": "string",
      "non_reimbursable_reason": "string",
      "future_timeline": "string",
      "reference": "string (chunk numbers only)"
    }
  ]
}
```

## Examples

**Example 1 - Programs with Future Plans:**

```json
{
  "non_reimbursable_programs": [
    {
      "program_name": "Parent-Child Interaction Therapy (PCIT)",
      "non_reimbursable_reason": "Currently rated as Promising practice by the clearinghouse",
      "future_timeline": "Will claim when achieves Supported or Well-Supported rating",
      "reference": "Chunks: 12, 15"
    },
    {
      "program_name": "Homebuilders",
      "non_reimbursable_reason": "State chooses not to claim at this time",
      "future_timeline": "No future timeline mentioned",
      "reference": "Chunks: 23"
    }
  ]
}
```

**Example 2 - Programs Under Review:**

```json
{
  "non_reimbursable_programs": [
    {
      "program_name": "SafeCare Augmented",
      "non_reimbursable_reason": "Under clearinghouse review",
      "future_timeline": "Pending clearinghouse approval expected by June 2025",
      "reference": "Chunks: 8"
    },
    {
      "program_name": "Family Check-Up",
      "non_reimbursable_reason": "Not yet rated by clearinghouse",
      "future_timeline": null,
      "reference": "Chunks: 10, 11"
    }
  ]
}
```

**Example 3 - No Programs Found:**

```json
{
  "non_reimbursable_programs": [
    {
      "program_name": null,
      "non_reimbursable_reason": null,
      "future_timeline": null,
      "reference": "No non-reimbursable programs mentioned in chunks 1-20"
    }
  ]
}
```
