# Campus Customs — MGT 409 Homework 4

A Yale apparel storefront with an AI shop assistant. React + Vite + TypeScript on the front,
FastAPI on the back, and a PydanticAI agent that answers questions about the catalogue using
tools that read the shop's SQLite database — so every price, size, and stock figure it quotes
is a real column value rather than a guess.

Ask it *"what t-shirts do you sell?"* and the website itself rebuilds into a results grid.
Ask *"do you have this in large?"* on a product page and it knows what "this" means.

---

## What you need

- **Python 3.12+**
- **Node.js 20+**
- A **Portkey API key** for the model (`gpt-5.6-luna`)
- The **course data pack** (see the next section — it is not in this repository)

## 1. Put the data pack in place

The catalogue database and the product photographs are course-supplied and are **not**
committed here. Unzip the data pack into this folder so that it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/            # images referenced by the catalogue
```

From the folder containing this README:

```bash
unzip ~/Downloads/data.zip -d .
```

`data/` is listed in `.gitignore`, so it stays local.

## 2. Add your key

```bash
cp .env.example .env
```

Then open `.env` and set `PORTKEY_API_KEY` to your own key. `.env` is git-ignored and must
never be committed. Setting `CAMPUS_CUSTOMS_SESSION_SECRET` as well is optional but means a
backend restart will not sign everyone out.

## 3. Run the backend

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```

The API is now on <http://127.0.0.1:8000>, with interactive docs at
<http://127.0.0.1:8000/docs>.

## 4. Run the frontend

In a second terminal, from this folder:

```bash
cd frontend
npm install
npm run dev
```

Open **<http://127.0.0.1:5173>**.

The Vite dev server proxies `/api` and `/images` through to port 8000, so no base URL is
hard-coded anywhere in the frontend and the two servers behave as one origin.

### Signing in

The data pack ships with a test account. Its email is `test@campuscustoms.yale.edu`; the
password is the one given in the assignment prompt. You can also create a new account
through the site — passwords are stored only as salted PBKDF2 hashes.

---

## Layout

```
hw4/
├── AI_prompts.md              every prompt typed while building this, in order
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/                  # Vite React TypeScript app
├── backend/
│   ├── main.py                # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py               # agent wiring: model, prompt, tools, limits, audit trail
│   ├── models.py              # every Pydantic structured type
│   ├── tools.py               # catalogue access + the tools the agent may call
│   ├── auth.py                # password hashing and session tokens
│   ├── perf_check.py          # measures SQL statement counts and timings
│   └── prompts/
│       └── prompt.md          # the system prompt: voice, grounding, safety rules
└── output/
    ├── harness.md             the full system write-up — start here
    ├── design.md
    ├── usability.md
    ├── app_check.html         screenshots of the running site
    ├── app_check_images/      # screenshots linked from app_check.html
    └── audit_trail.json       append-only record of every agent turn
```

The agent itself is the four files named in the assignment — `prompts/prompt.md`,
`agent.py`, `tools.py`, and `models.py`. `auth.py` and `perf_check.py` sit beside them
because sign-in and the performance measurement in `output/usability.md` need them; neither
is part of the agent.

## Where to look first

**`output/harness.md`** is the complete write-up. Section 9 is a self-contained reference:
the database schema, every Pydantic model and why its fields were chosen, all seven tools,
the safety rules, every loop limit and result cap, and these run instructions.

**`output/app_check.html`** opens in a browser and shows three screenshots of the running
site with the assistant's figures checked against the database.

## Quick checks without the browser

```bash
cd backend
python agent.py "do you have any navy hoodies in large?"   # one turn from the terminal
python perf_check.py                                       # SQL statement counts and timings
```

Both append to `output/audit_trail.json`, which is never wiped.

---

Coursework for MGT 409, AI Foundations for Managers. Campus Customs is a fictional shop.
The campus photograph in the hero is *Harkness Tower Canopy* by Carol M. Highsmith, from her
Library of Congress collection, which is dedicated to the public domain.
