# Usability improvements — Homework 4, Problem 9

Four changes to the working shop: two on the front end, two behind it. Each entry says what
was built, why it helps the customer or the business, and how to see it running. Measured
results were filled in after the work, against the live app.

Written before the work started, then completed with the numbers.

---

## Front end 1 — Find something among 102 products

### The problem

The Products page listed all 102 items in one grid with no search, no filter, and no sort.
A customer who wanted a navy crewneck under $60 had to scroll the whole catalogue and read
every card. The only way to narrow anything down was to ask the chat assistant, which is a
lot to demand of someone who just wants to browse.

The underlying catalogue data made this worse. `garment_type` holds **22 different labels**
for about six kinds of garment — `hoodie`, `pullover hoodie`, `hooded sweatshirt`,
`hooded pullover sweatshirt`, and `full-zip hooded sweatshirt` all mean hoodie — so a naive
category dropdown built from that column would have offered 22 confusing options, most with
two or three items in them.

### What was built

A toolbar above the grid:

- **Search box** — matches name, description, colours, and tags as you type.
- **Category filter** — built on a normalised map, so one "Hoodies" option covers all five
  of the labels above. Each option shows its count.
- **Sort** — name, price low to high, price high to low.
- **In stock only** toggle.
- A live result count, a **Clear** button, and a proper empty state when nothing matches.

### Why it helps

The customer can answer their own question in two clicks instead of scrolling 102 cards or
opening a chat. For the business, the categories are finally usable: the dirty column is
normalised in one place rather than being worked around in each feature.

### How to see it

Open **Products**. Type "navy" in the search box, pick **Crewnecks**, sort by price.

---

## Front end 2 — Somewhere to go from a product page

### The problem

The product page was a dead end. After looking at one crewneck the only ways forward were
the browser back button or the full 102-item grid. A customer comparing two similar items
had to re-find the second one each time.

### What was built

A **"More like this"** row at the bottom of every product page: up to four other products in
the same normalised category, ranked by shared search tags, each a normal product card that
opens its own page.

### Why it helps

It keeps a browsing customer moving instead of dead-ending them, which is the single most
common reason someone leaves a shop page. It also surfaces the long tail of the catalogue —
residential-college and team variants that are hard to find any other way.

### How to see it

Open any product, for example **Grace Hopper College Crewneck**, and scroll to the bottom.

---

## Back end 1 — Stop running 104 queries per search

### The problem

`search_catalogue` is the tool the agent calls on almost every turn. Measured on the live
code, one call issued **104 SQLite statements**: two to load the catalogue and the stock
totals, then **one more per product** to fetch its size rows. A textbook N+1.

### What was built

- The per-product size loop was replaced with **one grouped query** that reads all 612
  inventory rows at once and buckets them in Python.
- A small in-process **catalogue cache**, invalidated by the database file's modification
  time, so repeated reads within a session skip SQLite entirely while still noticing a
  changed file.

### Why it helps

Faster replies for the customer, and cheaper and more scalable for the business: the saving
grows with the catalogue, and the same fix removes 100 round trips per search if the
database ever moves off the local disk.

### How to see it

`python perf_check.py` in `backend/` prints the statement count and timing for a search.

### Measured result

Counted with `backend/perf_check.py`, which traces every SQLite statement:

| | Before | After (cold) | After (cached) |
| --- | --- | --- | --- |
| SQL statements per search | **104** | **2** | **0** |
| Time per search | 9.2 ms | 5.6 ms | **1.4 ms** |

**52× fewer queries on a cold read, and 6.6× faster once warm.** Every other catalogue
read is now 2 statements cold and 0 warm as well.

---

## Back end 2 — Answer "what t-shirts do you sell?" completely

### The problem

Every catalogue question went through `search_catalogue`, which returns the **8 best
matches**. For a specific request that is right. For a browse question — "what t-shirts do
you sell?" — it is misleading: the shop has far more than eight, and the assistant could
only show a sample while sounding like it had answered.

### What was built

- A shared **category map** that folds the 22 `garment_type` labels into six real
  categories, used by both the agent and the Products page filter.
- A new tool, **`browse_category(category, max_price, in_stock_only)`**, that returns the
  **complete** list for a category with a true total, rather than a relevance-ranked sample.
- A **`list_categories()`** tool so the assistant can answer "what do you sell?" with the
  real categories and counts instead of guessing.
- `prompts/prompt.md` now routes browse questions to `browse_category` and specific requests
  to `search_catalogue`.

### Why it helps

More accurate answers: the assistant can say how many of something the shop actually has,
and show them all. For the business it also means fewer follow-up turns — the customer is
not asking "is that all of them?" — which is cheaper per conversation.

### Measured result

| Question | Before | After |
| --- | --- | --- |
| "What t-shirts do you sell?" | 8 cards from `search_catalogue`, no total | **25 cards** from `browse_category`, and the reply opens *"We have 25 T-shirts, all priced at $32."* |
| "What kinds of things do you sell?" | A guess from one search | *"Hoodies (27), Quarter-Zips (11), T-Shirts (25), Long Sleeves (2), Crewnecks (29), Jackets & Fleece (8) … prices run from $32 up to $98."* All six counts verified against the database. |

### A bug this caught

The first version of the category map used substring tests. `"sweatshirt"` contains
`"tshirt"`, so **every crewneck sweatshirt was filed under T-Shirts** — 53 T-shirts and 1
crewneck, and the assistant would have told customers t-shirts cost "$32 to $58".

The rules were rewritten as regular expressions with word boundaries. The real split is 25
T-Shirts and 29 Crewnecks, and all 25 T-shirts are genuinely $32. A category error had
become a pricing error, which is the kind of thing a customer would notice before anyone
internally did.


---

## Verification

Everything below was exercised in the running app, not just in code.

### Front end 1 — toolbar

- Products page shows **"102 designs"** with search, category, sort, and an in-stock toggle.
- Typing `navy`, choosing **Crewnecks (29)**, and sorting by price gave **"23 of 102"**,
  cards starting at $58, with a **Clear** button appearing.
- A nonsense search gave 0 cards and the empty state *"Nothing matches those filters. Try
  fewer words, or clear the filters."*
- Clicking that inline **clear the filters** link restored **102 designs**.
- Category counts come from the normalised map, so the dropdown offers six options rather
  than the 22 raw `garment_type` labels.

### Front end 2 — More like this

- `/products/grace-hopper-college-crewneck` renders a **"More crewnecks"** row with four
  cards: Davenport, Lacrosse Left Chest, Pierson, Saybrook College Crewneck.
- Each links to its own product page (`/products/davenport-college-crewneck`, etc.) and
  opens the full detail view, so the behaviour built in Problem 3 is unchanged.
- The row is hidden when there is nothing to show, and a failed request leaves the rest of
  the page working.

### Back end 1 — performance

- `python perf_check.py` reports **2 statements cold, 0 warm** for every catalogue read.
- The cache keys on the database file's modification time, so editing the database is picked
  up on the next read rather than needing a restart.

### Back end 2 — categories

- `GET /api/products` now carries a `category` on every product. Counts:
  Crewnecks 29, Hoodies 27, T-Shirts 25, Quarter-Zips 11, Jackets & Fleece 8,
  Long Sleeves 2 — **102 total**.
- All 22 raw `garment_type` labels were checked one by one against the map; each lands in
  the right category, including the two awkward ones: `short-sleeve crew-neck t-shirt` is a
  T-shirt, and `full-zip hooded sweatshirt` is a hoodie.
- `browse_category("hats")` raises `ModelRetry` listing the real categories, so the agent
  asks again rather than inventing a category.
- The agent used `browse_category` for the browse question and `list_categories` for the
  "what do you sell?" question — confirmed in `tools_used` on both replies.

### Regression

- Sign-in, chat history, page context, and chat-driven page results all still work.
- `npm run build` passes type-checking and bundles cleanly.
