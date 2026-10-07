"""Every Pydantic structured type used by the Campus Customs backend.

Grouped in one file so the shapes crossing a boundary — database row to API
response, tool result to model, model output to browser — are all visible
together. `main.py` imports the request and response models, `tools.py` returns
the catalogue models, and `agent.py` uses `ChatReply` as the agent's output type.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

MIN_PASSWORD_LENGTH = 8

# ----------------------------------------------------------------- catalogue


class SizeAvailability(BaseModel):
    """Stock for one product in one size."""

    size: str
    quantity: int
    status: str  # in_stock | low_stock | out_of_stock


class ProductSummary(BaseModel):
    """A product as it appears on a grid card."""

    product_id: str
    name: str
    garment_type: str
    category: str
    price: float
    short_description: str
    colors: list[str]
    image_url: str
    in_stock: bool


class ProductDetail(ProductSummary):
    """A product as it appears on its own page, with per-size stock."""

    description: str
    search_tags: list[str]
    sizes: list[SizeAvailability]
    available_sizes: list[str]
    total_quantity: int


# --------------------------------------------------------------------- users


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=200)
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def require_a_real_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Please enter a name.")
        return cleaned

    @model_validator(mode="after")
    def passwords_must_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("The two passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class PublicUser(BaseModel):
    """What the browser is allowed to know about the signed-in account.

    There is deliberately no password field. Even if a query were widened by
    mistake, a hash could not reach the browser through this model.
    """

    id: int
    first_name: str | None
    last_name: str | None
    email: str
    created_at: str


# --------------------------------------------------------- what tools return


class CatalogueMatch(BaseModel):
    """One product as the *model* sees it.

    Trimmed on purpose: enough to describe and recommend a product, small enough
    that a dozen matches do not flood the context window. The size list is
    included because stock is the fact the assistant is most likely to get wrong.
    """

    product_id: str
    name: str
    garment_type: str
    category: str
    price: float
    description: str
    colors: list[str]
    available_sizes: list[str]
    low_stock_sizes: list[str]
    sold_out_sizes: list[str]
    in_stock: bool


class CatalogueSearchResult(BaseModel):
    """What `search_catalogue` and `browse_category` hand back to the model."""

    query: str
    total_matches: int
    returned: int
    note: str = ""
    products: list[CatalogueMatch] = Field(default_factory=list)


class CategoryCount(BaseModel):
    """One shop category and how many products are in it."""

    category: str
    product_count: int
    in_stock_count: int
    price_from: float
    price_to: float


class CategoryList(BaseModel):
    """What `list_categories` hands back to the model."""

    total_products: int
    categories: list[CategoryCount] = Field(default_factory=list)


class ProductStock(BaseModel):
    """Every size's stock for one product, as `get_stock_by_size` returns it.

    One call covers the whole size run, so the assistant can answer "how many
    are left?" without six separate lookups — and cannot answer it for only the
    sizes it happened to ask about.
    """

    product_id: str
    name: str
    price: float
    in_stock: bool
    total_quantity: int
    sizes: list[SizeAvailability]
    available_sizes: list[str] = Field(default_factory=list)
    sold_out_sizes: list[str] = Field(default_factory=list)
    note: str = ""


class AvailabilityAnswer(BaseModel):
    """What `check_size_availability` hands back to the model."""

    product_id: str
    name: str
    size: str
    available: bool
    quantity: int
    status: str
    alternative_sizes: list[str] = Field(default_factory=list)
    note: str = ""


# ------------------------------------------------- who and where (agent deps)


class CustomerContext(BaseModel):
    """What the agent is told about the person it is chatting with.

    Populated only for a signed-in customer, from the account row. There is no
    password field and no tool that could reach one.
    """

    user_id: int
    first_name: str | None
    last_name: str | None
    email: str


class PageContext(BaseModel):
    """Where the customer is on the site when they send a message.

    `path` is the route; `product_id` is set only on a product page. The client
    sends an id, never product facts — the backend looks the product up itself,
    so a page claim cannot put a false price or name in front of the model.
    """

    path: str = Field(default="/", max_length=300)
    product_id: str | None = Field(default=None, max_length=120)
    results_heading: str | None = Field(default=None, max_length=60)


class ShopDeps(BaseModel):
    """Dependencies handed to one agent run: who is asking, and from where."""

    model_config = ConfigDict(frozen=True)

    customer: CustomerContext | None = None
    page: PageContext | None = None


# ---------------------------------------------------------------------- chat


class ProductCard(BaseModel):
    """A product the assistant referred to.

    Rendered twice from one payload: as a compact row inside the chat panel, and
    as a full card in the results grid on the page. Built by the backend from the
    database after the model answers, never from text the model wrote, so a card
    can never show a price, photo, or size the catalogue does not contain.
    """

    product_id: str
    name: str
    garment_type: str
    category: str = ""
    price: float
    image_url: str
    short_description: str
    in_stock: bool
    colors: list[str] = Field(default_factory=list)
    available_sizes: list[str] = Field(default_factory=list)
    sold_out_sizes: list[str] = Field(default_factory=list)


class ChatReply(BaseModel):
    """The agent's structured output.

    `referenced_product_ids` is the agent's claim about which catalogue products
    its answer is grounded in. The backend resolves those ids against the
    database to build the cards; any id that does not exist is dropped.
    """

    reply: str = Field(description="The answer to show the customer, in plain prose.")
    referenced_product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values returned by a tool that this answer is about. These become "
            "the product cards shown on the page, so include every product the customer "
            "should see, not only the ones named in the prose."
        ),
    )
    results_heading: str = Field(
        default="",
        description=(
            "A short heading for the results grid, three or four words, e.g. "
            "'Quarter-zip pullovers' or 'Navy hoodies under $70'. Empty when the answer "
            "shows no products."
        ),
        max_length=60,
    )


class ChatTurn(BaseModel):
    """One earlier message, replayed so the assistant can follow a conversation."""

    role: str  # user | assistant
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)
    page: PageContext | None = None


class StoredChatMessage(BaseModel):
    """One row of `chat_messages`, as the browser receives it on sign-in."""

    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[StoredChatMessage] = Field(default_factory=list)


class AuditToolCall(BaseModel):
    """One tool call inside an agent loop, as written to the audit trail.

    Arguments and results are stored as short previews rather than in full: the
    point of the record is to show *what the agent did*, and a complete tool
    result would bloat the file and copy catalogue text that is already in the
    database.
    """

    tool: str
    args: str = ""
    result: str = ""
    error: str | None = None


class AuditEntry(BaseModel):
    """One turn of the agent loop, appended to output/audit_trail.json.

    Deliberately excludes the customer's email, the session cookie, the API key,
    and any password: an audit record has to be safe to read.
    """

    run_id: str
    time: str
    model: str
    status: str  # ok | error
    user_id: int | None = None
    signed_in: bool = False
    page_path: str | None = None
    page_product_id: str | None = None
    message: str = Field(description="The customer's message, clipped.")
    message_chars: int = 0
    history_turns: int = 0
    tool_calls: list[AuditToolCall] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    model_requests: int = 0
    referenced_product_ids: list[str] = Field(default_factory=list)
    reply: str = Field(default="", description="The assistant's reply, clipped.")
    stop_reason: str = ""
    duration_ms: int = 0


class ChatResponse(BaseModel):
    """What the chat widget receives.

    `products` drives both renderings: the compact rows under the reply in the
    chat panel, and the results grid the page switches to. `results_heading`
    captions that grid.
    """

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    results_heading: str = ""
    tools_used: list[str] = Field(default_factory=list)
