# Campus Customs

A Yale-inspired merchandise storefront with an AI shopping assistant, built for AI Foundations for Managers, Homework 4.

- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Backend:** FastAPI (`backend/main.py`)
- **AI agent:** PydanticAI with read-only database tools (`backend/agent.py`, `backend/tools.py`, `backend/models.py`, `backend/prompts/prompt.md`)
- **Data:** the supplied Campus Customs SQLite catalogue and product images (kept local, **not** in this repository)

See [`output/harness.md`](output/harness.md) for the full system reference: architecture, models, tools, safety rules, limits, and audit trail.

## Repository layout

```
hw4/
├── backend/
│   ├── main.py              # FastAPI entry point (products, auth, chat, history)
│   ├── agent.py             # PydanticAI agent: model, context, loop limits, audit events
│   ├── tools.py             # Read-only SQLite tools the agent can call
│   ├── models.py            # Pydantic request / tool-result / response models
│   ├── audit.py             # Append-only audit trail writer
│   └── prompts/prompt.md    # System prompt and safety rules
├── frontend/                # Vite + React + TypeScript storefront
├── output/
│   ├── harness.md           # System documentation
│   ├── design.md            # Design decisions (Problem 10)
│   ├── usability.md         # Usability improvements (Problem 9)
│   ├── app_check.html       # Visual test report (Problem 11)
│   ├── app_check_images/    # Screenshots used by app_check.html
│   └── audit_trail.json     # Append-only agent audit log (Problem 12)
├── data/                    # NOT committed: place the local data pack here (see below)
├── AI_prompts.md            # Prompts used for each problem
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration template (placeholders only)
└── .gitignore
```

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer (includes `npm`)
- An OpenAI API key (or the course Portkey key) for the chat assistant
- The Campus Customs data pack (`data.zip`), supplied separately with the assignment

## 1. Add the local data pack

The database and product images are not published. Place them so the folder looks like this:

```
hw4/data/campus_customs.db
hw4/data/products/*.jpg
```

`data.zip` already contains a top-level `data/` folder, so extract it **inside `hw4/`**:

```powershell
cd hw4
Expand-Archive data.zip -DestinationPath .
```

On macOS/Linux, run `unzip data.zip` from inside `hw4/`. The backend refuses to start with a clear error if `data/campus_customs.db` or `data/products/` is missing.

## 2. Configure environment variables

Copy the template and fill in your own values:

```powershell
Copy-Item .env.example .env
```

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes, unless using Portkey | OpenAI key for the assistant |
| `PORTKEY_API_KEY` / `PORTKEY_BASE_URL` | Alternative | Course Portkey gateway, used only when `OPENAI_API_KEY` is not set |
| `CAMPUS_CUSTOMS_AI_MODEL` | Optional | Model name (configured: `gpt-5.6-luna`) |
| `CAMPUS_CUSTOMS_SESSION_SECRET` | Recommended | Long random string that signs login tokens; keep it stable so logins survive restarts |

`.env` is git-ignored and loaded automatically by the backend. Never commit it.

## 3. Start the backend (terminal 1)

From `hw4/`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

On macOS/Linux, activate with `source .venv/bin/activate`. You can also start it from `hw4/` with `python -m uvicorn backend.main:app --reload --port 8000`.

The API runs at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`. Product and image endpoints work without an API key; only the chat needs one.

## 4. Start the frontend (terminal 2)

From `hw4/`:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. During development, Vite forwards `/api` and `/product-images` requests to the backend on port 8000. If the backend uses a different address, set `VITE_API_TARGET` before `npm run dev`.

## Try it

- Log in with the supplied test account `test@campuscustoms.yale.edu` / `password`, or create a new account.
- Ask the assistant “What hoodies do you have?” and matching product cards appear on the page.
- On a product page, ask “How many are left in size L?” and the answer comes from the inventory table.
- Each chat appends events to `output/audit_trail.json`.

## Routes

| Route | Page |
|---|---|
| `/` | Home |
| `/products` | Catalogue with keyword and category filters |
| `/products/:productId` | Product detail with sizes and stock |
| `/about` | About Campus Customs |
| `/login` | Log in |
| `/create-account` | Create an account |

## Data and security notes

- Catalogue and inventory are read in SQLite query-only mode. Registration writes to `users`, and logged-in chat history writes to `chat_messages`, both in your local database.
- Passwords are stored only as PBKDF2-SHA256 hashes. Secrets come from `.env` or environment variables, never from source code.
- `data/`, `data.zip`, all `*.db` files, `.env`, virtual environments, `node_modules/`, and build output are excluded by `.gitignore`.
- `frontend/_capture_app_check.mjs` is the optional script used to capture the Problem 11 screenshots. It expects the app running at `http://127.0.0.1:5174` and a local Chrome install.
