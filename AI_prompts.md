# AI Prompts — Homework 4

This file records every prompt typed into the vibe coder for Homework 4, verbatim and in
chronological order. It is a record of what was typed, not of the files the assistant
generated, so prompts are quoted exactly as entered — typos and all.

**Assignment:** _To be filled in once the scope is described._

The **Prompt Log** below is the running chronological record. The **Problem sections**
that follow group those same prompts under the thirteen assignment problems, showing the
work was done problem by problem rather than submitted all at once.

---

## Prompt Log

### 2026-10-04 — Prompt 1

> okay back to my-app-foundations folder, this is now Homework 5

### 2026-10-04 — Prompt 2

> yes this is homework 4, sorry, everything tonight goes in that. Please make AI_promts.md log and update it and a section for each problem 1-13 (this is #1 titled "Vibe coder prompts). Each section should include the problem # and title ill provide, the one unique prompt I enter, and the one follow up promt if needed with a sentence on what was missing.

### 2026-10-04 — Prompt 3

> Problem 2, "Analyze the database,"  please look into the database "data/campus_customs.db " and understand the fields of each table including "catalogue,"  "inventory," and "users" Begin a file, "output/harness.md" to record each table + fields, add a sentence on why the fields all matter to the shop/chatbot.

### 2026-10-04 — Prompt 4

> did you check for that file from the previous homework, it should be in that folder?

### 2026-10-04 — Prompt 5

> yup, found it, unzip my most recent download it should be in there.

### 2026-10-04 — Prompt 6

> Problem 3, "Build the Campus Customs website,"  build up a "React + Vite + TypeScript" front end for Campus Customs  with a navigation bar for "Home, Products, About Us, Log In, Create Accounts",  the home and about us concepts should come from "https://yalebulldogblue.com/"  but mix up the words so it's not exact plagarism, on the products page include images from catalogue (image paths from database) + product name, price and mini description. make it so each product card clicked opens a single-item page with the large image on the left and words on the right including more detailed description, price, sizes, availbility etc.. Include a chat in the bottom right like a floating chat (it does not need an agent talk now, just a stub to call thw backend later. Soon we want a API to read the database to start a FastAPI app in backend/main.py only to serve products and images, we will grow it in a later problem

### 2026-10-04 — Prompt 7

> make it Yale navy instead of green, with a bunch of white, the style should kinda match the site but not be deriviate or a copy

### 2026-10-04 — Prompt 8

> Problem 4, "Create account and login" now build a normal create-account / login flow. "create account: first name, last name, email password (please add confirm password) then a login which includes email and password. new accounts go into the "users" table and store passwords securely so no hackers human or ai can access them. the seed database includes a test user for building, their email is "test@campuscustoms.yale.edu" and thier password is "password" . confrim you can log them as a user and that the new account you create works. then update harness/output.md with how authorization works (ie what you store and how they are protected)

### 2026-10-04 — Prompt 9

> Now problem 5, "PydanticAI agent backend" now make chatbot as pydanticAI agent behind FastAPI  connected to front-end chat widget. the API app should be in backend/main.py the file you run with Uvicorn. Copy homework 3 by having the agent as the  following files next to it: "backend/prompts/prompt.md" to track the system, "backend/agent.py" for entry/wiring, "backend/tools.py" for the tools the agent can use, and "backend/models.py" with the Pydantic strucutr types. In main.py build a route so a message vfrom the website chat gets a reply from the agent + what is nedded for products/auth. Use API code for the agent, but do it securely! Campus Customs voice and safety basics in prompts/prompt.md not tools or safety yet. models.py should include types for chat replies/product cards as required. Record how frontend talks to FastAPI and the agent loaded strucutre with prompt file + model recorded: all in output/harness.md. the backend shoudl run from backend/ folder like: "uvicorn main:app --reload --port 8000"

### 2026-10-05 — Prompt 10

> Now problem 6, "Tools: product info and stock" now give agent tools to draw info from "campus_customs.db" including product description, price, and how many are in stock (by size when clicked). The agent CANNOT invent prices or quantiies, draw from the database and say out of stock when relevant. Build out prompts/promt.md so the agent knows to call these tools for questions on those topics, and add/return types in models.py    Also record each tool and which and why you picked various fields for lookup results in output/harness.md

### 2026-10-05 — Prompt 11

> Now problem 7, "chat search that updates the page," now add a feature to the site when a customer asks about a thing, for example "what hats do you sell?" the agent will search the catalogue then the website will change to show all the hats sold (or matching product cards to the question that include image, name, price and breif descriptions maybe stock). This is API contract the agent will return the product matches and then front end renders them beautifully on the website. After the new cards load, ensure the same single-item page behavior we build in problem 3 still works including the ones the chat recently put on the page should still open that detail view (big image + full info when clicked). Record how search results meet the page with prompts/prompt.md and output/harness.md.

### 2026-10-05 — Prompt 12

> Now problem 8, "Customer memory," now when a customer is logged in, save thier previous chat history in the database in a relevant table and reload it when they log back in, the agent should know the name and email of who they are chatting, put that in agent deps (or a similar clear pattern),  and/or the tools the agent can use. also have enough page context to answer questions without all the info, for example, "do you have this in another color?" the agent should know what they mean, you can put code into the agent context. Only use the history for when people are logged in, but guests can still chat. record how chat history is stored, what consumer fields the agent sees, and how page context is passed in output/harness.md

### 2026-10-05 — Prompt 13

> Now problem 9, "usability improvements" I want you to improve the core shop. Pick and implement two front-end usability improvements  then two agent/back end usability improvements. Front end: make it look better and ease of customers use. On the back end choose things that make it more accurate, faster, cheaper or new tools. write "output/usability.md" before or as you build and include what you did and why it helped the customer or business for each improvement. make sure each improvement actually works and shows up in the app. This problem depends on weather the outputs actually show up and work compared to the record in the write up.

### 2026-10-05 — Prompt 14

> Now problem 10, "style the website," add beautiful design so the site feels like a real Campus Customs storefront with: fonts, color, heirarchy, motion, product presentation, chat feel etc. I sent the Campus Customs website eailer you can use to check, please make it imagnative and innovative, I'll get more points for that. write "output/design.md" to record what changed and why it should help customers stay on the site and buy stuff. But keep the write up short and to the point.

### 2026-10-05 — Prompt 15

> great, now problem 11, "site testing (app check)" please check the live site and record your findings in output/app_check.html which should be a page I can open with a doubleclick, include clear screenshots with sentences below for: the chat checking the inventory level of an item (with real price/stock from database), dynamic search results cards that show up after a question about a certain inventory category (like t-shirts), and one of the usability features you added in problem 9. make the html easy for graders by having a heading for each check, screenshot, and one/two sentences on what the screenshot indicates. put screenshot files in output/app_check_images/ and them from app_check.html with relevant paths like app_check_images/inventory.png make sure the screenshots have words not that small.

### 2026-10-07 — Prompt 16

> another one, problem 12, "Audit trail, safety, finish harness" retain a append-only output/audit_trail.json of the agent loop activity with time, tool, short args/result, reason for stop ). Do not clear/wipe between runs. also think of safety rules for the agent (no human faces, protect keys, passwords, etc..) and store in prompts/prompt.md. Finish output/harness.md to clearly show the system procedure: model fields in models.py + reason for choice, tools+abilities, safety rules added and specifics on loop limits, result caps, models, how to run frontend + back end

---

## Problem 1 — Vibe Coder Prompts

### Initial prompt

> okay back to my-app-foundations folder, this is now Homework 5

### Follow-up prompt

> yes this is homework 4, sorry, everything tonight goes in that. Please make AI_promts.md log and update it and a section for each problem 1-13 (this is #1 titled "Vibe coder prompts). Each section should include the problem # and title ill provide, the one unique prompt I enter, and the one follow up promt if needed with a sentence on what was missing.

### What was missing from the first prompt

The first prompt named the wrong folder (`homework-05` instead of `homework-04`) and did
not say that a prompt log was wanted; the follow-up corrected the folder and specified the
log format, including the thirteen problem sections and what each section must contain.

---

## Problem 2 — Analyze the Database

### Initial prompt

> Problem 2, "Analyze the database,"  please look into the database "data/campus_customs.db " and understand the fields of each table including "catalogue,"  "inventory," and "users" Begin a file, "output/harness.md" to record each table + fields, add a sentence on why the fields all matter to the shop/chatbot.

### Follow-up prompts

> did you check for that file from the previous homework, it should be in that folder?

> yup, found it, unzip my most recent download it should be in there.

### What was missing from the first prompt

The initial prompt pointed to `data/campus_customs.db`, but the Homework 4 course data
pack had not been downloaded or unzipped yet, so that file did not exist anywhere on the
machine; the follow-ups confirmed it was not left over from Homework 3 and then supplied
its real location, the most recent download.

---

## Problem 3 — Build the Campus Customs Website

### Initial prompt

> Problem 3, "Build the Campus Customs website,"  build up a "React + Vite + TypeScript" front end for Campus Customs  with a navigation bar for "Home, Products, About Us, Log In, Create Accounts",  the home and about us concepts should come from "https://yalebulldogblue.com/"  but mix up the words so it's not exact plagarism, on the products page include images from catalogue (image paths from database) + product name, price and mini description. make it so each product card clicked opens a single-item page with the large image on the left and words on the right including more detailed description, price, sizes, availbility etc.. Include a chat in the bottom right like a floating chat (it does not need an agent talk now, just a stub to call thw backend later. Soon we want a API to read the database to start a FastAPI app in backend/main.py only to serve products and images, we will grow it in a later problem

### Follow-up prompt

> make it Yale navy instead of green, with a bunch of white, the style should kinda match the site but not be deriviate or a copy

### What was missing from the first prompt

The initial prompt specified the stack, the navigation, both page layouts, the chat stub,
and the backend scope, and the whole build was completed from it in one pass; it did not
name a colour palette, so the project's default green-and-tan direction was used, and the
follow-up replaced it with Yale navy on white.

---

## Problem 4 — Create Account and Login

### Initial prompt

> Problem 4, "Create account and login" now build a normal create-account / login flow. "create account: first name, last name, email password (please add confirm password) then a login which includes email and password. new accounts go into the "users" table and store passwords securely so no hackers human or ai can access them. the seed database includes a test user for building, their email is "test@campuscustoms.yale.edu" and thier password is "password" . confrim you can log them as a user and that the new account you create works. then update harness/output.md with how authorization works (ie what you store and how they are protected)

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt named both forms and their fields, where accounts are
stored, the test account to verify against, and the documentation to update, and the work
was completed from it in one pass.

---

## Problem 5 — PydanticAI Agent Backend

### Initial prompt

> Now problem 5, "PydanticAI agent backend" now make chatbot as pydanticAI agent behind FastAPI  connected to front-end chat widget. the API app should be in backend/main.py the file you run with Uvicorn. Copy homework 3 by having the agent as the  following files next to it: "backend/prompts/prompt.md" to track the system, "backend/agent.py" for entry/wiring, "backend/tools.py" for the tools the agent can use, and "backend/models.py" with the Pydantic strucutr types. In main.py build a route so a message vfrom the website chat gets a reply from the agent + what is nedded for products/auth. Use API code for the agent, but do it securely! Campus Customs voice and safety basics in prompts/prompt.md not tools or safety yet. models.py should include types for chat replies/product cards as required. Record how frontend talks to FastAPI and the agent loaded strucutre with prompt file + model recorded: all in output/harness.md. the backend shoudl run from backend/ folder like: "uvicorn main:app --reload --port 8000"

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt named every file, the route, the model and prompt-file
documentation to record, and the uvicorn command, and the work was completed from it in one
pass. One phrase was read in context rather than literally: "Campus Customs voice and safety
basics in prompts/prompt.md not tools or safety yet" was taken to mean the prompt file
should carry the voice and basic safety rules now, with the fuller tool and safety sections
left for a later problem, so `prompts/prompt.md` keeps its tool guidance to the minimum the
agent needs to call the tools at all.

---

## Problem 6 — Tools: Product Info and Stock

### Initial prompt

> Now problem 6, "Tools: product info and stock" now give agent tools to draw info from "campus_customs.db" including product description, price, and how many are in stock (by size when clicked). The agent CANNOT invent prices or quantiies, draw from the database and say out of stock when relevant. Build out prompts/promt.md so the agent knows to call these tools for questions on those topics, and add/return types in models.py    Also record each tool and which and why you picked various fields for lookup results in output/harness.md

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing. Part of this problem was already satisfied by Problem 5, which created
`search_catalogue`, `get_product_details`, and `check_size_availability`; this problem added
the per-size stock tool `get_stock_by_size`, added `ProductStock` and the `low_stock_sizes`
field to `models.py`, rewrote the grounding and stock sections of `prompts/prompt.md` with a
question-to-tool routing table and explicit no-invented-price and no-invented-quantity
rules, and recorded the field-by-field rationale for every tool in `output/harness.md`.

---

## Problem 7 — Chat Search That Updates the Page

### Initial prompt

> Now problem 7, "chat search that updates the page," now add a feature to the site when a customer asks about a thing, for example "what hats do you sell?" the agent will search the catalogue then the website will change to show all the hats sold (or matching product cards to the question that include image, name, price and breif descriptions maybe stock). This is API contract the agent will return the product matches and then front end renders them beautifully on the website. After the new cards load, ensure the same single-item page behavior we build in problem 3 still works including the ones the chat recently put on the page should still open that detail view (big image + full info when clicked). Record how search results meet the page with prompts/prompt.md and output/harness.md.

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt described the behaviour, the API contract, the card contents,
the detail-view requirement, and both files to document, and the work was completed from it
in one pass.

---

## Problem 8 — Customer Memory

### Initial prompt

> Now problem 8, "Customer memory," now when a customer is logged in, save thier previous chat history in the database in a relevant table and reload it when they log back in, the agent should know the name and email of who they are chatting, put that in agent deps (or a similar clear pattern),  and/or the tools the agent can use. also have enough page context to answer questions without all the info, for example, "do you have this in another color?" the agent should know what they mean, you can put code into the agent context. Only use the history for when people are logged in, but guests can still chat. record how chat history is stored, what consumer fields the agent sees, and how page context is passed in output/harness.md

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt specified the storage, the deps pattern, the page-context
requirement, the guest rule, and the three things to document, and the work was completed
from it in one pass. One earlier decision was reversed on purpose: Problem 5 deliberately
kept the customer's email away from the model, and this prompt asked for the name and email,
so the email is now in the agent dependencies and the earlier note in `output/harness.md`
was marked as superseded rather than left to contradict it.

---

## Problem 9 — Usability Improvements

### Initial prompt

> Now problem 9, "usability improvements" I want you to improve the core shop. Pick and implement two front-end usability improvements  then two agent/back end usability improvements. Front end: make it look better and ease of customers use. On the back end choose things that make it more accurate, faster, cheaper or new tools. write "output/usability.md" before or as you build and include what you did and why it helped the customer or business for each improvement. make sure each improvement actually works and shows up in the app. This problem depends on weather the outputs actually show up and work compared to the record in the write up.

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt set the count, the split between front end and back end, the
criteria for each side, the file to write, and the requirement that each improvement
actually work in the app. `output/usability.md` was written first as a plan and then
completed with measured results.

---

## Problem 10 — Style the Website

### Initial prompt

> Now problem 10, "style the website," add beautiful design so the site feels like a real Campus Customs storefront with: fonts, color, heirarchy, motion, product presentation, chat feel etc. I sent the Campus Customs website eailer you can use to check, please make it imagnative and innovative, I'll get more points for that. write "output/design.md" to record what changed and why it should help customers stay on the site and buy stuff. But keep the write up short and to the point.

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing from the design brief, which named the areas to cover and the file to
write. One reference could not be used: the prompt says "I sent the Campus Customs website
earlier", but the only site sent in this homework was the one named in Problem 3, used for
the Home and About *concepts*. Campus Customs is the fictional shop this project is building,
so the design was built from the catalogue's own data instead, and `output/design.md` records
that rather than implying a reference site was checked.

---

## Problem 11 — Site Testing (App Check)

### Initial prompt

> great, now problem 11, "site testing (app check)" please check the live site and record your findings in output/app_check.html which should be a page I can open with a doubleclick, include clear screenshots with sentences below for: the chat checking the inventory level of an item (with real price/stock from database), dynamic search results cards that show up after a question about a certain inventory category (like t-shirts), and one of the usability features you added in problem 9. make the html easy for graders by having a heading for each check, screenshot, and one/two sentences on what the screenshot indicates. put screenshot files in output/app_check_images/ and them from app_check.html with relevant paths like app_check_images/inventory.png make sure the screenshots have words not that small.

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt named the three checks, the output file, the image folder,
the relative path style, the per-check structure, and the legibility requirement. The three
screenshots were captured from the running site, and every number the assistant produced was
re-checked against `data/campus_customs.db` before being written up.

---

## Problem 12 — Audit Trail, Safety, Finish Harness

### Initial prompt

> another one, problem 12, "Audit trail, safety, finish harness" retain a append-only output/audit_trail.json of the agent loop activity with time, tool, short args/result, reason for stop ). Do not clear/wipe between runs. also think of safety rules for the agent (no human faces, protect keys, passwords, etc..) and store in prompts/prompt.md. Finish output/harness.md to clearly show the system procedure: model fields in models.py + reason for choice, tools+abilities, safety rules added and specifics on loop limits, result caps, models, how to run frontend + back end

### Follow-up prompt, if needed

_None needed._

### What was missing from the first prompt

Nothing was missing; the prompt named the audit fields, the append-only requirement, the
file to hold the safety rules, the kinds of rule wanted, and every section the finished
harness had to cover. The safety rules were then checked against live probes rather than
just written down, and one of those probes — a prompt-injection attempt asking for the
system prompt and the API key — produced the first `error` record in the audit trail, which
is included in the write-up as an example of the trail doing its job.

---

## Problem 13 — _title to be provided_

### Initial prompt

_Add the prompt for this problem when it is entered._

### Follow-up prompt, if needed

_Add only if a follow-up is needed._

### What was missing from the first prompt

_Explain why the follow-up was needed, if applicable._
