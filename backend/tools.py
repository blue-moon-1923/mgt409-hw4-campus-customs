"""Catalogue data access, and the three tools the chat agent is allowed to call.

Two things live here:

1. Plain helpers (`connect_ro`, `load_product_summaries`, ...) shared by the REST
   endpoints in `main.py`.
2. The agent-facing tools at the bottom of the file — `search_catalogue`,
   `get_product_details`, and `check_size_availability` — which are the *only*
   functions `agent.py` hands to the model.

Every read here opens SQLite read-only and touches `catalogue` and `inventory`
only. The `users` table is never queried from this module, so the agent has no
route to an email address or a password hash.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import ModelRetry, RunContext

from models import (
    CategoryCount,
    CategoryList,
    AvailabilityAnswer,
    CatalogueMatch,
    CatalogueSearchResult,
    ProductDetail,
    ProductStock,
    ProductSummary,
    ShopDeps,
    SizeAvailability,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
IMAGE_DIR = ROOT / "data" / "products"

# The catalogue stocks exactly these six sizes for every product.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_AT = 3

MAX_SEARCH_RESULTS = 8
CARD_DESCRIPTION_CHARS = 120
TOOL_DESCRIPTION_CHARS = 240

# `garment_type` is not a clean category field: the catalogue files one hoodie
# under five different labels ("hoodie", "pullover hoodie", "hooded sweatshirt",
# "hooded pullover sweatshirt", "full-zip hooded sweatshirt"). Matching a
# customer's word against these groups, rather than against the column directly,
# is what stops a search for "hoodie" from missing most of the hoodies.
SYNONYMS: dict[str, set[str]] = {
    "hoodie": {"hoodie", "hooded", "hood", "pullover"},
    "hooded": {"hoodie", "hooded", "hood"},
    "sweatshirt": {"sweatshirt", "crewneck", "crew", "fleece"},
    "crewneck": {"crewneck", "crew", "sweatshirt"},
    "tshirt": {"tshirt", "tee", "t", "shirt"},
    "tee": {"tshirt", "tee", "shirt"},
    "shirt": {"shirt", "tshirt", "tee"},
    "jacket": {"jacket", "bomber", "fleece", "zip"},
    "fleece": {"fleece", "jacket", "sweater"},
    "quarterzip": {"quarter", "zip", "14"},
    "zip": {"zip", "zipper", "quarter", "full"},
    "sweater": {"sweater", "fleece"},
    "longsleeve": {"long", "sleeve", "longsleeve"},
}

# Words that carry no signal in a shop query.
STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "but", "by", "can", "do", "does",
    "for", "from", "get", "give", "got", "has", "have", "i", "in", "is", "it", "its",
    "like", "looking", "me", "my", "need", "of", "on", "or", "please", "see", "show",
    "some", "something", "that", "the", "them", "there", "they", "this", "to", "want",
    "was", "we", "what", "which", "with", "would", "you", "your", "do", "u", "got",
}


# `garment_type` holds 22 labels for about six kinds of garment (see harness §1.5).
# Folding them into real categories here, once, is what lets the products filter and
# the browse tool agree with each other instead of each inventing its own grouping.
#
# These are regular expressions with word boundaries, not substring tests, because
# substrings get this badly wrong: "sweatshirt" contains "tshirt", so a naive match
# filed every crewneck sweatshirt under T-Shirts.
#
# Order matters: "short-sleeve crew-neck t-shirt" is a T-shirt, not a crewneck, and
# "full-zip hooded sweatshirt" is a hoodie, not a jacket.
CATEGORY_RULES: list[tuple[str, str]] = [
    ("Hoodies", r"\bhood"),
    ("Quarter-Zips", r"quarter[\s-]?zip|1/4[\s-]?zip"),
    ("T-Shirts", r"\bt[\s-]?shirts?\b|\btees?\b"),
    ("Long Sleeves", r"long[\s-]?sleeve"),
    ("Crewnecks", r"crew[\s-]?necks?\b|mock[\s-]?necks?\b|\bsweatshirts?\b|\bsweaters?\b"),
    ("Jackets & Fleece", r"\bjackets?\b|\bfleece\b"),
]
CATEGORY_ORDER = [name for name, _ in CATEGORY_RULES] + ["Other"]


def category_for(garment_type: str) -> str:
    """Fold a raw `garment_type` label into one of the shop's real categories."""
    label = garment_type.lower()
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, label):
            return category
    return "Other"


def _category_tokens(text: str) -> set[str]:
    """Singular word stems, so "crewneck" matches the category "Crewnecks"."""
    return {token.rstrip("s") or token for token in _normalise(text)}


def resolve_category(text: str) -> str | None:
    """Match a customer's word for a category to the shop's name for it."""
    wanted = _category_tokens(text)
    return next(
        (name for name in CATEGORY_ORDER if _category_tokens(name) & wanted),
        None,
    )


@dataclass(frozen=True)
class CatalogueSnapshot:
    """The whole catalogue and its stock, read in two queries and reused.

    Before this, one `search_catalogue` call issued 104 SQLite statements: two for
    the catalogue and the totals, then one more per product for its size rows. The
    sizes are now loaded in a single grouped query and bucketed in Python, and the
    whole snapshot is cached until the database file changes.
    """

    rows: tuple[sqlite3.Row, ...]
    sizes: dict[str, list[SizeAvailability]]
    totals: dict[str, int]


_snapshot_cache: tuple[float, CatalogueSnapshot] | None = None


def _load_snapshot() -> CatalogueSnapshot:
    with connect_ro() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        # One query for all 612 inventory rows, instead of one query per product.
        inventory = conn.execute(
            "SELECT product_id, size, quantity FROM inventory"
        ).fetchall()

    buckets: dict[str, dict[str, int]] = {}
    for row in inventory:
        buckets.setdefault(row["product_id"], {})[row["size"]] = row["quantity"]

    sizes: dict[str, list[SizeAvailability]] = {}
    totals: dict[str, int] = {}
    for product_id, quantities in buckets.items():
        ordered = SIZE_ORDER + sorted(set(quantities) - set(SIZE_ORDER))
        sizes[product_id] = [
            SizeAvailability(
                size=size, quantity=quantities[size], status=stock_status(quantities[size])
            )
            for size in ordered
            if size in quantities
        ]
        totals[product_id] = sum(quantities.values())

    return CatalogueSnapshot(rows=tuple(rows), sizes=sizes, totals=totals)


def catalogue_snapshot() -> CatalogueSnapshot:
    """The cached catalogue, reloaded when the database file changes on disk."""
    global _snapshot_cache
    stamp = DB_PATH.stat().st_mtime if DB_PATH.exists() else 0.0
    if _snapshot_cache is None or _snapshot_cache[0] != stamp:
        _snapshot_cache = (stamp, _load_snapshot())
    return _snapshot_cache[1]


# ------------------------------------------------------------- shared helpers


def connect_ro() -> sqlite3.Connection:
    """Open the catalogue read-only, so no read path can modify course data."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Catalogue database is missing: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def parse_json_list(raw: str) -> list[str]:
    """`colors` and `search_tags` are JSON arrays stored in TEXT columns."""
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def short_description(description: str, limit: int = CARD_DESCRIPTION_CHARS) -> str:
    """First sentence of the description, for a product card."""
    head = description.strip().split(". ")[0].rstrip(".")
    if len(head) > limit:
        return clip(head, limit)
    return head + "." if head else head


def stock_status(quantity: int) -> str:
    if quantity <= 0:
        return "out_of_stock"
    if quantity <= LOW_STOCK_AT:
        return "low_stock"
    return "in_stock"


def image_url(image_file_path: str) -> str:
    """Map `products/foo.jpg` in the database to the mounted `/images/foo.jpg`."""
    return f"/images/{Path(image_file_path).name}"


def _summary(row: sqlite3.Row, in_stock: bool) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        category=category_for(row["garment_type"]),
        price=row["price"],
        short_description=short_description(row["description"]),
        colors=parse_json_list(row["colors"]),
        image_url=image_url(row["image_file_path"]),
        in_stock=in_stock,
    )


def _sizes_for(conn: sqlite3.Connection, product_id: str) -> list[SizeAvailability]:
    quantities = {
        row["size"]: row["quantity"]
        for row in conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        )
    }
    ordered = SIZE_ORDER + sorted(set(quantities) - set(SIZE_ORDER))
    return [
        SizeAvailability(
            size=size, quantity=quantities[size], status=stock_status(quantities[size])
        )
        for size in ordered
        if size in quantities
    ]


def load_product_summaries() -> list[ProductSummary]:
    """Every product, ordered by name, for the products grid."""
    snapshot = catalogue_snapshot()
    return [
        _summary(row, snapshot.totals.get(row["product_id"], 0) > 0) for row in snapshot.rows
    ]


def load_product_detail(product_id: str) -> ProductDetail | None:
    """One product with per-size stock, or None when the id is unknown."""
    snapshot = catalogue_snapshot()
    row = next((r for r in snapshot.rows if r["product_id"] == product_id), None)
    if row is None:
        return None
    sizes = snapshot.sizes.get(product_id, [])

    total = sum(size.quantity for size in sizes)
    return ProductDetail(
        **_summary(row, total > 0).model_dump(),
        description=row["description"],
        search_tags=parse_json_list(row["search_tags"]),
        sizes=sizes,
        available_sizes=[s.size for s in sizes if s.quantity > 0],
        total_quantity=total,
    )


# --------------------------------------------------------------- text matching


def _match(row: sqlite3.Row) -> CatalogueMatch:
    """One product as the model sees it."""
    snapshot = catalogue_snapshot()
    sizes = snapshot.sizes.get(row["product_id"], [])
    return CatalogueMatch(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        category=category_for(row["garment_type"]),
        price=row["price"],
        description=clip(row["description"], TOOL_DESCRIPTION_CHARS),
        colors=parse_json_list(row["colors"]),
        available_sizes=[s.size for s in sizes if s.quantity > 0],
        low_stock_sizes=[s.size for s in sizes if s.status == "low_stock"],
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
        in_stock=snapshot.totals.get(row["product_id"], 0) > 0,
    )


def _normalise(text: str) -> list[str]:
    """Lower-case and split on anything that is not a letter or digit.

    This is what lets "t-shirt", "t shirt", and "tshirt" all reduce to the same
    tokens, and it strips the punctuation that varies across catalogue labels.
    """
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def _expand(tokens: list[str]) -> set[str]:
    expanded: set[str] = set()
    for token in tokens:
        expanded.add(token)
        expanded |= SYNONYMS.get(token, set())
    return expanded


def _haystack(row: sqlite3.Row) -> set[str]:
    """All the words that describe one product.

    `search_tags` and `description` do the real work here; `garment_type` is
    included but never relied on alone, because its values are inconsistent.
    """
    parts = [
        row["name"],
        row["garment_type"],
        row["description"],
        " ".join(parse_json_list(row["colors"])),
        " ".join(parse_json_list(row["search_tags"])),
    ]
    return set(_normalise(" ".join(parts)))


# ------------------------------------------------------------- agent tools


def search_catalogue(
    query: str, max_price: float | None = None, in_stock_only: bool = False
) -> CatalogueSearchResult:
    """Search the Campus Customs catalogue for products matching a customer's words.

    Searches product names, descriptions, colours, and search tags together, so
    everyday phrasing like "warm navy hoodie" or "something for the Harvard game"
    finds the right items. Returns at most 8 products, best match first, each with
    its price and which sizes are in stock.

    Args:
        query: What the customer is looking for, in their own words.
        max_price: Optional ceiling in US dollars.
        in_stock_only: Set true to drop products with no stock in any size.
    """
    tokens = [token for token in _normalise(query) if token not in STOPWORDS]
    wanted = _expand(tokens)

    snapshot = catalogue_snapshot()
    stock = snapshot.totals
    sizes_by_product = snapshot.sizes

    scored: list[tuple[int, sqlite3.Row]] = []
    for row in snapshot.rows:
        if max_price is not None and row["price"] > max_price:
            continue
        if in_stock_only and stock.get(row["product_id"], 0) <= 0:
            continue
        score = len(wanted & _haystack(row)) if wanted else 1
        if score:
            scored.append((score, row))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    selected = scored[:MAX_SEARCH_RESULTS]

    products = [_match(row) for _, row in selected]

    note = ""
    if not products:
        note = "No products matched. Try broader words, or tell the customer we do not carry it."
    elif len(scored) > len(selected):
        note = f"Showing the {len(selected)} closest of {len(scored)} matches."

    return CatalogueSearchResult(
        query=query,
        total_matches=len(scored),
        returned=len(products),
        note=note,
        products=products,
    )


def _require_product(product_id: str) -> ProductDetail:
    """Load one product, or send the model back to search instead of guessing."""
    detail = load_product_detail(product_id)
    if detail is None:
        raise ModelRetry(
            f"There is no product with product_id {product_id!r}. "
            "Call search_catalogue first and use a product_id from its results."
        )
    return detail


def get_product_details(product_id: str) -> ProductDetail:
    """Look up one product by its exact product_id, with the full description and
    every size's stock level.

    Use this after `search_catalogue` when a customer asks about one specific item.

    Args:
        product_id: A product_id returned by `search_catalogue`.
    """
    detail = load_product_detail(product_id)
    if detail is None:
        raise ModelRetry(
            f"There is no product with product_id {product_id!r}. "
            "Call search_catalogue first and use a product_id from its results."
        )
    return detail


def get_stock_by_size(product_id: str) -> ProductStock:
    """Report how many units of one product are on hand in every size.

    Use this for any "how many are left", "what sizes do you have", or "is it
    running low" question. It returns the whole size run in one call — XS through
    XXL with an exact count for each — so the answer cannot accidentally cover
    only some sizes. Quantities come straight from the inventory table.

    Args:
        product_id: A product_id returned by `search_catalogue`.
    """
    detail = _require_product(product_id)
    sold_out = [s.size for s in detail.sizes if s.quantity == 0]

    note = ""
    if detail.total_quantity == 0:
        note = "Every size is sold out. Say so plainly."
    elif sold_out:
        note = "Sold out in " + ", ".join(sold_out) + ". Lead with that before the rest."

    return ProductStock(
        product_id=detail.product_id,
        name=detail.name,
        price=detail.price,
        in_stock=detail.total_quantity > 0,
        total_quantity=detail.total_quantity,
        sizes=detail.sizes,
        available_sizes=detail.available_sizes,
        sold_out_sizes=sold_out,
        note=note,
    )


def check_size_availability(product_id: str, size: str) -> AvailabilityAnswer:
    """Check whether one product is in stock in one size right now.

    Use this whenever a customer asks about a specific size. Never answer a size
    question from a description — the stock number is the only reliable source.

    Args:
        product_id: A product_id returned by `search_catalogue`.
        size: One of XS, S, M, L, XL, XXL (case-insensitive).
    """
    detail = _require_product(product_id)
    requested = size.strip().upper()
    match = next((s for s in detail.sizes if s.size == requested), None)
    if match is None:
        return AvailabilityAnswer(
            product_id=detail.product_id,
            name=detail.name,
            size=requested,
            available=False,
            quantity=0,
            status="unknown_size",
            alternative_sizes=detail.available_sizes,
            note=f"We do not cut this item in {requested}. Stocked sizes: "
            + ", ".join(s.size for s in detail.sizes),
        )

    return AvailabilityAnswer(
        product_id=detail.product_id,
        name=detail.name,
        size=match.size,
        available=match.quantity > 0,
        quantity=match.quantity,
        status=match.status,
        alternative_sizes=[s for s in detail.available_sizes if s != match.size],
    )


def list_categories() -> CategoryList:
    """List the kinds of clothing the shop sells, with how many of each.

    Call this for "what do you sell?", "what kinds of things do you have?", or when
    a customer is not sure what they are looking for. Returns the real categories
    with product counts and price ranges, so you never have to guess at the shape
    of the catalogue.
    """
    snapshot = catalogue_snapshot()
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in snapshot.rows:
        grouped.setdefault(category_for(row["garment_type"]), []).append(row)

    counts = [
        CategoryCount(
            category=category,
            product_count=len(rows),
            in_stock_count=sum(1 for r in rows if snapshot.totals.get(r["product_id"], 0) > 0),
            price_from=min(r["price"] for r in rows),
            price_to=max(r["price"] for r in rows),
        )
        for category in CATEGORY_ORDER
        if (rows := grouped.get(category))
    ]
    return CategoryList(total_products=len(snapshot.rows), categories=counts)


def browse_category(
    category: str, max_price: float | None = None, in_stock_only: bool = False
) -> CatalogueSearchResult:
    """List every product in one category, not just the closest matches.

    Use this for browse questions — "what t-shirts do you sell?", "show me all the
    hoodies" — where the customer wants to see the range rather than a best guess.
    Unlike `search_catalogue`, this returns the complete list and a true total, so
    you can tell the customer how many there really are.

    Args:
        category: One of the categories from `list_categories`, e.g. "Hoodies",
            "T-Shirts", "Crewnecks", "Quarter-Zips", "Long Sleeves",
            "Jackets & Fleece". Matched loosely, so "hoodie" also works.
        max_price: Optional ceiling in US dollars.
        in_stock_only: Set true to drop products with no stock in any size.
    """
    snapshot = catalogue_snapshot()
    resolved = resolve_category(category)
    if resolved is None:
        available = ", ".join(c.category for c in list_categories().categories)
        raise ModelRetry(
            f"{category!r} is not one of the shop's categories. Pick one of: {available}. "
            "For anything else, use search_catalogue."
        )

    rows = [row for row in snapshot.rows if category_for(row["garment_type"]) == resolved]
    if max_price is not None:
        rows = [row for row in rows if row["price"] <= max_price]
    if in_stock_only:
        rows = [row for row in rows if snapshot.totals.get(row["product_id"], 0) > 0]

    note = (
        f"This is the complete {resolved} list: {len(rows)} products. "
        "Tell the customer the total; do not imply there are more."
        if rows
        else f"No {resolved} match those filters."
    )
    return CatalogueSearchResult(
        query=f"category: {resolved}",
        total_matches=len(rows),
        returned=len(rows),
        note=note,
        products=[_match(row) for row in rows],
    )


def related_products(product_id: str, limit: int = 4) -> list[ProductSummary]:
    """Other products in the same category, ranked by shared search tags.

    Not an agent tool — this backs the "More like this" row on a product page.
    """
    snapshot = catalogue_snapshot()
    row = next((r for r in snapshot.rows if r["product_id"] == product_id), None)
    if row is None:
        return []

    category = category_for(row["garment_type"])
    tags = set(_normalise(" ".join(parse_json_list(row["search_tags"]))))

    scored: list[tuple[int, sqlite3.Row]] = []
    for other in snapshot.rows:
        if other["product_id"] == product_id:
            continue
        if category_for(other["garment_type"]) != category:
            continue
        shared = len(tags & set(_normalise(" ".join(parse_json_list(other["search_tags"])))))
        in_stock = snapshot.totals.get(other["product_id"], 0) > 0
        # In-stock items rank above sold-out ones at the same tag overlap.
        scored.append((shared * 2 + (1 if in_stock else 0), other))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return [
        _summary(other, snapshot.totals.get(other["product_id"], 0) > 0)
        for _, other in scored[:limit]
    ]


def get_page_product(ctx: RunContext[ShopDeps]) -> ProductDetail:
    """Look up the product the customer is currently looking at on the website.

    Call this whenever the customer says "this", "it", "that one", or asks a
    follow-up with no product named — "do you have this in another colour?",
    "what sizes does it come in?". It resolves what they are pointing at from the
    page they have open, so you never have to guess which product they mean.

    Fails if they are not on a product page; search instead in that case.
    """
    page = ctx.deps.page
    if page is None or not page.product_id:
        raise ModelRetry(
            "The customer is not on a product page, so there is no 'this' to resolve. "
            "Ask which product they mean, or use search_catalogue."
        )
    detail = load_product_detail(page.product_id)
    if detail is None:
        raise ModelRetry(
            "The page refers to a product that is not in the catalogue. Use search_catalogue."
        )
    return detail


AGENT_TOOLS = [
    list_categories,
    browse_category,
    search_catalogue,
    get_product_details,
    get_stock_by_size,
    check_size_availability,
    get_page_product,
]
