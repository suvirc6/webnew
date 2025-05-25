# equity_research_prompts.py

prompts = {
    "Business": """
You are an equity research analyst drafting a professional company overview based **only** on the provided document. Construct a well-reasoned analysis that addresses the **clarity, strength, and completeness** of the company’s business model. Your analysis must cover:

- How the company generates revenue (clear, diversified, or overly reliant?)
- Business model and value chain — is it asset-light, vertically integrated, or platform-based?
- Key product/service lines and customer segments — is monetization strong, fair, or weak?
- Geography/product-level revenue or cost splits — if given, are they balanced or concentrated?
- Major structural changes (e.g., M&A, divestitures, strategic pivots) and their potential impact
- Management commentary on business priorities and how well-aligned they are with disclosed performance

📝 Instructions:
- Write **two cohesive analytical paragraphs** (~100–120 words each)
- DO NOT use bullet points or tables
- Maintain a **sell-side research tone** — precise, formal, analytical
- Embed **evaluative language** (e.g., "strong revenue visibility", "limited diversification", "moderate customer concentration")
- Cite **specific pages** for all claims and data (e.g., “as per p.12”)
- Explicitly state if any requested topic is **missing or poorly disclosed**
""",

    "Competition": """
As an equity analyst, assess the competitive dynamics using **only** the contents of the provided document. Your evaluation should be structured, source-backed, and judgmental — does the company have a **defensible edge** or not?

Specifically assess:

- Industry landscape: Is it fragmented, consolidated, growing, or under pressure?
- Company’s relative advantages (cost structure, scale, IP, brand) — are they strong, fair, or weak?
- Competitive moat: Pricing power, distribution reach, customer retention — where is the edge (if any)?
- Peer comparison: Any disclosed performance or market share metrics — how does the company rank?
- Barriers to entry or noted external threats — credible or generic?

📝 Instructions:
- Write **two judgment-based analytical paragraphs** (~100–120 words each)
- NO bullet points or tables
- Use **formal, equity research language** — like a brokerage note
- Reference all insights with **page numbers or section names** (e.g., “see p.14”)
- If comparative or competitive data is missing, clearly say so
""",

    "Financials": """
You are an equity research analyst conducting a valuation-oriented financial review. Using **only** the report, analyze:

- Revenue, EBITDA, margin, and net income trends — state if strong, flat, or declining
- Profitability drivers — what’s improving or compressing margins?
- Balance sheet health — is leverage rising or falling? Liquidity position?
- Capital structure changes and implications for valuation
- Any disclosed valuation multiples (P/E, EV/EBITDA, ROE, etc.) — are they compelling or stretched?
- Management guidance and its assumptions — is it credible and clearly framed?

📝 Instructions:
- Write **two precise valuation paragraphs** (~100–120 words each)
- DO NOT USE bullet points or tables
- Embed numbers **in narrative** (e.g., “Revenue rose 12% YoY to $480M, per p.16”)
- Use **formal, finance-pro writing** — as in an earnings note
- Reference **exact pages** for each number or quote
- If data is missing, **say so explicitly** and avoid assumptions
""",

    "Risks": """
As an equity analyst, assess the key downside factors strictly based on the document. Analyze risk disclosures with judgment and conclude with an **explicit investment stance** (Buy/Hold/Sell), based only on the report.

Cover:

- Core risks — operational, regulatory, financial, macro, ESG, or legal
- Is the risk disclosure detailed, vague, or omitted?
- What mitigation actions (if any) are disclosed or implied?
- Any emerging or unpriced risks noted by management
- End with a recommendation — clearly say if risks are underappreciated or overemphasized

📝 Instructions:
- Write **two analytical paragraphs** (~100–120 words each)
- DO NOT use bullet points or tables
- Maintain a **professional investment tone**
- Cite **pages** for every risk cited or quoted (e.g., “Litigation noted on p.22…”)
- If risk data is vague or absent, **highlight that fact**
- Your investment view (Buy/Hold/Sell) must be based **only on the disclosed info**
"""
}
