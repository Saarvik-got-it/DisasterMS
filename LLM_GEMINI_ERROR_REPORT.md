# Gemini Severity Parse Error Report

## Error Summary

- **Message**: `Gemini response missing content parts`
- **Observed Behavior**: Severity LLM falls back to default and then gets aligned to prediction mapping.

## Role of the Severity Assessor

- Produces a human-readable severity label (LOW/MEDIUM/HIGH/CRITICAL) based on:
  - Forecast feature summary
  - Classifier prediction probabilities
  - Relevant news context
- It is a **synthesis step** and should not contradict the classifier output.

## Likely Causes

1. **Gemini response missing content**
   - The API can return `candidates` with no `content.parts` when a response is blocked or empty.
2. **Response MIME mismatch**
   - Some Gemini configurations ignore or fail to honor `responseMimeType=application/json`, yielding empty parts.
3. **Safety or policy filtering**
   - Safety filters can produce responses without content parts while still returning a 200 status.
4. **Transient provider issues**
   - Short-lived API or quota issues can return partially formed responses.

## Fix Implemented (No Disruption to Working Paths)

- Added robust extraction for Gemini outputs and safe fallback logic:
  - When `content.parts` is missing, reissue **one** request **without** `responseMimeType`.
  - Extract the text from the alternate response if present.
- Added a short-circuit for **Normal** predictions:
  - Skip the LLM entirely and return `LOW` severity with a clear reason.

## Expected Result

- Normal conditions no longer invoke the LLM.
- Gemini responses that omit content parts are retried without JSON MIME.
- Severity output remains consistent with the classifier and routing rules.

## Files Updated

- [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py)

## Remaining Risks

- If Gemini repeatedly blocks output, the system will still fall back to default severity.
- If you need zero fallback usage, consider:
  - stricter prompt controls
  - higher `maxOutputTokens`
  - explicit Gemini safety settings
