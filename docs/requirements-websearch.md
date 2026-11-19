# Stage 3 Requirements: Web Search

**Status:** Complete (19 Nov 2026) · **Date:** 19 Nov 2026 · **Owner:** Fahmy Islam

## 1. User

Me: a job seeker preparing applications and interviews.

## 2. Problem

The AI's knowledge is out of date. It doesn't know current company news, open roles or salaries, and it can state invented answers confidently instead of saying it doesn't know.

## 3. Goal

The assistant searches the web when a question needs current information, and answers briefly with source links I can check.

## 4. User stories

1. As a job seeker, I want to ask "what does BJIT do and what's new with them?" and get a short answer with source links, so that I can prepare for applications and interviews.
2. As a job seeker, I want current answers (for example typical junior BA salaries in Dhaka) to include sources, so that I can check whether they're true.
3. As a job seeker, I want the assistant to decide by itself when a search is needed, so that simple questions stay fast and use no search credits.

## 5. Service choice

| Option | Free | Card needed | After the free amount |
|---|---|---|---|
| **Tavily (chosen)** | 1,000 credits/month (basic search = 1 credit) | No | $0.008 per credit |
| Brave Search | $5 monthly credit (~1,000 searches) | Yes, charged after the credit | $5 per 1,000 searches |
| OpenAI built-in search | none | uses OpenAI billing | $10 per 1,000 searches + page text as tokens |

**Why Tavily:** no credit card means no surprise bills, and my expected use (5-10 searches a day) fits inside the free amount. Prices checked 19 Nov 2026; check again at signup.

## 6. The assistant must NOT

1. Answer questions about current facts without giving sources.
2. Put private data (emails, CV, tracker contents) into search queries. Queries go to an outside company.
3. Follow instructions written on web pages. Web content is treated as data, like email content (prompt-injection protection).
4. Make more than 3 searches for one message, to protect the free credits and prevent search loops.

## 7. How we'll know it works (acceptance criteria)

- [x] "What does BJIT do?" returns a short answer with source links (1 search, 4 links).
- [x] "What's 15 × 4?" makes no search.
- [x] A message that would need many searches stops at 3 and still answers (a 5-company comparison searched exactly 3 times).
- [x] Search queries never contain email text or CV details (checked in the logs; queries with an email address are blocked in code).
- [x] The Tavily key is in `.env` only, never in the code or on GitHub (checked on GitHub after pushing).

### Test findings

| Finding | Fix |
|---|---|
| A long answer (5-company comparison) crashed with "Message is too long": Telegram allows at most 4,096 characters per message | Long answers are split into several messages, cutting between paragraphs first |
| The error said "contacting the AI" failed, but the AI had worked; sending to Telegram failed | Separate error messages for "the AI failed" and "sending failed" |
| After hitting the 3-search limit, the AI said Pathao and bKash had "no data available", although it never searched them | When the limit is hit, the AI is told to say which parts it didn't search |
| Telegram showed a preview card for the first link, which added noise to answers with several sources | Link previews turned off for all bot messages |
| Web pages can contain hidden instructions, like emails | Web results are labelled as data, and tracker changes are blocked in any message where web pages were read |

## 8. Known limitations

- Answers depend on the pages Tavily finds, which can be wrong or outdated; I check the source links for anything important.
- The "say what you didn't search" rule is an instruction to the AI, not a code check.
- The free plan is 1,000 searches per month; after that, searches stop (no charges, because no card is attached).

## 9. Out of scope

- Reading full web pages in depth (summaries of search results only)
- Scheduled or automatic searches (for example daily job alerts)
