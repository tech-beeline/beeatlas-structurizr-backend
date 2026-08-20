# Fix: Temporary File Path Contains Spaces

## Root Cause Analysis

The bug is a **shell word-splitting** issue caused by spaces in a temporary filename combined with unquoted shell command construction.

### Execution Flow (from log)

```
1. CMDB code extracted: LOYALTY_PROCESSING       ← underscore, no spaces
2. Writing workspace JSON to /tmp/workspace_loyalty processing.json  ← space appears!
3. Executing CLI command for workspace 36932234339
4. workspace path /tmp/workspace_loyalty does not exist  ← shell split on space
```

### The Bug Chain

**Step 1 — Wrong parameter passed as filename component**  
In [`src/routers/fitness_functions.py:173`](src/routers/fitness_functions.py:173):
```python
if not publish_json_workspace(cmdb= product_beeatlas.alias, ...)
```
`product_beeatlas.alias` is `"loyalty processing"` (with a space), whereas the actual CMDB code from the document is `"LOYALTY_PROCESSING"` (underscore, no spaces).

**Step 2 — Filename contains space**  
In [`src/routers/fitness_functions.py:51`](src/routers/fitness_functions.py:51):
```python
filename = tempfile.gettempdir() + f'/workspace_{cmdb}.json'
# Result: /tmp/workspace_loyalty processing.json  ← space in path
```

**Step 3 — Shell command has unquoted path**  
In [`src/routers/fitness_functions.py:63`](src/routers/fitness_functions.py:63):
```python
command += "-workspace "+filename
# Result: -workspace /tmp/workspace_loyalty processing.json  ← no quotes!
```

**Step 4 — Shell splits arguments on space**  
In [`src/routers/fitness_functions.py:69`](src/routers/fitness_functions.py:69):
```python
if os.system(command) == 0:
```
`os.system()` passes the string to `/bin/sh -c`, which splits on spaces. The CLI receives:
- `-workspace` → `/tmp/workspace_loyalty`
- `processing.json` → separate argument (ignored/confused)

The CLI then reports: `workspace path /tmp/workspace_loyalty does not exist`

### All Affected Locations

| File | Function | Issue | Severity |
|------|----------|-------|----------|
| [`src/routers/fitness_functions.py:45-83`](src/routers/fitness_functions.py:45) | `publish_json_workspace()` | Filename uses alias with spaces; `os.system()` with unquoted path | **HIGH — actively failing** |
| [`src/routers/workspace.py:29-66`](src/routers/workspace.py:29) | `publish_default_workspace()` | `os.system()` with unquoted path (filename is hardcoded `workspace.dsl`, safe for now) | **LOW — fragile, same pattern** |
| [`src/routers/utils.py:52-92`](src/routers/utils.py:52) | `convert_dsl2json()` | Uses `subprocess.Popen()` with argument list — **CORRECT pattern** | ✅ Reference implementation |

## Proposed Solution

### Approach: Refactor to `subprocess.run()` + sanitize filenames

**Why:** [`src/routers/utils.py:72`](src/routers/utils.py:72) already demonstrates the correct pattern using `subprocess.Popen()` with an argument list (no shell). We should consistently apply this pattern.

### Changes Required

#### 1. [`src/routers/fitness_functions.py`](src/routers/fitness_functions.py) — `publish_json_workspace()`

**a) Sanitize filename (line 51):**
```python
# BEFORE:
filename = tempfile.gettempdir() + f'/workspace_{cmdb}.json'

# AFTER:
safe_name = cmdb.replace(' ', '_').replace('\t', '_')
filename = tempfile.gettempdir() + f'/workspace_{safe_name}.json'
```

**b) Replace `os.system()` with `subprocess.run()` (lines 58-69):**
```python
# BEFORE:
command  = "/usr/local/structurizr-cli/structurizr.sh "
command += "push -url "+url_onpremises_base+" "
command += "-id "+ str(workspace_id) + " "
command += "-key "+structurizrApiKey+" "
command += "-secret "+structurizrApiSecret+" "
command += "-workspace "+filename
command += " -merge false"

result = False
if os.system(command) == 0:
    result = True

# AFTER:
import subprocess

command = [
    "/usr/local/structurizr-cli/structurizr.sh",
    "push",
    "-url", url_onpremises_base,
    "-id", str(workspace_id),
    "-key", structurizrApiKey,
    "-secret", structurizrApiSecret,
    "-workspace", filename,
    "-merge", "false"
]

result = subprocess.run(command, capture_output=True, text=True)
success = result.returncode == 0
```

#### 2. [`src/routers/workspace.py`](src/routers/workspace.py) — `publish_default_workspace()` (defensive)

**Replace `os.system()` with `subprocess.run()` (lines 47-61):**
```python
# BEFORE:
command  = "/usr/local/structurizr-cli/structurizr.sh "
command += "push -url " +url_onpremises_base+" "
command += "-id "+ str(workspace_id) + " "
command += "-key "+product.structurizrApiKey+" "
command += "-secret "+product.structurizrApiSecret+" "
command += "-workspace "+filename

if os.system(command) == 0:
    return True

# AFTER:
import subprocess

command = [
    "/usr/local/structurizr-cli/structurizr.sh",
    "push",
    "-url", url_onpremises_base,
    "-id", str(workspace_id),
    "-key", product.structurizrApiKey,
    "-secret", product.structurizrApiSecret,
    "-workspace", filename
]

result = subprocess.run(command, capture_output=True, text=True)
if result.returncode == 0:
    return True
```

### Diagram: Data Flow Before/After Fix

```mermaid
flowchart LR
    subgraph "Before Bug"
        A[CMDB: LOYALTY_PROCESSING] --> B[product_beeatlas.alias<br/>loyalty processing]
        B --> C[Filename: /tmp/workspace_loyalty processing.json]
        C --> D[os.system unquoted command]
        D --> E[Shell splits on space]
        E --> F[/tmp/workspace_loyalty<br/>processing.json]
        F --> G[CLI ERROR: file not found]
    end

    subgraph "After Fix"
        H[CMDB: LOYALTY_PROCESSING] --> I[sanitize alias<br/>loyalty_processing]
        I --> J[Filename: /tmp/workspace_loyalty_processing.json]
        J --> K[subprocess.run argument list]
        K --> L[CLI receives correct path]
        L --> M[CLI SUCCESS: file found]
    end
```

### Testing Notes

1. Verify with a product whose alias contains spaces (e.g., "loyalty processing")
2. Verify with a product whose alias has no spaces (regression check)
3. Verify the CLI output/return code is still properly captured in logs
4. Check that `os.remove(filename)` on line 74 still works with the sanitized name

### Files to Modify

| File | Changes |
|------|---------|
| [`src/routers/fitness_functions.py`](src/routers/fitness_functions.py) | Add `import subprocess`; sanitize filename in `publish_json_workspace()`; replace `os.system()` with `subprocess.run()` |
| [`src/routers/workspace.py`](src/routers/workspace.py) | Add `import subprocess` (if not already); replace `os.system()` with `subprocess.run()` in `publish_default_workspace()` |
