# Title IV-E Prevention Plan: Trauma-Informed Programs Extraction

## Task

You are an expert in child welfare policy. You will review provided text chunks from a State's Title IV-E prevention plan and extract programs that are described as trauma-informed.

## Important Note on Chunk-Based Extraction

- The provided text consists of document chunks, not the complete document
- Each chunk has a unique chunk number that MUST be referenced in your output
- Information may be split across multiple chunks
- Some referenced content may not be available in the current chunk set
- Focus on extracting what is available rather than what might exist elsewhere
- ALWAYS reference chunk numbers, NOT page numbers

## Search Strategy

### Step 1: Find Trauma-Informed Programs

Look for programs described with terms like:

- "trauma-informed", "trauma-focused", "trauma-responsive"
- Programs that mention addressing trauma in their description
- Training programs that teach trauma-informed approaches
- Service delivery systems using trauma-informed practices

### Step 2: Extract Program Details

For each trauma-informed program found:

- Exact program name
- Description of how it's trauma-informed

### Step 3: Capture Complete Information

- Use exact language from the document
- Link the trauma-informed description to the specific program

## Extraction Rules

### Include:

- Programs explicitly described as trauma-informed
- Programs with trauma-focused components
- Descriptions of how programs address trauma
- Training programs focused on trauma-informed care
- System-wide programs implementing trauma-informed approaches
- Service delivery frameworks with trauma-informed practices

### Exclude:

- General trauma-informed philosophy without specific implementation
- Vague references to trauma without concrete programs or practices

## Output Rules

### Rules

1. Provide your response in JSON format using the exact schema below
2. Return only the JSON output with no preamble or explanation
3. Synthesize information across all relevant chunks
4. **CRITICAL: When NO trauma-informed programs are found**:
   - Return an array with ONE object containing:
   - `program_name`: null (actual JSON null, not string)
   - `trauma_description`: null (actual JSON null, not string)
   - `reference`: Explanation of why no programs were found (e.g., "No trauma-informed programs mentioned in chunks 1-20")
5. **CRITICAL: Reference field rules**:
   - If you use anything from any chunk that information must be included in the reference
   - Reference chunks must be exact to where the data was found
   - When no data exists: Explanation of why
6. Use verbatim language from the chunks when data exists

### JSON Schema

````json
{
  "trauma_informed_programs": [
    {
      "program_name": "string",
      "trauma_description": "string",
      "reference": "string (chunk numbers only)"
    }
  ]
}
## Examples

**Example 1 - Multiple Programs:**
```json
{
  "trauma_informed_programs": [
    {
      "program_name": "Trauma-Focused Cognitive Behavioral Therapy (TF-CBT)",
      "trauma_description": "Evidence-based treatment for children and adolescents impacted by trauma and their parents or caregivers",
      "reference": "Chunks: 12"
    },
    {
      "program_name": "Parent-Child Interaction Therapy",
      "trauma_description": "Delivered using trauma-informed principles to address parent-child relationship disrupted by trauma",
      "reference": "Chunks: 15, 16"
    }
  ]
}
````

**Example 2 - Single Program:**

```json
{
  "trauma_informed_programs": [
    {
      "program_name": "Functional Family Therapy",
      "trauma_description": "Incorporates trauma-responsive approaches in working with youth and families",
      "reference": "Chunks: 8"
    }
  ]
}
```

**Example 3 - None Found:**

```json
{
  "trauma_informed_programs": []
}
```
