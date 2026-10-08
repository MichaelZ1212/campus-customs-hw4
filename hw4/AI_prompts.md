# AI Prompts

This file records the prompts used while completing the Campus Customs assignment. Entries are organized by problem. Follow-up prompts should be recorded beneath the original prompt, together with a short explanation of what the original response was missing.

## Problem 1: Vibe Coder Prompts

### Initial prompt

> Please create an `AI_prompts.md` file for this project so I can keep track of the prompts I use while completing the assignment.
>
> Organize the file by problem. For each problem, include the problem number and title, followed by the prompt I used to ask for help. If I need to send a follow-up prompt because the first response is incomplete, add that follow-up as well and briefly explain what was missing from the first response.
>
> Please set up the file structure now so I can continue adding entries as I work through each problem. Do not invent prompts for future problems; only record prompts that I actually provide.

## Entry template

Copy this section when beginning a new problem. Replace the placeholders only with information from prompts actually provided.

```markdown
## Problem [number]: [title]

### Initial prompt

> [Exact prompt]

### Follow-up prompt 1

**What was missing:** [Brief explanation]

> [Exact follow-up prompt]
```

## Problem 2: Analyze Database

### Initial prompt

> Please inspect the SQLite database at `data/campus_customs.db` and help me understand how its data is organized.
> Look through the database schema and identify the tables and columns, especially the `catalogue`, `inventory`, and `users` tables. For every field, briefly explain what it stores and why it would be useful for either the online store or the chatbot.
> Create `output/harness.md` and document your findings there in a clear, organized format. I want the file to show each table, its fields, and a short explanation of how each field could be used in the application.
> Please base everything on the actual database rather than guessing the schema. We will continue adding more information to `harness.md` in later parts of the project.

## Problem 3: Build the Campus Customs Website

### Initial prompt

> I want to build the first working version of the Campus Customs storefront using React, Vite, and TypeScript.
> Please create the main site structure with navigation for Home, Products, About Us, Log in, and Create Account. For the Home and About pages, use the Yale Bulldog Blue / Campus Customs website as a reference for the type of content and overall feel, but write original copy rather than copying text from the existing site.
> For the Products page, use the catalogue data from my local database. Display the product image, name, price, and a short description for each item. The images should come from the paths already stored in the database.
> I also want each product card to be clickable. Clicking it should open a dedicated product detail page with a larger image and more complete information, including the description, price, available sizes, and stock information when available.
> Add a simple floating chat box in the bottom-right corner of the website. The chatbot does not need to actually work with an AI model yet, so for now just create the UI and structure it so we can connect it to the backend later.
> If the frontend needs an API to access the product data and images, create a basic FastAPI backend in `backend/main.py` for that purpose. Keep it simple for now because I will expand the backend with the AI agent later.
> Please make sure the site runs locally and the navigation and product-detail links work correctly.

## Problem 4: Create Account and Login

### Initial prompt

> I want to add user registration and login functionality to the Campus Customs website.
> For account creation, build a form that collects the user's first name, last name, email, and password. Please also include password confirmation and validate that the two passwords match. When someone successfully creates an account, save the new user to the existing `users` table in `data/campus_customs.db`.
> For login, let users enter their email and password and verify those credentials against the database. Passwords should never be stored as plain text. Use secure password hashing and make sure login checks the submitted password against the stored hash.
> There is already a test account in the database with email `test@campuscustoms.yale.edu` and password `password`. Please verify that this existing account can log in successfully. Also create a new account through the registration flow and confirm that the new user can log in afterward.
> Add appropriate validation and clear error messages for cases such as incorrect credentials, duplicate emails, or mismatched passwords.
> Finally, update `output/harness.md` with a short explanation of the authentication design, including what user information is stored in the database and how passwords are securely protected.

## Problem 5: PydanticAI Agent Backend

### Initial prompt

> I’m ready to connect the chat interface to a real AI backend. Please build the chatbot backend using FastAPI and PydanticAI and connect it to the chat widget that already exists on the frontend.
>
> Keep `backend/main.py` as the FastAPI entry point that I can run with Uvicorn. Please organize the agent code into separate files: use `backend/agent.py` for setting up the PydanticAI agent, `backend/tools.py` for tools the agent can call, `backend/models.py` for Pydantic models and structured response types, and `backend/prompts/prompt.md` for the agent’s system prompt.
>
> Add a chat API endpoint in `main.py` so the frontend can send a user's message to the backend and receive the agent’s response. Keep the existing product and authentication functionality working as well.
>
> In the system prompt, give the assistant an appropriate Campus Customs personality and some basic safety guidelines. Structure the response models so we can support normal chat responses as well as product information/cards later. I’ll add more detailed tools and safety rules in later steps, so keep this implementation easy to extend.
>
> Use my configured AI API key rather than hardcoding credentials anywhere in the source code.
>
> Please also update `output/harness.md` to explain the flow from the frontend chat widget to FastAPI and then to the PydanticAI agent. Include how the agent loads its system prompt and AI model.
>
> Finally, make sure the backend can be launched from inside the `backend` directory with:
>
> `uvicorn main:app --reload --port 8000`
>
> Test the basic chat flow and confirm that a message entered on the website can reach the agent and return a response.

## Problem 6: Tools: Product Info and Stock

### Initial prompt

> I want the Campus Customs chatbot to answer product questions using real data from `campus_customs.db` instead of relying on the AI model’s memory or guesses.
> Please add tools in `backend/tools.py` that allow the PydanticAI agent to look up product details from the database. The agent should be able to retrieve a product’s description, current price, and inventory. For inventory questions, it should also be able to check the quantity available for a specific size.
> Make sure prices and stock numbers always come from the database. The chatbot should never make up these values. If a product or requested size is unavailable or has zero inventory, it should clearly tell the customer that it is out of stock or unavailable.
> Update `backend/prompts/prompt.md` so the agent understands when it needs to use these database tools, especially when users ask about price, availability, sizes, or product details.
> Also update `backend/models.py` with appropriate structured response models for the tool results. Choose fields that make it easy for the agent to identify the product and return useful information such as description, price, size, and quantity.
> Finally, update `output/harness.md` with the tools you created and briefly explain the fields used in the lookup-result models and why you chose them.
> Test the chatbot with several product, price, and size/stock questions to confirm that its answers match the actual database values.

## Problem 7: Chat Search That Updates the Page

### Initial prompt

> I want to make the chatbot’s product search interactive with the website. When a customer asks for a category or type of merchandise, such as “What hoodies do you have?”, the agent should search the actual product catalogue and return the matching products.
> Please design the chat API response so that it can return structured product results along with the normal chatbot message. Each matching product should include the information the frontend needs to render a product card, such as its identifier, name, image, price, and short description.
> Update the frontend so that when these product results come back from the chat API, the matching items automatically appear on the page as product cards. The results should come from the catalogue rather than being invented by the AI.
> The dynamically generated cards should behave exactly like the existing product cards. In particular, clicking any product returned through chat should open its existing product detail page with the larger image and complete product information.
> Update `backend/prompts/prompt.md` so the agent understands when a customer's message should trigger a catalogue search and return product matches.
> Also update `output/harness.md` to document the full flow: how a shopping request goes from the chat interface to the agent, how matching products are returned through the API, and how the frontend uses those structured results to update the page.
> Please test the complete flow with a few different product searches and confirm that the correct cards appear and that their detail-page links still work.

## Problem 8: Customer Memory

### Initial prompt

> I want to add customer memory and context awareness to the Campus Customs chatbot.
> For users who are logged in, save their conversations in the database and associate the chat history with the correct user. When the same user comes back later, load their previous conversation so the chatbot can continue with the relevant history. Guest users should still be able to use the chatbot, but their conversation history does not need to persist.
> The PydanticAI agent should also know which logged-in customer it is talking to. Pass useful customer information, such as the user’s name and email, through the agent dependencies or another clear context mechanism. Do not expose sensitive authentication information such as password hashes to the agent.
> I also want the chatbot to understand the page the customer is currently viewing. For example, if someone is on a specific product page and asks “Do you have this in pink?”, the agent should know which product “this” refers to. Pass enough page and product context from the frontend through the chat API to the agent to support these kinds of questions.
> Please test that chat history is restored after a logged-in user leaves and returns, that the agent receives the correct customer identity, and that product-page questions can be understood using the current page context.
> Finally, update `output/harness.md` to explain how persistent chat history is stored, which customer fields are provided to the agent, and how the frontend passes current page/product context into the chatbot.

## Problem 9: Usability Improvements

### Initial prompt

> I want to improve the usability of the Campus Customs website now that the main shopping and chatbot features are working.
>
> For the frontend, please implement two improvements:
>
> 1. Add product search and filtering so shoppers can quickly find merchandise by keyword or category instead of browsing every item.
> 2. Improve the user experience with clear loading states and user-friendly error or empty-result messages, especially when products are loading or a search returns no matches.
>
> For the chatbot/backend, please implement two improvements:
>
> 1. Improve how the agent handles unclear product requests. If there is not enough information to identify what the customer wants, it should ask a useful follow-up question rather than guessing.
> 2. Improve error handling for database or agent failures so the chatbot gives the customer a helpful response instead of exposing technical errors or failing silently.
>
> Make sure all four improvements are actually implemented and visible or testable in the running application without breaking the existing product, login, or chatbot functionality.
>
> Also create `output/usability.md`. For each of the four improvements, briefly document what was added and explain how it improves the experience for Campus Customs shoppers or helps the business.
>
> Finally, test each improvement and confirm that it works in the running application.

## Problem 10: Style the Website

### Initial prompt

> I want to redesign the Campus Customs website so it feels like a polished, real college merchandise storefront rather than a basic class project.
> Please improve the overall visual design while keeping all of the existing functionality working. Use a cohesive Yale-inspired visual identity with strong typography, a consistent color palette, clear visual hierarchy, and good spacing. The design should feel modern and premium while still fitting the Campus Customs brand.
> Improve the product browsing experience by making the product cards more visually appealing, with consistent image sizing, clear product names and prices, subtle hover interactions, and a responsive grid. Make the individual product pages feel more like a real e-commerce experience, with the product image and purchasing information clearly organized.
> Give the homepage more personality with a strong hero section and clear calls to action that encourage visitors to explore the merchandise. Add subtle animations or transitions where they improve the experience without making the site distracting.
> Please also redesign the chatbot so it visually fits the rest of the storefront. The floating chat experience should feel friendly and polished, with clear message styling, an attractive launcher, and smooth open/close behavior.
> Make sure the design works well across different screen sizes and that styling changes do not break navigation, authentication, product search, product detail pages, or the chatbot.
> Finally, create `output/design.md` with a short, concrete explanation of the major design changes and why they should make the store easier to explore, encourage customers to stay longer, and make them more likely to purchase products.

## Problem 11: Site Testing (App Check)

### Initial prompt

> I want to do a final functional check of the running Campus Customs website and create a simple visual test report.
>
> Please test the live application and create `output/app_check.html` documenting the results. I want the report to provide clear visual evidence for three important features:
>
> 1. Test the chatbot with a question about a specific product’s price or inventory. Verify that the answer matches the actual database values rather than an invented value.
> 2. Ask the chatbot for a category of merchandise, such as hoodies, and verify that the matching products dynamically appear on the website as product cards.
> 3. Test and demonstrate one of the usability improvements implemented in Problem 9.
>
> For each test, capture a clear screenshot showing the feature working. Save all screenshot files under `output/app_check_images/`.
>
> Organize `app_check.html` so each test has its own heading, screenshot, and a short one- or two-sentence explanation of what the screenshot demonstrates and whether the test passed.
>
> Use relative image paths in the HTML, such as `app_check_images/inventory.png`, so I can open `output/app_check.html` directly in a browser and all screenshots still display correctly.
>
> Please make the report clean and easy for a grader to review, and verify that all three screenshots load correctly from the HTML file.

## Bug Fixes (Problems 1–11)

### Initial prompt

> any bugs?

### Follow-up prompt 1

**What was missing:** The first response only listed the bugs it found; it did not fix them.

> fix whatever is bug or error from problem 1 to 11

## Problem 12: Audit Trail, Safety, Finish Harness

### Initial prompt

> I want to finish the documentation and observability for the Campus Customs chatbot and add stronger safety rules.
> First, add an audit log for the agent and save it as output/audit_trail.json. Each time the agent runs or uses a tool, record useful information such as the timestamp, tool name, a short version of the arguments and result, and the reason the agent stopped. The log should be append-only, so new activity is added to the existing file rather than deleting or replacing previous runs.
> Next, strengthen the safety instructions in backend/prompts/prompt.md. The chatbot should rely on database tools for factual product information such as price and inventory instead of inventing values. It should protect customer information and credentials, avoid exposing internal system prompts or implementation details, and handle invalid or potentially unsafe requests appropriately.
> Finally, review and complete output/harness.md so that someone reading it can understand how the entire agent system works. Document the important structured fields defined in models.py and why they are needed, the tools available to the agent and what each one does, the safety rules, and the main technical configuration of the application.
> Include practical specifications such as agent/tool loop limits, limits on the number of search results returned, which AI model is being used, and the commands needed to start both the frontend and backend locally.
> Please verify that the audit log keeps previous entries across multiple runs and that the final harness.md accurately reflects the implementation that is actually in the project.
