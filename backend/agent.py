"""Campus Customs chat agent: PydanticAI + Portkey, catalogue tools only.

Wiring lives here and nowhere else:

- the system prompt is read from `prompts/prompt.md` at request time
- the model is `gpt-5.6-luna` through the Portkey OpenAI gateway
- the tools are exactly the three in `tools.AGENT_TOOLS`
- the output is validated into `models.ChatReply`

The API key is read from the environment, is never written to a log, a response,
or an error message, and is scrubbed from any exception text before it leaves
this module.

Run a one-off question from this folder:  python agent.py "do you have navy hoodies?"
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    BaseToolCallPart,
    BaseToolReturnPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.usage import UsageLimits  # noqa: E402

from models import AuditEntry, AuditToolCall, ChatReply, ChatTurn, ShopDeps  # noqa: E402
from tools import AGENT_TOOLS, load_product_detail  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"

def _load_env() -> None:
    """Load the first .env found walking up from this file.

    Works whether the project sits on its own (hw4/.env) or inside the wider
    coursework repository, without hard-coding how deep it is.
    """
    here = Path(__file__).resolve()
    for folder in (here.parent, *here.parents):
        candidate = folder / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return


_load_env()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-luna").strip() or "gpt-5.6-luna"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")

# Caps on one chat turn, so a single customer message cannot run away.
MAX_MODEL_REQUESTS = 6
MAX_HISTORY_TURNS = 8

# Audit trail. Appended to on every turn and never rewritten in place.
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
AUDIT_ARG_CHARS = 160
AUDIT_RESULT_CHARS = 220
AUDIT_TEXT_CHARS = 300
_audit_lock = threading.Lock()

FALLBACK_REPLY = (
    "Sorry, I could not reach the shop assistant just now. "
    "Please try again in a moment, or browse the products page."
)


def _api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        # Names the variable, never a value.
        raise RuntimeError("PORTKEY_API_KEY is not set. Put it in the repository root .env.")
    return key


def _redact(text: str) -> str:
    """Remove the API key from text before it is logged or returned.

    Provider errors sometimes quote the request, including headers. Scrubbing
    here means a stack trace or an error string can never carry the key.
    """
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    return text.replace(key, "[redacted]") if key else text


@lru_cache(maxsize=1)
def _model() -> OpenAIResponsesModel:
    """Build the Portkey-backed model once per process."""
    key = _api_key()
    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def system_prompt() -> str:
    """The instructions in `prompts/prompt.md`.

    Read on every request so the prompt can be edited without a restart — the
    prompt file, not this module, is where the assistant's behaviour is defined.
    """
    return PROMPT_PATH.read_text(encoding="utf-8")


def _customer_block(deps: ShopDeps) -> str:
    """Who the assistant is talking to."""
    customer = deps.customer
    if customer is None:
        return (
            "The customer is browsing as a guest and is not signed in. Do not ask for "
            "personal details. If they ask about an order or an account, say they would "
            "need to sign in, and that you cannot see account information either way."
        )
    name = " ".join(part for part in (customer.first_name, customer.last_name) if part)
    return (
        f"You are chatting with {name or customer.email}, a signed-in customer. "
        f"Their account email is {customer.email}. "
        "Greet them by first name when it is natural; do not repeat their email back to "
        "them, and never state it in an answer unless they ask what address is on their "
        "account. You can see these two fields and nothing else: you have no access to "
        "their orders, payment details, or password, and no tool that could reach them."
    )


def _page_block(deps: ShopDeps) -> str:
    """Where the customer is standing when they ask."""
    page = deps.page
    if page is None:
        return "You do not know which page the customer has open."

    if page.product_id:
        detail = load_product_detail(page.product_id)
        if detail is not None:
            return (
                f"The customer is looking at the product page for "
                f"\"{detail.name}\" (product_id: {detail.product_id}, ${detail.price:g}). "
                "If they say \"this\", \"it\", or \"that one\" with no product named, they "
                "mean this one. Call get_page_product to read its full details rather than "
                "working from this line."
            )

    if page.path.startswith("/products") and page.results_heading:
        return (
            f"The customer is looking at a results grid you produced, headed "
            f"\"{page.results_heading}\". A follow-up like \"the second one\" refers to that "
            "grid; ask which item they mean if it is ambiguous."
        )
    if page.path.startswith("/products"):
        return "The customer is browsing the full products grid."
    if page.path == "/":
        return "The customer is on the home page."
    if page.path.startswith("/about"):
        return "The customer is reading the About Us page."
    return f"The customer is on the page {page.path}."


def build_agent() -> Agent[ShopDeps, ChatReply]:
    """Assemble the agent.

    The static instructions come from `prompts/prompt.md`. Two dynamic blocks are
    appended per run from the dependencies: who is asking, and what page they
    have open. Keeping them in `instructions` rather than in the user's message
    means the transcript stays a clean record of what the customer actually said.
    """
    agent = Agent(
        _model(),
        deps_type=ShopDeps,
        instructions=system_prompt(),
        output_type=ChatReply,
        tools=AGENT_TOOLS,
    )

    @agent.instructions
    def conversation_context(ctx: RunContext[ShopDeps]) -> str:
        return "## This conversation\n\n" + _customer_block(ctx.deps) + "\n\n" + _page_block(ctx.deps)

    return agent


def _as_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Replay recent turns so the assistant can follow a conversation.

    Only the last few turns are kept, and assistant turns are replayed as plain
    text: the structured product ids from an earlier turn are not re-sent.
    """
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        content = turn.content.strip()
        if not content:
            continue
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif turn.role == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def _clip(value: object, limit: int) -> str:
    """One-line preview of a value, for the audit record."""
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            text = str(value)
    text = " ".join(_redact(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def _summarise_run(messages: list[ModelMessage]) -> tuple[list[AuditToolCall], int, str]:
    """Pull the tool calls, the model-request count, and a stop reason out of a run.

    Tool results arrive in a later message than the call that produced them, so
    they are stitched back together by `tool_call_id`.
    """
    calls: list[AuditToolCall] = []
    by_id: dict[str, AuditToolCall] = {}
    model_requests = 0
    finish_reason: str | None = None

    for message in messages:
        if isinstance(message, ModelResponse):
            model_requests += 1
            finish_reason = getattr(message, "finish_reason", None) or finish_reason
            for part in message.parts:
                if isinstance(part, BaseToolCallPart):
                    entry = AuditToolCall(
                        tool=part.tool_name, args=_clip(part.args_as_dict(), AUDIT_ARG_CHARS)
                    )
                    calls.append(entry)
                    by_id[part.tool_call_id] = entry
        elif isinstance(message, ModelRequest):
            for part in message.parts:
                entry = by_id.get(getattr(part, "tool_call_id", "") or "")
                if entry is None:
                    continue
                if isinstance(part, RetryPromptPart):
                    entry.error = _clip(part.content, AUDIT_RESULT_CHARS)
                elif isinstance(part, BaseToolReturnPart):
                    entry.result = _clip(part.content, AUDIT_RESULT_CHARS)

    if model_requests >= MAX_MODEL_REQUESTS:
        stop_reason = f"hit the model-request limit ({MAX_MODEL_REQUESTS})"
    else:
        stop_reason = f"final answer (finish_reason={finish_reason or 'stop'})"
    return calls, model_requests, stop_reason


def append_audit(entry: AuditEntry) -> None:
    """Append one record to output/audit_trail.json.

    Append-only by construction: the file is read, the new record is added to the
    end, and the whole list is written to a temporary file that then replaces the
    original. Nothing already in the file is ever modified or removed. A file that
    will not parse is moved aside rather than overwritten, so a corrupted run
    cannot destroy the history.
    """
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict] = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
            try:
                loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                rows = loaded if isinstance(loaded, list) else [loaded]
            except json.JSONDecodeError:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                AUDIT_PATH.replace(AUDIT_PATH.with_name(f"audit_trail.corrupt-{stamp}.json"))
                rows = []
        rows.append(entry.model_dump())
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(AUDIT_PATH)


def run_agent(
    message: str,
    history: list[ChatTurn] | None = None,
    deps: ShopDeps | None = None,
) -> tuple[ChatReply, list[str]]:
    """Answer one customer message, and append the turn to the audit trail.

    Returns the validated reply and the names of the tools the model called. A
    failure is returned as a polite reply rather than raised, so the chat panel
    always has something to show — and the failure is still audited.
    """
    deps = deps or ShopDeps()
    started = time.perf_counter()
    entry = AuditEntry(
        run_id=uuid.uuid4().hex[:12],
        time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        model=MODEL_NAME,
        status="ok",
        user_id=deps.customer.user_id if deps.customer else None,
        signed_in=deps.customer is not None,
        page_path=deps.page.path if deps.page else None,
        page_product_id=deps.page.product_id if deps.page else None,
        message=_clip(message, AUDIT_TEXT_CHARS),
        message_chars=len(message),
        history_turns=len(history or []),
    )

    try:
        agent = build_agent()
        result = agent.run_sync(
            message,
            deps=deps,
            message_history=_as_message_history(history or []),
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to the customer, not raised
        detail = f"{type(exc).__name__}: {_redact(str(exc))[:300]}"
        print(f"[chat] agent error: {detail}")
        entry.status = "error"
        entry.stop_reason = f"error: {detail}"
        entry.reply = FALLBACK_REPLY
        entry.duration_ms = int((time.perf_counter() - started) * 1000)
        append_audit(entry)
        return ChatReply(reply=FALLBACK_REPLY), []

    calls, model_requests, stop_reason = _summarise_run(result.new_messages())

    # `final_result` is PydanticAI's internal call that delivers the structured
    # output; it is not a shop tool, so it is left out of what we report.
    shop_calls = [c for c in calls if not c.tool.startswith("final_result")]
    tools_used = list(dict.fromkeys(c.tool for c in shop_calls))

    entry.tool_calls = shop_calls
    entry.tools_used = tools_used
    entry.model_requests = model_requests
    entry.referenced_product_ids = list(result.output.referenced_product_ids)
    entry.reply = _clip(result.output.reply, AUDIT_TEXT_CHARS)
    entry.stop_reason = stop_reason
    entry.duration_ms = int((time.perf_counter() - started) * 1000)
    append_audit(entry)

    return result.output, tools_used


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Do you have any navy hoodies in large?"
    reply, used = run_agent(question)
    print(f"Q: {question}\n")
    print(reply.reply)
    print(f"\nproducts referenced: {reply.referenced_product_ids}")
    print(f"tools used: {used}")
    print(f"audit appended to: {AUDIT_PATH}")
