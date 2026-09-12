# Multi-Agent Research Pipeline

A multi-agent research pipeline (Supervisor -> Researcher -> Validator ->
Writer -> Quality -> Human review) exposed as a web API, deployable on
**Render** (backend) and **Vercel** (frontend).

```
USER
  -> Supervisor Agent      (breaks the request into a research plan)
  -> Researcher Agent      (runs real web searches, summarizes findings)
  -> Validator Agent       (real ticker check + LLM review of the research)
  -> Writer Agent          (turns research into a report)
  -> Quality Agent         (checks the report meets standards)
       |
       +-- if rejected --> back to Writer (up to 3 times)
  -> Human-in-the-Loop     (you approve or reject via the web UI)
       |
       +-- if rejected: "research" reason --> back to Researcher
       +-- if rejected: "writing"/"other"  --> back to Writer
       (up to 2 retries)
  -> FINAL OUTPUT
```

## Why this version is different from before

A script that calls Python's `input()` cannot run on Render or Vercel —
both platforms run your code as a **web server** answering HTTP requests,
there's no terminal for a human to type into. So the human-approval step
is now a real API: the backend pauses and waits for an approve/reject
**HTTP request** instead of a keyboard prompt. A tiny web page (deployed
on Vercel) is what actually shows you the report and sends that request.

## Project structure

```
multi-agent-app/
├── .env.example          # copy to .env and fill in your real key — never commit .env
├── .gitignore              # makes sure .env and __pycache__ never get committed
├── requirements.txt
├── render.yaml              # tells Render how to run the backend
├── config.py                  # loads .env, holds all tunable settings
├── api.py                       # FastAPI app — THIS is what Render runs
├── pipeline.py                    # core orchestration logic (agent order, loops)
├── agents/
│   ├── supervisor.py
│   ├── researcher.py
│   ├── validator.py
│   ├── writer.py
│   └── quality.py
├── human/
│   └── review_store.py             # in-memory "pending review" tracking (replaces input())
├── core/
│   ├── llm_client.py
│   ├── search.py
│   └── finance.py
└── frontend/                         # deployed separately, on Vercel
    ├── index.html                      # the page you actually use to run/approve reports
    ├── app.js
    └── vercel.json
```

## The `.env` file (this is what was missing)

Your API key must never be hardcoded or committed to git. Instead:

1. Copy the example file:
   ```
   cp .env.example .env
   ```
2. Open `.env` and put your real key in:
   ```
   GROQ_API_KEY=gsk_your_real_key_here
   ```
3. `config.py` loads this automatically via `python-dotenv`. `.gitignore`
   already excludes `.env` from git, so it never gets pushed or exposed.

On Render, you won't upload `.env` at all — you'll paste the same key into
Render's **Environment Variables** dashboard setting instead (covered below).

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your real key
uvicorn api:app --reload
```

Open `frontend/index.html` directly in your browser (or serve it), point
it at `http://localhost:8000`, and use the page to submit a question and
approve/reject reports.

## Deploying the backend to Render

1. Push this project to a GitHub repo.
2. In Render: **New -> Web Service**, connect the repo.
3. Render reads `render.yaml` automatically and sets:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. In the Render dashboard, go to **Environment** and add:
   - `GROQ_API_KEY` = your real key
5. Deploy. Render gives you a URL like `https://your-app.onrender.com`.

## Deploying with Docker instead (optional)

If you'd rather run this as a container — on Render, on any other host, or
just locally — nothing in the application code changes. Only two new files
were added for this:

- **`Dockerfile`** — builds the same backend (`api.py`) into a container image.
- **`.dockerignore`** — keeps `.env`, `frontend/`, and other clutter out of
  the image (mirrors what `.gitignore` does for git).

Build and run it locally:
```bash
docker build -t multi-agent-app .
docker run -p 8000:8000 --env-file .env multi-agent-app
```
`--env-file .env` passes your `GROQ_API_KEY` into the container at runtime —
the key is never baked into the image itself (that's what `.dockerignore`
excluding `.env` guarantees).

**Or, one command instead of two**, using the included `docker-compose.yml`:
```bash
docker compose up --build
```
This does the same build + run as the two commands above, reading your
`.env` file automatically. Stop it with `Ctrl+C`, or run it in the
background with `docker compose up --build -d` and stop it later with
`docker compose down`.

To deploy this image instead of Render's native Python build:
- **Render**: when creating the Web Service, choose **"Existing Dockerfile"**
  as the environment instead of "Python 3" — Render will build and run the
  `Dockerfile` directly. You still set `GROQ_API_KEY` under Environment,
  exactly as before; `render.yaml` isn't needed in this mode.
- **Any other container host** (Fly.io, Railway, a VPS, etc.): build the
  image with the command above, push it to a registry, and run it with
  `GROQ_API_KEY` set as an environment variable at runtime.

The frontend (`frontend/`) is intentionally excluded from the Docker image
and still deploys separately to Vercel as a static site — Docker only
changes how the backend API is packaged and run.

## Deploying the frontend to Vercel

1. Open `frontend/app.js` and set `API_BASE_URL` to your Render URL from
   above.
2. In Vercel: **New Project**, point it at the `frontend/` folder (or the
   whole repo with root directory set to `frontend`).
3. Vercel serves it as a static site — no build step needed, `vercel.json`
   handles the routing.

## What's real (not simulated)

- **Web search**: the Researcher runs real DuckDuckGo queries.
- **Ticker validation**: the Validator checks tickers against live Yahoo
  Finance data, not an LLM guess.
- **Quality feedback loop**: real retries (up to `MAX_QUALITY_REVISIONS`).
- **Human rejection routing**: real retries, routed by reason (up to
  `MAX_HUMAN_REJECTIONS`), now driven by API calls from the web page
  instead of terminal input.
- **No database** — pending reviews are held in memory (a Python dict)
  while the server is running. This is NOT persistent storage: if the
  server restarts mid-review, that pending review is lost. That's a
  deliberate simplification, not an oversight — say the word if you want
  this backed by a real database later (e.g. for surviving restarts).

## Troubleshooting

**Getting a plain "Internal Server Error" from `/pipeline/run`?** FastAPI
hides the real exception in the HTTP response. Check the terminal running
`docker compose up` (or `uvicorn` directly) — the full Python traceback
prints there. Common cause: Groq periodically deprecates models: see
https://console.groq.com/docs/deprecations for the current list. If your
model has been deprecated, set `GROQ_MODEL` in `.env` to a supported one
(no code changes needed — `config.py` reads it automatically).

## Known limitation in this sandbox (not your machine or Render)

This was built and tested in a sandboxed environment whose network only
allows package registries (pypi, npm, etc.) — not general internet access
or Render/Vercel's own infrastructure. So I could not run a live DuckDuckGo
search, a live Yahoo Finance lookup, or an actual deployment from here.
Everything is syntax-checked and import-tested. Once deployed on your
Render/Vercel accounts (which do have full internet access), the live
calls should work directly — if something errors, send me the exact
message and I'll fix it.

The Docker setup specifically: this sandbox doesn't have Docker installed,
so I could not actually build or run the image here. I hand-checked that
the `Dockerfile`'s `CMD` matches `api.py`'s app name and that
`COPY requirements.txt .` points at the right file, but the build itself
is untested. Try `docker build -t multi-agent-app .` on your machine —
if it fails, send me the error and I'll fix the `Dockerfile`.
