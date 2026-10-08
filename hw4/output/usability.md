# Campus Customs Usability Improvements

## 1. Frontend: product search and category filtering

The Products page now combines its existing keyword search with a category selector generated from the catalogue's actual `garment_type` values. Both controls work together, update the visible result count immediately, and search product names, descriptions, colors, tags, and garment types.

**Benefit:** Shoppers can narrow a catalogue of 102 products quickly instead of scanning every card. Because category options come from the API data, the interface stays aligned with the merchandise the business actually carries.

**Verification:** Source checks confirmed both controls and their combined filtering logic. Catalogue API regression testing continued to return all 102 products.

## 2. Frontend: loading, error, and empty-result feedback

The catalogue now displays six animated skeleton cards while loading. If the API fails, it shows a plain-language message and a **Try again** button that repeats the request. Searches with no matches explain what happened and provide a **Clear filters** action.

**Benefit:** Customers always understand whether the store is loading, unavailable, or simply has no matching merchandise, and they have an immediate recovery action.

**Verification:** Source checks confirmed the loading skeleton, retry state, no-results message, and filter reset handler. Browser execution remains unavailable because this environment has no Node.js runtime.

## 3. Agent: clarification instead of guessing

The agent prompt now requires a short, useful follow-up question when a request is underspecified or matches multiple products. The product lookup tool returns candidate names instead of choosing an ambiguous match, giving the agent grounded options to present. Suggested clarifiers include garment type, color, school, sport, and budget.

**Benefit:** Customers receive relevant questions and recommendations while the business avoids showing an arbitrary or misleading product.

**Verification:** Looking up the ambiguous term `Yale` returned `found: false`, a clarification instruction, and six real candidate names rather than an assumed product.

## 4. Backend: safe, helpful failure handling

The chat endpoint now separates database failures from general agent/provider failures. Database errors return HTTP 503 with “I can’t check the catalogue right now. Please try again in a moment.” Agent errors return HTTP 502 with “I’m having trouble answering right now. Please try again in a moment.” Full exceptions remain in server logs for diagnosis, while the chat widget displays only the safe response.

**Benefit:** Shoppers get an actionable explanation rather than a silent failure or technical stack trace, while developers retain diagnostic information.

**Verification:** Simulated failures produced the expected 503 and 502 statuses and customer messages. Deliberately embedded technical details appeared in neither API response.
