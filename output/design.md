# Design — Campus Customs storefront

What changed in Problem 10, and why each change should keep someone on the site long enough
to buy something.

Note on reference: the only site given in this assignment was the one named in Problem 3,
used for the *concepts* behind the Home and About copy. Nothing here is copied from it. The
look below is built from the shop's own catalogue — Yale navy, residential-college crests,
and the colours already recorded in the data.

---

## Type

**Fraunces** (display serif) for headings, **Inter** for everything else, loaded from Google
Fonts with full system fallbacks. Fraunces is a variable face with `SOFT` and `WONK` axes;
set warm and slightly wonky, it reads like a shop with a history rather than another
start-up grotesk. Inter keeps the interface — labels, buttons, forms — crisp and neutral.

The hero headline uses Fraunces at 900 with tight negative tracking, and one italic word in
brass. One accented word gives the sentence a focal point without a second typeface.

**Why it helps:** a distinctive face is the cheapest trust signal a small shop has. The
pairing says "real store", and the heading/label contrast makes the page scannable instead
of uniform.

## Hero photograph

The hero now sits on a real campus photograph — Harkness Tower seen through the trees —
rather than a patterned navy field.

- **Image:** “Harkness Tower Canopy” by **Carol M. Highsmith**, from her Library of Congress
  collection, which is **dedicated to the public domain**. Downloaded from Wikimedia Commons,
  resized to 1920 px and compressed to 568 KB, stored at
  `frontend/public/yale-campus-hero.jpg`. Credited in the site footer.
- **Legibility was measured, not eyeballed.** The raw photo is unusable behind white text on
  its own: bright sky gaps in the headline area give white only **1.65:1**. A navy scrim sits
  over it, heaviest on the left where the text is and lifting past the content so the trees
  and tower stay visible. Sampled against the brightest pixels in each band:

  | Zone | White text | Small stat labels |
  | --- | --- | --- |
  | Headline and lede (left 55%) | **12.6:1** | 9.8:1 |
  | Middle of the stats row | 9.6:1 | 7.5:1 |
  | Right end of the stats row | 6.7:1 | 5.2:1 |

  All well above the 4.5:1 AA threshold. `background-color: var(--navy-deep)` stays behind the
  image, so the hero still reads correctly if the photograph fails to load.
- On a phone the headline covers most of the frame, so the crop shifts toward the tower and
  the gradient flattens into an even, heavier wash.

**Why it helps:** a real place does what a pattern cannot — it tells a visitor in one glance
that this is a New Haven shop selling Yale clothing, not a generic merch site.

## Colour

Yale navy on **warm bone** (`#faf8f4`) rather than pure white, white reserved for cards, and
a **brass** accent (`#8a6a2f`) for eyebrows, rules, and small labels.

**Why it helps:** bone makes the product photography — mostly navy and grey garments on
white — sit forward instead of dissolving into the page. Brass gives the eye somewhere to
land on every section without competing with the price.

Every text pair was measured. Body 17.0:1, headings 15.1:1, brass labels 4.7:1, muted text
5.5:1, white on navy 12.2:1 — all above the 4.5:1 AA threshold.

## Hierarchy

- A **thin announcement bar** above the masthead: free campus pickup, printed in New Haven,
  XS–XXL on every design. On a phone it collapses to the one that changes a buying decision.
- A **shield monogram** replaces the text logo — fitting for a shop that prints crests.
- Every section opens with a brass **eyebrow with a rule**, then the heading. Repeated
  rhythm means a customer always knows where they are.
- The hero closes with four **stat blocks** — 102 designs, XS–XXL, 14 residential colleges,
  and one unbeatable bulldog — answering "is this shop big enough to have my thing?" before
  any scrolling, with a joke at the end so it reads like a shop rather than a spec sheet.
- The hero is **deliberately short**. Its padding, the stat spacing, and the first section's
  top padding were all trimmed until the category names — Hoodies & Crewnecks, Tees & Long
  Sleeves, Residential Colleges — clear the fold on a 768 px-tall window. A visitor should be
  able to see what the shop sells without scrolling.

## Motion

All of it is additive, and all of it is switched off under `prefers-reduced-motion`.

- Grid cards **rise in with a 45 ms stagger**, so a grid assembles instead of appearing.
- Sections **reveal on scroll** via `IntersectionObserver`. Content is visible by default and
  only hidden once the observer is confirmed, so a failure can never blank the page.
- Product images **zoom gently on hover**; cards lift and the border turns navy.
- Nav links grow a brass underline from the left.
- Chat bubbles **animate in individually**; the thinking state is three blinking dots.

**Why it helps:** motion here is feedback, not decoration — it confirms a hover is a target,
that a reply is coming, and that more page exists below the fold.

## Product presentation

- The **price sits on the photograph** as a navy chip. It is the second thing a shopper looks
  for, and it no longer moves around with the length of the description.
- **Colour swatches**, generated from the catalogue's own `colors` field. 22 colour names are
  mapped to real values; an unmapped name falls back to a labelled chip, so a new colour
  never renders as a mystery dot. Shoppers scan for colour before they read.
- Sold-out items get a **full-image veil** with a centred badge rather than a corner sticker —
  honest at a glance, and it stops a customer falling for something they cannot buy.
- Descriptions are clamped to three lines, so cards align no matter how long the copy is.
- The detail page shows the photograph on a soft gradient panel that **sticks while the
  right column scrolls**, and large swatches sit beside the colour names.

## Chat feel

- Header is a navy gradient with the **shield as the assistant's avatar** and a live green
  status dot — it reads as part of the shop, not a bolted-on widget.
- **Three suggestion chips** appear on a fresh conversation ("What hoodies do you sell?",
  "Something navy under $60", "Do you have XL crewnecks?"). An empty box gets ignored; an
  example gets clicked.
- **Typing dots** while the agent works, replacing a line of static text.
- A **pulsing brass dot** on the closed button when a reply arrives while the panel is shut.
- The input **focuses on open**, and **Escape closes** the panel.

**Why it helps:** the assistant is the feature that separates this shop from a static
catalogue, and nobody used it while it looked like a support widget. Suggestions make its
job legible in one glance, and the small affordances make it feel answered-by-a-person.

---

## Verified in the running app

- Fonts load: `document.fonts.check` returns true for both; `h1` computes to Fraunces, body
  to Inter.
- Announcement bar, shield, brass nav underline, and the stat row all render; on a 375 px
  viewport the bar collapses to one claim and the toolbar goes full width.
- Product cards show the price chip and real colour swatches (navy `rgb(28,42,74)`, white).
- Detail page renders large swatches beside the colour names.
- Chat panel shows the avatar, status dot, and — on a fresh conversation — the three chips.
- Contrast ratios measured in the browser; every text pair is above AA.
- No console warnings or errors beyond the expected `401` from "who am I" when signed out.
