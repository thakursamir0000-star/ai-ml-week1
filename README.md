# ai-ml-week1

Week 1 assignments for my AI/ML Engineer internship: the **Monday** and
**Tuesday** tasks from the internship roadmap.

| Day | Roadmap task | What this repo contains |
|-----|--------------|-------------------------|
| Monday | Configure Git, prepare the Python environment, make a working test call to the Claude API | `src/api_client.py`: configuration loading, one Messages API call, text extraction and error handling. `python -m src.main ping` is the live test call. |
| Tuesday | A script that calls Claude and parses its JSON response | `src/classifier.py` + `src/response_parser.py`: classify a short text into a category, parse Claude's reply with `json`, and validate it against a schema. `python -m src.main classify "..."` runs it. |

Wednesday (embeddings), Thursday (semantic search) and Friday (review) are
**out of scope** for this repository so far.

## Status

| Item | Status |
|------|--------|
| Git repository and `.gitignore` | Done |
| Python environment verified (`check-env`) | Done |
| Claude API client (`api_client.py`) | Done, verified against mocked HTTP responses |
| JSON parsing and schema validation (`response_parser.py`) | Done, verified by unit tests |
| Classification workflow and CLI (`classifier.py`, `main.py`) | Done, verified against mocked HTTP responses |
| Automated tests (offline) | Passing (see [Run the tests](#run-the-tests)) |
| **Live Claude API call** | **Pending.** No API key or billing access yet. The code has not been run against the real API. |

## Project structure

```
ai-ml-week1/
├── src/
│   ├── __init__.py
│   ├── api_client.py       # Monday: settings, SDK client, send_message(), extract_text(), errors
│   ├── response_parser.py  # Tuesday: JSON parsing + schema validation (pure, no network)
│   ├── classifier.py       # Tuesday: classify_text() workflow (prompt -> API -> parse -> validate)
│   └── main.py             # CLI: check-env, ping, classify
├── tests/
│   ├── fakes.py            # fake Anthropic API at the HTTP layer (httpx2.MockTransport)
│   ├── conftest.py         # isolates env vars/.env and blocks real network access
│   ├── test_api_client.py
│   ├── test_response_parser.py
│   ├── test_classifier.py
│   └── test_main.py
├── .env.example            # placeholder only, copy to .env
├── .gitattributes          # LF line endings for Windows + WSL
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

This follows the recommended layout with one addition: `classifier.py` holds
the Tuesday workflow, so `response_parser.py` stays free of network code and
can be tested without any mocks.

## Prerequisites

- Windows 11 with **WSL2 Ubuntu**; VS Code connected to WSL.
- The existing Linux virtual environment **`/home/asuss/venvs/ai-ml-linux`**
  (Python 3.12). Windows Python is not used because application-control
  policy blocks PyTorch's native DLL there. This project doesn't need
  PyTorch, but the internship work shares the one environment.
- Git (already configured in WSL with `user.name` / `user.email`).

## Setup

```bash
source /home/asuss/venvs/ai-ml-linux/bin/activate
cd /mnt/d/ai-ml-week1
pip install -r requirements.txt      # everything is already installed in this venv; this is a no-op
python -m src.main check-env         # verify interpreter, packages and credential status (offline)
```

Expected `check-env` output without credentials:

```
Python executable : /home/asuss/venvs/ai-ml-linux/bin/python
Python version    : 3.12.15
anthropic         : 1.15.0
httpx2            : 2.13.1
python-dotenv     : 1.2.4
pytest            : 9.1.1
ANTHROPIC_API_KEY : not configured - live API calls are unavailable
```

## Configure credentials

Do this only once your supervisor provides an API key with billing enabled.

```bash
cp .env.example .env
nano .env                 # replace your-api-key-here with the real key
chmod 600 .env            # optional: keep the file private
python -m src.main check-env   # should now say: configured (value hidden)
```

You can export the variable in your shell instead (`export ANTHROPIC_API_KEY=...`).
A non-empty environment variable takes precedence over `.env`.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ANTHROPIC_API_KEY` | yes | none | API key. Never printed, logged or committed. |
| `CLAUDE_MODEL` | no | `claude-opus-5-5` | Model ID to call. |
| `CLAUDE_USE_FALLBACKS` | no | `true` | Server-side refusal fallback (see [Design notes](#design-notes)). |

`.env` is in `.gitignore`. If `.env` still contains the placeholder, the code
treats the key as missing and sends nothing.

## Monday: run the live Claude API test

```bash
python -m src.main ping
python -m src.main ping --prompt "Name one use of embeddings in one sentence."
```

On success it prints the model, token usage and Claude's reply, and exits 0:

```
Model : claude-opus-5-5
Tokens: <n> input / <n> output
Reply : <one sentence from Claude>
```

Every call is capped at `max_tokens=1024` (thinking included) and classify
input at 4,000 characters. At Claude Opus 5.5 list prices ($4 / $20 per
million input / output tokens), one call therefore costs at most about
US$0.03. Typical calls cost well under one cent.

From Python:

```python
from src.api_client import ask_claude
print(ask_claude("Say hello in five words."))
```

## Tuesday: classify text and parse the JSON response

```bash
python -m src.main classify "The app crashes every time I export a PDF."
python -m src.main classify                   # prompts: Text to classify:
python -m src.main classify --prompt-only "I was charged twice this month."
```

**Example input:** `The app crashes every time I export a PDF.`

**Expected response schema** (printed as JSON, returned as a Python `dict`):

| Field | Type | Rule |
|-------|------|------|
| `category` | string | One of `bug_report`, `feature_request`, `billing`, `account_access`, `general_question`, `other` |
| `confidence` | number | 0 to 1 inclusive (booleans and strings are rejected) |
| `explanation` | string | Non-empty, at most 500 characters |

No other fields are allowed. An *illustrative* result (the shape is
guaranteed; Claude's actual wording will vary):

```json
{
  "category": "bug_report",
  "confidence": 0.95,
  "explanation": "The user describes a crash that happens during PDF export."
}
```

From Python:

```python
from src.classifier import classify_text
result = classify_text("Please add a dark mode.")   # -> {"category": ..., "confidence": ..., "explanation": ...}
```

### How the reply is handled

1. The input is checked: it must be non-empty and at most 4,000 characters.
   Longer input is rejected, never silently truncated.
2. Claude is called with a JSON-only system prompt. The text to classify is
   wrapped in `<text>` tags, and the prompt says to treat it as data.
3. **Structured outputs** (`output_config.format` with a JSON Schema) are on
   by default. The installed SDK (1.15) and `claude-opus-5-5` support them,
   and they constrain the reply to the schema. `--prompt-only` turns them off
   to rely on the prompt alone.
4. In either mode the reply is **not trusted**. `extract_text()` selects text
   blocks by type and rejects refusals and replies cut off at `max_tokens`.
   `parse_json_response()` uses `json.loads` (rejecting `NaN`/`Infinity`).
   `validate_classification()` checks every field. The only leniency is a
   reply that is entirely one Markdown code fence: that fence is unwrapped.
   The code never slices out "the part that looks like JSON".

### Errors

Every failure raises a documented exception. The CLI turns each one into a
one-line message on stderr and an exit code.

| Exception | When | CLI exit |
|-----------|------|----------|
| `MissingAPIKeyError` | `ANTHROPIC_API_KEY` unset, empty or placeholder (no request sent) | 2 |
| `ClaudeConfigError` | invalid optional setting, e.g. `CLAUDE_USE_FALLBACKS=maybe` | 2 |
| `ValueError` | empty or too-long input text (no request sent) | 2 |
| `ClaudeAuthenticationError` | HTTP 401 (bad key) or 403 (not permitted) | 1 |
| `ClaudeRateLimitError` | HTTP 429 after the SDK's automatic retries; `.retry_after` is kept | 1 |
| `ClaudeAPIError` | any other HTTP error (400, 404, 500, 529, ...); `.status_code` is kept | 1 |
| `ClaudeConnectionError` | network failure or timeout | 1 |
| `UnexpectedResponseError` | refusal, truncated reply, no text blocks, or malformed response | 1 |
| `EmptyResponseError` | reply text is empty | 1 |
| `MalformedJSONError` | reply is not valid JSON | 1 |
| `SchemaValidationError` | valid JSON with missing, extra or invalid fields | 1 |

The API errors share the base class `ClaudeClientError`. The parsing errors
share `ResponseParseError`. The original SDK exception is kept as `__cause__`.

## Run the tests

```bash
source /home/asuss/venvs/ai-ml-linux/bin/activate
cd /mnt/d/ai-ml-week1
python -m pytest -v
```

The tests need **no API key and no network**. `conftest.py` hides real
environment variables and the real `.env`, and blocks socket connections.
The Anthropic API is faked at the HTTP layer with `httpx2.MockTransport`.
The real SDK still builds each request, parses each response and raises its
own typed exceptions. Only the remote server is fake, and the JSON parsing
and validation code runs unmocked.

Coverage includes: request shape (model, `max_tokens`, effort,
structured-output schema, fallback beta header, no unsupported parameters);
config from env/`.env`/placeholder; text extraction (thinking blocks skipped,
multiple text blocks, empty content, missing/`None`/string content, non-JSON
body, refusal, truncation); 401/403/429/400/404/500/529 and network/timeout
errors; JSON parsing (valid, fenced, empty, malformed variants, NaN);
schema validation (each missing field, extra fields, wrong types/ranges);
the CLI's output, exit codes and that the key never appears in output.

## Design notes

- **Model and effort.** The default model is `claude-opus-5-5`. On this model
  thinking is always on, and `output_config.effort` is the cost and latency
  control. These short tasks use `effort: "low"`. `temperature`/`top_p`/`top_k`
  and `thinking: {type: "disabled"}` are rejected by this model and are never
  sent.
- **Refusal fallback.** Requests opt into `fallbacks: "default"` (beta header
  `server-side-fallback-2026-07-01`). If Claude's safety classifiers decline a
  request, the API retries it on Anthropic's recommended fallback model inside
  the same call. If your organization isn't enabled for this beta, the API
  answers 400 mentioning `anthropic-beta`. Set `CLAUDE_USE_FALLBACKS=false`
  to use the standard endpoint.
- **Secrets.** The key is read from the environment or `.env` and passed to
  the SDK only. `ClaudeSettings` hides it from `repr`. The error messages and
  CLI output never include it, and tests assert this.
- **Retries.** The SDK retries 408/409/429/5xx and connection errors twice
  with backoff. The code adds no retry loop of its own.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `ANTHROPIC_API_KEY is not configured` | Create `.env` from `.env.example` and set the key. |
| `HTTP 401` | Key mistyped or revoked. Ask your supervisor to check it. |
| `HTTP 400 ... credit balance` | The organization has no API billing set up. Ask your supervisor; do not buy credits yourself. |
| `HTTP 400 ... anthropic-beta` | Set `CLAUDE_USE_FALLBACKS=false` in `.env`. |
| `HTTP 404 ... model` | The `CLAUDE_MODEL` value is wrong or not available to the organization. |
| `HTTP 429` | Rate limited. Wait for the `retry-after` time and retry. |
| `Could not reach the Anthropic API` | Check internet/proxy settings inside WSL. |

## Live verification checklist (when credentials arrive)

1. `python -m src.main check-env` shows `configured (value hidden)`.
2. `python -m src.main ping` exits 0 and prints a reply. Record the date and output.
3. `python -m src.main classify "The app crashes when I export a PDF."` prints valid JSON.
4. `python -m src.main classify --prompt-only "Please add dark mode."` prints valid JSON.
5. `git status` shows `.env` is **not** listed (it is ignored).
6. Update the Status table above: change "Live Claude API call" to Done.

## Publishing to GitHub (after review)

The remote is not configured yet. After creating an empty `ai-ml-week1`
repository on GitHub (no README or .gitignore, to avoid a merge):

```bash
git remote add origin https://github.com/<your-username>/ai-ml-week1.git
git push -u origin main
```
