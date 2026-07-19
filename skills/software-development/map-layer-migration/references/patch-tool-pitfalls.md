# Patch Tool Pitfalls

## Literal `\n` corruption

When passing multi-line strings to `patch(mode='replace')`, the tool may write literal backslash-n (`\n`) escape sequences into the file instead of real newlines.

**Symptoms:** The file shows `\\n` or `\n` in the middle of source code — LSP reports "Invalid character" errors.

**Reproduction:** Using `\n` in the new_string parameter instead of actual newlines. The patch tool doesn't interpret escape sequences.

**Fix:** 
1. Read the corrupted section with `read_file`
2. Use `patch` with the actual corrupted text as `old_string` and corrected text as `new_string` (with real newlines)
3. Or use `write_file` to overwrite the affected section entirely

## Fuzzy match over-deletion

The patch tool's fuzzy matching (9 strategies) can match the wrong adjacent lines if the `old_string` doesn't precisely exist in the target.

**Symptoms:** Lines adjacent to your target get deleted unexpectedly. `git diff` shows more removals than intended.

**Reproduction:** When replacing a line in a densely-packed file (e.g. hook-keys.ts with consecutive key definitions), the fuzzy matcher may interpret nearby similar-looking entries as a close match and merge them.

**Defense:**
- After every patch, verify with `git diff HEAD -- <file>` or `read_file` around the edit area
- For densely-packed files, prefer `write_file` (overwrite the whole file) when the patch is small relative to file size
- Include more surrounding context lines in `old_string` to reduce ambiguity
