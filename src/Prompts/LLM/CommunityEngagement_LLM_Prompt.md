# Title IV-E Prevention Plan: Community Engagement and Stakeholder Involvement Extraction

## Task

You are an expert in community engagement and stakeholder participation. You will review provided text chunks from a State's Title IV-E prevention plan and extract information about community engagement and stakeholder involvement in planning and implementation.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Stakeholder Information

Look for mentions of:

- Specific organizations or groups involved
- Youth, parents, families with lived experience
- Providers, courts, schools, advocates
- Advisory boards, committees, workgroups
- Community-based organizations

### Step 2: Find Engagement Methods

Look for descriptions of:

- How stakeholders were engaged (meetings, surveys, forums)
- When engagement occurred (planning vs. implementation)
- Frequency of engagement (one-time vs. ongoing)
- Decision-making structures

### Step 3: Extract Complete Information

Combine information across chunks to capture:

- All stakeholder groups mentioned
- All engagement methods used
- The purpose and outcomes of engagement

## Extraction Rules

### Include:

- Named organizations and specific stakeholder groups
- Concrete engagement activities and methods
- Formal committees or governance structures
- Both planning and implementation phase engagement
- How input was incorporated into the plan

### Exclude:

- Generic statements about importance of engagement
- Theoretical frameworks without specific actions
- Future intentions without concrete plans

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO stakeholders/methods/structures are found**:
   - For each empty array, return an array with ONE object containing:
   - All fields set to null (actual JSON null, not string)
   - `reference`: Explanation of why no data was found (e.g., "No stakeholders mentioned in chunks 1-20")
5. **CRITICAL: Reference field rules**:

   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found

   - When no data exists: Explanation of why (e.g., "No engagement methods found in chunks 1-20")

6. Use verbatim language from the chunks when data exists

### JSON Schema

```json
{
  "stakeholders_involved": [
    {
      "name": "string (organization or group name)",
      "type": "string (youth/families/providers/courts/etc.)",
      "role": "string (their involvement in process)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "engagement_methods": [
    {
      "method": "string (meeting/survey/committee/etc.)",
      "description": "string (details of engagement, max 75 words)",
      "frequency": "string (one-time/monthly/ongoing/etc.)",
      "phase": "string (planning/implementation/both)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "governance_structures": [
    {
      "name": "string (committee/board name)",
      "purpose": "string (role in prevention program)",
      "membership": "string (who participates)",
      "reference": "string (chunk numbers only)"
    }
  ],
  "additional_notes": "string (optional - important context or missing information)"
}
```

## Examples

**Example 1 - Comprehensive Engagement:**

```json
{
  "stakeholders_involved": [
    {
      "name": "Youth Advisory Board",
      "type": "youth",
      "role": "Provide input on service design and implementation",
      "reference": "Chunks: 12, 15"
    },
    {
      "name": "Parents as Partners Coalition",
      "type": "families",
      "role": "Review prevention strategies and provide feedback on family engagement approaches",
      "reference": "Chunks: 15"
    },
    {
      "name": "County Behavioral Health Department",
      "type": "providers",
      "role": "Partner in service delivery and workforce development",
      "reference": "Chunks: 18, 22"
    }
  ],
  "engagement_methods": [
    {
      "method": "Town halls",
      "description": "Quarterly community town halls held in each region to gather input on prevention needs and service gaps",
      "frequency": "quarterly",
      "phase": "both",
      "reference": "Chunks: 25"
    },
    {
      "method": "Online survey",
      "description": "Statewide survey of families and youth to identify prevention service priorities, received 1,200 responses",
      "frequency": "one-time",
      "phase": "planning",
      "reference": "Chunks: 28"
    }
  ],
  "governance_structures": [
    {
      "name": "Prevention Services Oversight Committee",
      "purpose": "Oversee implementation and continuous quality improvement",
      "membership": "State agency leaders, provider representatives, parent advocates, youth representatives",
      "reference": "Chunks: 30, 32"
    }
  ],
  "additional_notes": null
}
```

**Example 2 - Limited Information:**

```json
{
  "stakeholders_involved": [
    {
      "name": "Community stakeholders",
      "type": "various",
      "role": "Participated in planning process",
      "reference": "Chunks: 5"
    }
  ],
  "engagement_methods": [
    {
      "method": "Stakeholder meetings",
      "description": "Multiple meetings held to gather input",
      "frequency": null,
      "phase": "planning",
      "reference": "Chunks: 5"
    }
  ],
  "governance_structures": null,
  "additional_notes": "Limited detail on community engagement in provided chunks"
}
```

**Example 3 - No Engagement Information Found:**

```json
{
  "stakeholders_involved": null,
  "engagement_methods": null,
  "governance_structures": null,
  "additional_notes": "No community engagement or stakeholder involvement information found in provided chunks"
}
```
