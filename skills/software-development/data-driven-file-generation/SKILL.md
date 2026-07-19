---
name: data-driven-file-generation
description: "Generate many files from structured data using execute_code + write_file. Best for 5+ files with shared template."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
---

# Data-Driven File Generation

Generate many files from structured data using `execute_code` + `write_file` in a loop.

## When to Use

- 5+ output files, same structure, different content
- Documentation pages from a metadata registry
- Test stubs / fixtures
- Config files for similar environments (per-host, per-service)
- Component boilerplate from a data source

Do NOT use if: files are 1-2 (write individually faster), or each file has radically different structure (hand-craft).

## Core Pattern

```
execute_code (Python with hermes_tools):
  data = [dict1, dict2, ...]       # structured metadata
  def template(item) -> str:       # one function, all files
      return HEAD + body(item) + FOOT
  for item in data:
      write_file(path, template(item))
```

## Template Strategies

| Strategy | When | Example |
|----------|------|---------|
| **String replace** | HTML / plain‑text with placeholders | `s.replace('__KEY__', val)` |
| **Section composition** | Complex docs with optional sections | `parts = [h, purpose, api, example, anti, footer]` joined |
| **f-strings in function** | Python‑like output with minimal escaping | `f"<div>{name}</div>"` |
| **Jinja / string.Template** | Complex conditional templates | add import; fine inside execute_code |

## Key Technical Constraints

| Limit | Mitigation |
|-------|------------|
| 50 tool calls per execute_code | Batch: script generates max 40–45 files, then split |
| 5‑minute timeout | 45 files × ~2KB write = ~100ms each = safe |
| write_file overwrites | Run `ls` first to confirm target dir is clean |
| HTML/JS escaping | `content.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')` for code blocks |
| Cross‑profile guard | Docs go in project directory, not Hermes profile storage |

## Workflow: Mixed-Generation

For best quality when some files matter more:

1. **Hand‑craft 3–5 `write_file` calls** for the most important files (root index, key stores) — establishes the template
2. **Script the remaining bulk** in a single `execute_code` — fast, consistent
3. **Verify** — file count, content grep, cross‑reference links

## Template Functions for Section Composition

When docs have optional sections (some stores have API refs, others don't):

```python
# Each section is a function that returns HTML string (or empty)
def purpose(text):  return section_tag("Purpose", f"<p>{text}</p>")
def api(items):     return section_tag("API", format_items(items))
def anti(items):    return section_tag("Anti-patterns", format_cards(items))

def gen(store):
    parts = [header(store)]
    if store.get('purpose'): parts.append(purpose(store['purpose']))
    if store.get('api'):     parts.append(api(store['api']))
    if store.get('anti'):    parts.append(anti(store['anti']))
    parts.append(footer())
    return ''.join(parts)
```

## Verification Commands

```bash
# Count files
ls -1 *.html | wc -l

# Count total lines
wc -l *.html | tail -1

# Check a section exists in all files
grep -c 'Anti-patterns' *.html

# Find files missing a section
grep -L 'Anti-patterns' *.html
```

## Documentation-Site Enhancements

When generating a doc site, add these after the base generation:

### highlight.js syntax coloring

```html
<!-- In <head> -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<style>pre code.hljs{background:#1f1e1b;padding:0;border-radius:0}code.hljs{padding:0}</style>

<!-- Before </body> -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
```

Wrap each `<pre>CODE</pre>` as `<pre><code class="language-typescript">CODE</code></pre>`. highlight.js reads `textContent` (decodes HTML entities naturally), then inserts `<span class="hljs-*">` tags.

Apply via Python re.sub on generated files:
```python
content = re.sub(
  r'<pre style="([^"]*)">(.*?)</pre>',
  lambda m: f'<pre style="{m.group(1)}"><code class="language-typescript">{m.group(2)}</code></pre>'
    if '<code' not in m.group(2) else m.group(0),
  content, flags=re.DOTALL
)
```

### Copy-to-clipboard button on prompt cards

Attach a copy button using `data-p` attribute with URI-encoded text to avoid escaping issues:

```html
<button onclick="(function(b){var t=decodeURIComponent(b.getAttribute('data-p'));
navigator.clipboard.writeText(t);b.textContent='✓ Copied!';
setTimeout(function(){b.innerHTML='📋 Copy'},2000)})(this)"
 data-p="ENCODED_TEXT_HERE"
 style="background:rgba(255,255,255,0.2);border:none;...">
 📋 Copy
</button>
```

Encode in Python: `uri_escaped = text.replace('\\', '\\\\').replace('\n', '\\n')`.

### Claude.com warm editorial design system (default for doc sites)

Color tokens (implemented via tailwind.config + inline styles):

| Token | Hex | Use |
|-------|-----|-----|
| canvas | `#faf9f5` | Page background (warm cream) |
| ink | `#141413` | Headings, primary text (warm dark) |
| body | `#3d3d3a` | Running text |
| muted | `#6c6a64` | Secondary text |
| primary | `#cc785c` | Links, accents, badges (coral) |
| surface-card | `#efe9de` | Card backgrounds (light cream) |
| surface-dark | `#181715` | Header, footer, code blocks (navy) |
| on-dark | `#faf9f5` | Text on dark surfaces (cream echo) |
| on-dark-soft | `#a09d96` | Secondary text on dark |
| hairline | `#e6dfd8` | 1px borders on cream surfaces |

Typography stack:
- **Display**: `Cormorant Garamond` (serif, 400 weight, `-0.02em` tracking) for h1-h3
- **Body**: `Inter` for paragraph text
- **Code**: `JetBrains Mono` for code blocks
- Override with `Fantasque Sans Mono` everywhere when user prefers monospace-only

Layout: max content width `1200px`, section padding `96px`, card padding `32px`, border radius `12px`.

### Bulk restyling across files via sed + Python

Use sed for single-line replacements, Python heredoc for multi-line blocks:

```bash
# Single-line font-family replacement
sed -i "s|font-family: 'Cormorant Garamond'|font-family: 'Fantasque Sans Mono'|" *.html

# Multi-line tailwind.config replacement (Python)
python3 -c "
import os, re
pat = r'fontFamily:\s*\{[^}]*\}'
repl = '''fontFamily: { display: ['Fantasque Sans Mono', 'monospace'] }'''
for f in [f for f in os.listdir('.') if f.endswith('.html')]:
    c = open(f).read()
    if re.search(pat, c): open(f,'w').write(re.sub(pat, repl, c))
"
```

### Onboarding prompt cards per page

Add a coral callout card between the page header and content for developer onboarding:

```html
<div style="margin-top:24px;background:#cc785c;border-radius:12px;padding:24px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;...">
    <p>Onboarding Prompt</p>
    <button onclick="...">📋 Copy</button>
  </div>
  <p>Prompt text telling a new dev how to use this component.</p>
</div>
```

## Pitfalls to Avoid

- ❌ String escaping inside Python triple‑quoted strings inside JSX‑like templates → use `.replace()` at the end
- ❌ Unpacking tuples of wrong length → use dicts with `.get()` for optional fields
- ❌ Forgetting `write_file` path strings include the filename (not a directory)
- ❌ Over‑engineering a template system when 3 hand‑crafted files suffice
- ❌ sed for multi-line replacements → sed is line-based; use Python `re.subn` for JS/ HTML block objects
- ❌ `fontFamily:` config inside Tailwind config spans multiple lines; `[^}]*` won't cross newlines
- ❌ Case-insensitive font-name detection in inline styles → "Inter" matches "InteractionStore"; use full family-name patterns
- ❌ HTML entity escaping for highlight.js → not needed; hljs reads `textContent` (browser-decoded entities)

## Related Skills

- `writing-plans` — describes the plan that the generation follows
- `subagent-driven-development` — alternative: delegate each file to a subagent (slower but better per-file quality)
- `hermes-agent-skill-authoring` — similar pattern for generating SKILL.md files from data
