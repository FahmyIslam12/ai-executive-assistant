# Stage 3 Requirements: Web Search

**Status:** Approved · **Date:** 19 Nov 2026 · **Owner:** Fahmy Islam

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

- [ ] "What does BJIT do?" returns a short answer with 2-3 source links.
- [ ] "What's 15 × 4?" makes no search.
- [ ] A message that would need many searches stops at 3 and still answers.
- [ ] Search queries never contain email text or CV details (checked in the logs).
- [ ] The Tavily key is in `.env` only, never in the code or on GitHub.

## 8. Out of scope

- Reading full web pages in depth (summaries of search results only)
- Scheduled or automatic searches (for example daily job alerts)
