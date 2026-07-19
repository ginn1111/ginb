# Store Documentation HTML Generation (Session Example)

## Task

Generate 42 static HTML pages documenting 41 MobX stores (custom + keplr-wallet SDK) in a wallet extension, plus a root store-map index. Each page: Purpose → API Reference → Usage Example → Anti-patterns → Related Stores.

## Approach

### Phase 1: Hand-craft (5 core files)
Used `write_file` directly for the root index and 4 custom stores (UIConfigStore, HugeQueriesStore, VaultBalancesStore, ClaimRewardsStateStore) whose source code was already read. Established the HTML template and Tailwind CDN styling.

**Template structure per page:**
```
HEAD (Tailwind CDN, dark class, header with back-link + store badge + tag)
  Purpose section
  API Reference section (optional)
  Usage Example section (optional, with syntax-highlighted code block)
  Anti-patterns section (optional, danger cards)
  Related Stores section (optional, link list)
FOOT (source attribution)
```

### Phase 2: Script the bulk (37 files)
Used `execute_code` with Python + `from hermes_tools import write_file`:

1. **Template fragments**: `HEAD`, `FOOT` — global strings with `__KEY__` placeholders
2. **Section functions**: `purp(text)`, `api(items)`, `ex(title, code)`, `anti(items)`, `rel(links)` — compose optional sections
3. **Build function**: `build(store_dict) → html` — joins only non‑empty sections
4. **Data**: each store as dict with 9 keys (file, name, desc, pkg, src, purp, api, ex_code, anti, rel)
5. **Loop**: `for s in stores: write_file(f"{DIR}/{s['file']}.html", build(s))`

Executed in 2 scripts (batch 1 error → batch 2 fixed tuple-vs-dict bug) → second `execute_code` succeeded with 18 files in 1.6s.

### Data Model Per Store
```python
{"file":"store-file-name",
 "name":"DisplayName",
 "desc":"Short description",
 "pkg":"keplr-wallet/stores-core",   # badge label
 "src":"@keplr-wallet/stores-core",  # footer source
 "purp":"Paragraph of purpose text",
 "api":[("get", "propertyName — description")],  # or []
 "ex_title":"hooks/Example.ts",       # or ""
 "ex_code":"const x = ...",           # or ""
 "anti":[("Title", "Description")],   # or []
 "rel":[("file.html", "Name", "desc")]}  # or []
```

### Key Decisions
- **Dicts over tuples** — avoids unpacking bugs when some fields are optional (lesson learned from 1st script failure)
- **Tag badges**: custom stores → emerald (`bg-emerald-800`), keplr SDK → blue (`bg-blue-800`)
- **Section optionality**: each section function returns empty when no data, so CurrencyRegistrars (minimal public API) get Purpose-only without looking incomplete
- **File location**: `apps/extension/docs/stores/` — project-local, not Hermes profile storage

### Verification
```bash
ls -1 apps/extension/docs/stores/*.html | wc -l   # → 42
wc -l apps/extension/docs/stores/*.html | tail -1  # → 2485 total
grep -c 'Anti-patterns' *.html                      # → 22 files with anti-patterns
```

## Phase 3: Bulk Restyling Across All Files

After all 42 files existed, the user provided a complete design spec (Claude.com warm editorial aesthetic). Rather than re-running generation, applied changes in bulk across all files.

### Bulk CSS/HTML replace with sed

Used terminal `sed -i` across all 42 `*.html` files simultaneously:

```bash
# Replace Google Fonts import
sed -i 's|<link href="https://fonts.googleapis.com/[^\"]*" rel=\"stylesheet\">|<link href="https://fonts.googleapis.com/css2?family=Fantasque+Sans+Mono:wght@400;500;700&display=swap" rel=\"stylesheet\">|' *.html

# Replace CSS font-family declarations
sed -i "s|font-family: 'Cormorant Garamond', Garamond, 'Times New Roman', serif;|font-family: 'Fantasque Sans Mono', monospace;|" *.html
sed -i "s|font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;|font-family: 'Fantasque Sans Mono', monospace;|" *.html
sed -i "s|font-family: 'JetBrains Mono', Menlo, Monaco, 'Courier New', monospace;|font-family: 'Fantasque Sans Mono', monospace;|" *.html

# Inline style references
sed -i "s|font-family:JetBrains Mono,monospace;|font-family:Fantasque Sans Mono,monospace;|g" *.html
```

### Multi-line replacements via Python

For the multi-line `tailwind.config.fontFamily` block (sed can't do multi-line), used Python with regex:

```bash
python3 -c "
import os, re
pat = r'fontFamily:\s*\{[^}]*\}'
repl = '''fontFamily: {
        display: ['Fantasque Sans Mono', 'monospace'],
        body: ['Fantasque Sans Mono', 'monospace'],
        code: ['Fantasque Sans Mono', 'monospace']
      }'''
for f in [f for f in os.listdir('.') if f.endswith('.html')]:
    c = open(f).read()
    if re.search(pat, c): open(f,'w').write(re.sub(pat, repl, c))
"
```

### Key lessons for bulk restyling
- **sed first for single-line, Python heredoc for multi-line** — sed cannot match across newlines; use `re.subn` for JS object blocks
- **Verify with grep** — `grep -c "OldFont" *.html | grep -v ":0"` catches missed replacements
- **Watch for false positives** — "Inter" appears in "InteractionStore" class names; precision-check with full font name patterns
- **Case-insensitive matches in inline styles** — font-family values may appear as `JetBrains Mono,monospace` (no quotes), `'JetBrains Mono', monospace` (with quotes), or other variants. Run passes for each variant.

## Phase 4: Onboarding Prompts (42 files)

Added a coral `#cc785c` callout card between the header and main content of every page, containing a developer onboarding prompt. Each prompt is store-specific and covers:
- Core responsibility (1 sentence)
- How to access/import
- Key gotchas
- File path

### Copy button

Each prompt card includes a "📋 Copy" button that copies the prompt text to clipboard. Uses a `data-p` attribute with URI-encoded text to avoid HTML/JS escaping issues:

```html
<button onclick="(function(b){var t=decodeURIComponent(b.getAttribute('data-p'));
navigator.clipboard.writeText(t);b.textContent='✓ Copied!';
setTimeout(function(){b.innerHTML='📋 Copy'},2000)})(this)"
 data-p="ENCODED_TEXT" style="...">📋 Copy</button>
```

Applied via Python regex injection after the header's tags div:
```python
pattern = r'(<div class="mt-4 flex gap-2">.*?</div>\s*</div>\s*</header>)'
match = re.search(pattern, content, re.DOTALL)
content = content.replace(match.group(1), match.group(1) + '\n' + prompt_block)
```

## Phase 5: Syntax Highlighting (42 files)

Added highlight.js (atom-one-dark theme) for all code blocks:
1. CDN CSS in `<head>`
2. Wrapped `<pre>CODE</pre>` → `<pre><code class="language-typescript">CODE</code></pre>`
3. CDN JS + `hljs.highlightAll()` before `</body>`

Applied via Python re.sub:
```python
content = re.sub(
  r'<pre style="padding:24px;overflow-x:auto;margin:0;background:#1f1e1b;color:#faf9f5;">(.*?)</pre>',
  lambda m: f'<pre ...><code class="language-typescript">{m.group(1)}</code></pre>'
    if '<code' not in m.group(1) else m.group(0),
  content, flags=re.DOTALL
)
```

## Files Generated

`apps/extension/docs/stores/` — root `index.html` + 41 store pages:

| Category | Count | Examples |
|----------|-------|---------|
| Custom stores | 6 | UI config, chain, key ring, huge queries, vault balances, claim rewards |
| Interaction & Permission | 7 | Interaction, Permission, Chain suggest, Tokens, ICNS |
| Signing interactions | 6 | Cosmos/EVM/StarkNet/Bitcoin tx and message signers |
| Query stores | 7 | Queries, Skip, AIOZ bridge/stake, StarkNet/Bitcoin queries |
| Account stores | 4 | Cosmos, EVM, StarkNet, Bitcoin account |
| Price & Analytics | 3 | CoinGecko price, 24h changes, Analytics |
| IBC + Asset discovery | 8 | IBC channel/registry, 6 currency registrars |
