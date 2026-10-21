# ai-ml-week1

Week 1 assignments for my AI/ML Engineer internship: the **Monday** and
**Tuesday** tasks from the internship roadmap.

| Day | Roadmap task | What this repo contains |
|-----|--------------|-------------------------|
| Monday | Configure Git, prepare the Python environment, make a working test call to the Claude API | `src/api_client.py`: configuration loading, one Messages API call, text extraction and error handling. `python -m src.main ping` is the live test call. |
| Tuesday | A script that calls Claude and parses its JSON response | `src/classifier.py` + `src/response_parser.py`: classify a short text into a category, parse Claude's reply with `json`, and validate it against a schema. `python -m src.main classify "..."` runs it. |

Wednesday (embeddings), Thursday (semantic search) and Friday (review) are
**out of scope** for this repository so far.

The repo also contains an **optional alternative provider, Groq**
(`src/groq_client.py`). It runs the same classification task through the
official OpenAI Python SDK pointed at Groq's OpenAI-compatible API.

> **Important: Groq does not complete the Claude API requirement.** The
> roadmap's Monday task is a working call to the **Claude API**. A successful
> Groq call, Groq test or Groq key does not satisfy it. The Claude code paths
> are completely separate (`ANTHROPIC_API_KEY`, `ping`, `classify`) and still
> need a live run once Claude credentials are available.

## Status

| Item | Status |
|------|--------|
| Git repository and `.gitignore` | Done |
| Python environment verified (`check-env`) | Done |
| Claude API client (`api_client.py`) | Done, verified against mocked HTTP responses |
| JSON parsing and schema validation (`response_parser.py`) | Done, verified by unit tests |
| Classification workflow and CLI (`classifier.py`, `main.py`) | Done, verified against mocked HTTP responses |
| Automated tests (offline) | Passing (see [Run the tests](#run-the-tests)) |
| **Live Claude API call** | **Pending.** `ANTHROPIC_API_KEY` is not configured and no live Claude request has been made. The successful Groq test below does not change this. |
| Optional Groq provider (`groq_client.py`, `groq-classify`) | Done, verified by mocked tests and one live request |
| Live Groq API call | **Passed** (2026-10-21): one request, succeeded on the first attempt, exit code 0, JSON passed schema validation. Optional, and separate from the Claude requirement. |

## Project structure

```
ai-ml-week1/
├── src/
│   ├── __init__.py
│   ├── api_client.py       # Monday: settings, SDK client, send_message(), extract_text(), errors
│   ├── response_parser.py  # Tuesday: JSON parsing + schema validation (pure, no network)
│   ├── classifier.py       # Tuesday: classify_text() workflow (prompt -> API -> parse -> validate)
│   ├── groq_client.py      # optional alternative provider: Groq via the OpenAI SDK
│   └── main.py             # CLI: check-env, ping, classify, groq-classify
├── tests/
│   ├── fakes.py            # fake Anthropic and Groq APIs at the HTTP layer (MockTransport)
│   ├── conftest.py         # isolates env vars/.env and blocks real network access
│   ├── test_api_client.py
│   ├── test_response_parser.py
│   ├── test_classifier.py
│   ├── test_groq_client.py
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
openai            : 2.54.0
httpx             : 0.28.1
pytest            : 9.1.1
ANTHROPIC_API_KEY : not configured - live API calls are unavailable
GROQ_API_KEY      : not configured - optional Groq provider unavailable
```

## Configure credentials

Do this only once your supervisor provides an API key with billing enabled.

```bash
test -f .env || cp .env.example .env   # copy the template only if .env does not exist yet
nano .env                 # add or edit the line ANTHROPIC_API_KEY=<the real key>
python -m src.main check-env   # should now say: configured (value hidden)
```

Never run a plain `cp .env.example .env` once `.env` exists. It would
overwrite the file and erase keys already in it, such as `GROQ_API_KEY`.
`chmod 600` has no effect on Windows drives such as `/mnt/d`. `.gitignore`
is what keeps `.env` out of Git.

You can export the variable in your shell instead (`export ANTHROPIC_API_KEY=...`).
A non-empty environment variable takes precedence over `.env`.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ANTHROPIC_API_KEY` | yes (Claude) | none | API key. Never printed, logged or committed. |
| `CLAUDE_MODEL` | no | `claude-opus-5-5` | Model ID to call. |
| `CLAUDE_USE_FALLBACKS` | no | `true` | Server-side refusal fallback (see [Design notes](#design-notes)). |
| `GROQ_API_KEY` | only for `groq-classify` | none | Optional Groq key. Does **not** replace `ANTHROPIC_API_KEY`. |
| `GROQ_MODEL` | no | `openai/gpt-oss-20b` | Groq model ID. |

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

## Optional: Groq as an alternative provider

> Running anything in this section does **not** complete the Monday Claude API
> task. Keep the Claude row in the Status table as Pending until
> `python -m src.main ping` succeeds with a real Claude key.

`src/groq_client.py` runs the same classification task through Groq. It uses
the official **OpenAI Python SDK** (`openai` 2.x) with
`base_url="https://api.groq.com/openai/v1"`. It shares the `.env` file, the
system prompt, input limits, and the JSON parsing and schema validation with
the Claude workflow. It has its own settings, client, errors and CLI command,
and does not change `api_client.py`.

**Setup.** `.env` already has an empty `GROQ_API_KEY=` line. Open it in an
editor (`nano .env`), paste your key from https://console.groq.com/keys after
the `=` (no quotes), save, and confirm with `python -m src.main check-env`.

**Run.**

```bash
python -m src.main groq-classify "I was charged twice this month."
python -m src.main groq-classify --json-object "Please add a dark mode."
```

From Python:

```python
from src.groq_client import classify_text_with_groq
result = classify_text_with_groq("Please add a dark mode.")   # same dict shape as classify_text()
```

The output uses the same schema as the Claude `classify` command (see
[the schema table](#tuesday-classify-text-and-parse-the-json-response)).

**Model choice.** The default is `openai/gpt-oss-20b`. As of 2026-10-21,
Groq's docs list it as a production model (not a preview), not deprecated,
with strict JSON-schema structured outputs. `openai/gpt-oss-120b` also
qualifies and can be set with `GROQ_MODEL`. Groq retires models regularly;
check https://console.groq.com/docs/deprecations if you get an HTTP 404.

**Structured JSON.** By default the request sends
`response_format={"type": "json_schema", "json_schema": {"name": "text_classification", "strict": true, "schema": ...}}`,
so Groq constrains decoding to the schema. `--json-object` switches to
`{"type": "json_object"}`, which guarantees valid JSON syntax only. Either
way the reply goes through the same `json.loads` and schema validation as
Claude's. GPT-OSS models also get `reasoning_effort="low"`. Their reasoning
arrives in a separate `reasoning` field and is ignored; only
`message.content` is parsed.

**Groq errors.** These are separate from the Claude exceptions; the shared
parsing errors are the same.

| Exception | When | CLI exit |
|-----------|------|----------|
| `MissingGroqAPIKeyError` | `GROQ_API_KEY` unset, empty or placeholder (no request sent) | 2 |
| `GroqAuthenticationError` | HTTP 401 (bad key) or 403 (not permitted) | 1 |
| `GroqRateLimitError` | HTTP 429 after the SDK's automatic retries; `.retry_after` is kept | 1 |
| `GroqAPIError` | any other HTTP error; `.status_code` and Groq's `.code` (e.g. `json_validate_failed`, `model_not_found`) are kept | 1 |
| `GroqConnectionError` | network failure or timeout | 1 |
| `GroqUnexpectedResponseError` | no choices, `finish_reason` `length`/`content_filter`, refusal, or no text content | 1 |
| `EmptyResponseError` / `MalformedJSONError` / `SchemaValidationError` | same as for Claude | 1 |

All Groq API errors share the base class `GroqClientError`.

## Run the tests

```bash
source /home/asuss/venvs/ai-ml-linux/bin/activate
cd /mnt/d/ai-ml-week1
python -m pytest -v
```

The tests need **no API key and no network**. `conftest.py` hides real
environment variables and the real `.env`, and blocks socket connections.
The Anthropic API is faked at the HTTP layer with `httpx2.MockTransport`, and
Groq with `httpx.MockTransport` (the openai SDK uses `httpx`). Each real SDK
still builds each request, parses each response and raises its own typed
exceptions. Only the remote servers are fake, and the JSON parsing and
validation code runs unmocked.

Coverage includes: request shape (model, `max_tokens`, effort,
structured-output schema, fallback beta header, no unsupported parameters);
config from env/`.env`/placeholder; text extraction (thinking blocks skipped,
multiple text blocks, empty content, missing/`None`/string content, non-JSON
body, refusal, truncation); 401/403/429/400/404/500/529 and network/timeout
errors; JSON parsing (valid, fenced, empty, malformed variants, NaN);
schema validation (each missing field, extra fields, wrong types/ranges);
the CLI's output, exit codes and that the key never appears in output.

Groq coverage (`test_groq_client.py`, plus CLI tests in `test_main.py`):
- Config: key from env or `.env`; empty and placeholder keys count as
  missing; a Groq key never satisfies the Claude key, and the Claude key is
  never used for Groq.
- Request shape: Groq base URL, Bearer auth, model, strict `json_schema`
  vs `json_object`, `reasoning_effort` sent only to GPT-OSS models, and none
  of the fields Groq rejects.
- Extraction: missing, `None` or empty choices; non-JSON body; `null`
  content; `length`/`content_filter`; refusal.
- Errors: 401/403/429/400 (`json_validate_failed`)/404/500/503 and
  network/timeout.
- Classification: malformed JSON, empty reply, schema violations, input
  limits.
- CLI: the key never appears in output.

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
- **Secrets.** Both keys are read from the environment or `.env` and passed
  to their own SDK only. `ClaudeSettings` and `GroqSettings` hide them from
  `repr`. The error messages and CLI output never include them, and tests
  assert this.
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
| `GROQ_API_KEY is not configured` | Put your Groq key after `GROQ_API_KEY=` in `.env`. Only needed for `groq-classify`. |
| Groq `HTTP 404 ... model_not_found` | The Groq model was retired or mistyped. Check Groq's deprecations page and set `GROQ_MODEL`. |
| Groq `HTTP 400 ... json_validate_failed` | Groq could not produce JSON matching the schema. Retry, or rephrase the input. |

## Live verification checklist (when credentials arrive)

### Claude (required for Monday): pending

`ANTHROPIC_API_KEY` is not configured, and no live Claude request has been made.

1. `python -m src.main check-env` shows `configured (value hidden)`.
2. `python -m src.main ping` exits 0 and prints a reply. Record the date and output.
3. `python -m src.main classify "The app crashes when I export a PDF."` prints valid JSON.
4. `python -m src.main classify --prompt-only "Please add dark mode."` prints valid JSON.
5. `git status` shows `.env` is **not** listed (it is ignored).
6. Update the Status table above: change "Live Claude API call" to Done.

Steps 1-6 need a **Claude** key. Running `groq-classify` with a Groq key is a
separate, optional check and does not tick any of them.

### Groq (optional): passed on 2026-10-21

- [x] `python -m src.main check-env` showed `GROQ_API_KEY : configured (value hidden)`.
- [x] `python -m src.main groq-classify "I was charged twice this month."` exited 0.
  One live request was sent, and it succeeded on the first attempt.
- [x] The reply was valid JSON and passed schema validation:

```json
{
  "category": "billing",
  "confidence": 0.99,
  "explanation": "The user reports being charged twice, which is a billing issue."
}
```

## Publishing to GitHub (after review)

The remote is not configured yet. After creating an empty `ai-ml-week1`
repository on GitHub (no README or .gitignore, to avoid a merge):

```bash
git remote add origin https://github.com/<your-username>/ai-ml-week1.git
git push -u origin main
```
