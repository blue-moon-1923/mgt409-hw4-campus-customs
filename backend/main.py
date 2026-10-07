"""Campus Customs storefront API — the app you run with uvicorn.

    cd backend
    uvicorn main:app --reload --port 8000

Serves four things to the React storefront:

- the product catalogue (`/api/products`)
- the product photographs (`/images/...`)
- accounts: sign-up, sign-in, sign-out, who-am-I (`/api/auth/...`)
- the chat assistant (`/api/chat`), which runs the PydanticAI agent in `agent.py`

This module is only the HTTP layer. The structured types live in `models.py`,
the catalogue queries and the agent's tools in `tools.py`, the agent wiring in
`agent.py`, and its instructions in `prompts/prompt.md`.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import auth
import tools
from agent import MODEL_NAME, PROMPT_PATH
from agent import run_agent
from models import (
    MIN_PASSWORD_LENGTH,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    CustomerContext,
    LoginRequest,
    PageContext,
    ProductCard,
    ProductDetail,
    ProductSummary,
    PublicUser,
    ShopDeps,
    SignupRequest,
    StoredChatMessage,
)

DB_PATH = tools.DB_PATH
IMAGE_DIR = tools.IMAGE_DIR

# Every column of `users` except `password_hash`. Selecting the columns by name
# means the hash cannot reach a response by accident.
PUBLIC_USER_COLUMNS = "id, first_name, last_name, email, created_at"

# Dev-grade brute-force brake: failed sign-in attempts per email address, held in
# memory only. It resets when the server restarts and is not shared across
# processes, so it slows guessing during class rather than standing in for a real
# rate limiter.
MAX_LOGIN_FAILURES = 10
LOGIN_WINDOW_SECONDS = 15 * 60
_login_failures: dict[str, list[float]] = {}

# How much of a signed-in customer's saved transcript is returned on sign-in.
HISTORY_LIMIT = 40

FIELD_LABELS = {
    "first_name": "First name",
    "last_name": "Last name",
    "email": "Email address",
    "password": "Password",
    "confirm_password": "Confirm password",
    "message": "Message",
}

app = FastAPI(
    title="Campus Customs",
    version="0.3.0",
    description="Catalogue, images, accounts, and the shop assistant.",
)

# The Vite dev server proxies /api and /images, so CORS is a convenience for
# anyone hitting the API directly from another origin during class.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return validation messages without echoing the submitted values.

    FastAPI's default 422 body includes the request payload, which on the sign-up
    form would send the password straight back in an error response. This handler
    keeps the messages and drops the input.
    """
    messages: list[str] = []
    for error in exc.errors():
        message = str(error.get("msg", "Invalid value.")).removeprefix("Value error, ")
        fields = [part for part in error.get("loc", ()) if part != "body"]
        label = FIELD_LABELS.get(str(fields[-1])) if fields else None
        messages.append(f"{label}: {message}" if label else message)
    return JSONResponse(status_code=422, content={"detail": " ".join(messages)})


def connect() -> sqlite3.Connection:
    """Read-only connection, used for every read path."""
    try:
        return tools.connect_ro()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Catalogue database is not available.")


def connect_rw() -> sqlite3.Connection:
    """Writable connection. Used only when creating an account."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Catalogue database is not available.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "database": DB_PATH.name,
        "database_present": DB_PATH.exists(),
        "session_secret_from_env": auth.SESSION_SECRET_FROM_ENV,
        "agent_model": MODEL_NAME,
        "prompt_file": str(PROMPT_PATH.relative_to(Path(__file__).resolve().parent)),
    }


# -------------------------------------------------------------------- catalogue


@app.get("/api/products", response_model=list[ProductSummary])
def list_products() -> list[ProductSummary]:
    """Every product in the catalogue, with a card-sized description."""
    return tools.load_product_summaries()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> ProductDetail:
    """One product, with the full description and per-size availability."""
    detail = tools.load_product_detail(product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No product with id {product_id!r}.")
    return detail


@app.get("/api/products/{product_id}/related", response_model=list[ProductSummary])
def related(product_id: str) -> list[ProductSummary]:
    """Other products in the same category, for the "More like this" row."""
    if tools.load_product_detail(product_id) is None:
        raise HTTPException(status_code=404, detail=f"No product with id {product_id!r}.")
    return tools.related_products(product_id)


# --------------------------------------------------------------------- accounts


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.make_session_token(user_id),
        max_age=auth.SESSION_TTL_SECONDS,
        httponly=True,  # unreadable from JavaScript
        samesite="lax",
        path="/",
        secure=False,  # the class app runs over plain http on localhost
    )


def fetch_public_user(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        f"SELECT {PUBLIC_USER_COLUMNS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def signed_in_user(request: Request) -> PublicUser | None:
    """The account behind the session cookie, or None when nobody is signed in."""
    user_id = auth.read_session_token(request.cookies.get(auth.SESSION_COOKIE))
    if user_id is None:
        return None
    conn = connect()
    try:
        row = fetch_public_user(conn, user_id)
    finally:
        conn.close()
    return PublicUser(**dict(row)) if row else None


def login_is_locked(email: str) -> bool:
    cutoff = time.time() - LOGIN_WINDOW_SECONDS
    recent = [stamp for stamp in _login_failures.get(email, []) if stamp > cutoff]
    _login_failures[email] = recent
    return len(recent) >= MAX_LOGIN_FAILURES


@app.post("/api/auth/signup", response_model=PublicUser, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response) -> PublicUser:
    """Create an account, then sign the new customer in."""
    email = payload.email.strip().lower()
    password_hash = auth.hash_password(payload.password)

    conn = connect_rw()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                f"{payload.first_name} {payload.last_name}",
                email,
                password_hash,
                payload.first_name,
                payload.last_name,
            ),
        )
        conn.commit()
        row = fetch_public_user(conn, int(cursor.lastrowid))
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for that email address.",
        )
    finally:
        conn.close()

    assert row is not None
    set_session_cookie(response, row["id"])
    return PublicUser(**dict(row))


@app.post("/api/auth/login", response_model=PublicUser)
def login(payload: LoginRequest, response: Response) -> PublicUser:
    """Verify a password against the stored hash and start a session."""
    email = payload.email.strip().lower()
    if login_is_locked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please wait a few minutes and try again.",
        )

    conn = connect()
    try:
        credentials = conn.execute(
            "SELECT id, password_hash FROM users WHERE lower(email) = ?", (email,)
        ).fetchone()

        # `verify_password` runs the full hash even when the email is unknown, so a
        # wrong address and a wrong password take the same amount of time.
        if not auth.verify_password(
            payload.password, credentials["password_hash"] if credentials else None
        ):
            _login_failures.setdefault(email, []).append(time.time())
            # One message for both cases: do not reveal which addresses are registered.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="That email address and password do not match an account.",
            )

        _login_failures.pop(email, None)
        row = fetch_public_user(conn, int(credentials["id"]))
    finally:
        conn.close()

    assert row is not None
    set_session_cookie(response, row["id"])
    return PublicUser(**dict(row))


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(auth.SESSION_COOKIE, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@app.get("/api/auth/me", response_model=PublicUser)
def current_user(request: Request) -> PublicUser:
    """Who the session cookie belongs to, so a reload keeps the customer signed in."""
    user = signed_in_user(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in.")
    return user


# ------------------------------------------------------------------------- chat


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Build the chat's product cards from the database, not from model text.

    The agent returns ids; every card is then read out of `catalogue` and
    `inventory`. An id the model invented simply resolves to nothing and is
    dropped, so a card can never show a price, photo, or name the catalogue does
    not actually contain.
    """
    cards: list[ProductCard] = []
    for product_id in dict.fromkeys(product_ids):
        detail = tools.load_product_detail(product_id)
        if detail is None:
            continue
        cards.append(
            ProductCard(
                product_id=detail.product_id,
                name=detail.name,
                garment_type=detail.garment_type,
                price=detail.price,
                image_url=detail.image_url,
                short_description=detail.short_description,
                in_stock=detail.in_stock,
                colors=detail.colors,
                available_sizes=detail.available_sizes,
                sold_out_sizes=[s.size for s in detail.sizes if s.quantity == 0],
            )
        )
    return cards


def save_chat_message(
    user_id: int, role: str, content: str, products: list[ProductCard] | None = None
) -> None:
    """Append one turn to `chat_messages` for a signed-in customer.

    Guests are never written here: this is only called when a session cookie
    resolved to an account. `products_json` keeps the cards that went with an
    assistant reply, so a reloaded transcript looks the way it did live.
    """
    payload = (
        json.dumps([card.model_dump() for card in products], ensure_ascii=False)
        if products
        else None
    )
    conn = connect_rw()
    try:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json)"
            " VALUES (?, ?, ?, ?)",
            (user_id, role, content, payload),
        )
        conn.commit()
    finally:
        conn.close()


def load_chat_history(user_id: int, limit: int = HISTORY_LIMIT) -> list[StoredChatMessage]:
    """The customer's own saved transcript, oldest first.

    Scoped to one `user_id` by the query itself, so there is no request shape
    that returns somebody else's conversation.
    """
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages"
            " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    messages: list[StoredChatMessage] = []
    for row in reversed(rows):
        # Only the product ids are taken from the stored row; each card is then
        # rebuilt from the database. That way a restored transcript shows today's
        # price and stock rather than a snapshot from weeks ago, and rows written
        # by an earlier build in a different shape still render.
        stored_ids: list[str] = []
        if row["products_json"]:
            try:
                stored = json.loads(row["products_json"])
            except json.JSONDecodeError:
                stored = []
            stored_ids = [
                str(item["product_id"])
                for item in (stored if isinstance(stored, list) else [])
                if isinstance(item, dict) and item.get("product_id")
            ]
        cards: list[ProductCard] = product_cards(stored_ids)
        messages.append(
            StoredChatMessage(
                role=row["role"],
                content=row["content"],
                products=cards,
                created_at=row["created_at"],
            )
        )
    return messages


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(request: Request) -> ChatHistoryResponse:
    """The signed-in customer's saved conversation. Guests get an empty list."""
    user = signed_in_user(request)
    if user is None:
        return ChatHistoryResponse(messages=[])
    return ChatHistoryResponse(messages=load_chat_history(user.id))


def build_deps(user: PublicUser | None, page: PageContext | None) -> ShopDeps:
    """Assemble what the agent is told about who is asking and from where.

    The page `product_id` arrives from the client but is never trusted for
    product facts: the agent resolves it against the database through
    `get_page_product`, so a tampered request cannot put a false price or name in
    front of the model.
    """
    customer = (
        CustomerContext(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )
        if user
        else None
    )
    return ShopDeps(customer=customer, page=page)


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """One turn of the shop assistant.

    Takes the customer's message plus the recent transcript the widget is
    holding, runs the agent, then resolves the product ids it cited into cards.
    If a customer is signed in, their first name is passed through so the
    assistant can greet them; nothing else from the account is.
    """
    user = signed_in_user(request)
    reply, tools_used = run_agent(
        payload.message,
        history=payload.history,
        deps=build_deps(user, payload.page),
    )
    cards = product_cards(reply.referenced_product_ids)

    # Only a signed-in customer's conversation is kept. A guest's chat lives in
    # their browser tab and is never written to the database.
    if user is not None:
        save_chat_message(user.id, "user", payload.message)
        save_chat_message(user.id, "assistant", reply.reply, cards)

    return ChatResponse(
        reply=reply.reply,
        products=cards,
        # A heading with nothing under it would caption an empty grid.
        results_heading=reply.results_heading.strip() if cards else "",
        tools_used=tools_used,
    )


# Product photographs, served straight from the course data pack.
if IMAGE_DIR.is_dir():
    app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

__all__ = ["app", "MIN_PASSWORD_LENGTH"]
