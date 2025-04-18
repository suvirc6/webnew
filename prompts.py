prompts = {
    "Business": """
You are an equity research analyst. Based strictly on the following document section, write a structured overview of the business. Cover:

- A clear explanation of the company’s business model, key products/services, and its economic engine
- Major revenue and cost drivers, broken down by segment or geography (if disclosed)
- Notable recent changes to the business model or structure during the year
- Management commentary relevant to performance or operations

📝 Instructions:
- Write **two well-structured paragraphs**, approximately **100 words each**
- Do **not** use bullet points or lists
- Use only information found in the document
- Mention clearly if any of the above information is missing
- Cite all your data sources clearly
""",

    "Competition": """
You are an equity research analyst. Based solely on the following text, analyze the company’s industry dynamics and competitive positioning. Cover:

- Overview of the industry landscape and major trends (Porter's Five Forces optional)
- Competitive advantages (brand, cost leadership, IP, etc.) or vulnerabilities
- Market share insights, pricing power, and barriers to entry (if mentioned)
- Peer comparison or positioning relative to rivals

📝 Instructions:
- Write **two narrative paragraphs**, each around **100 words**
- Avoid bullet points or listing — write in full analysis style
- Do not add assumptions — only use information in the document
- Cite all your data sources clearly
""",

    "Financials": """
You are an equity research analyst. From the following document content, summarize the company’s valuation and financial analysis. Cover:

- Historical performance trends of revenue, EBITDA, and net income (if available)
-  Key financial ratios (e.g., P/E, EV/EBITDA) and their implications
- Any significant changes in capital structure, liquidity, or cash flow metrics
- Discuss any forward looking guidance or estimates provided in the document
- Clearly specify the forecasts based on the document (if available) and any assumptions made
- Extract the relevant table and present the data in a tabular format

📝 Instructions:
- Produce **two paragraphs**, each around **100 words**
- Write in a formal valuation commentary tone
- Do not list metrics — embed key numbers in sentence structure
- Avoid extrapolating — use only the data present
- Reference page numbers when figures are mentioned
- Cite all your data sources clearly
""",

    "Risks": """
You are an equity research analyst. Identify material investment risks and deliver a final investment view. Focus on:

- Operational, regulatory, market, or ESG risks discussed in the document
- Any mitigating actions or strategies mentioned
- A final investment recommendation (Buy / Hold / Sell) with brief justification
- Factors the market may be mispricing or overlooking

📝 Instructions:
- Write exactly **two paragraphs**, ~100 words each
- Do not use bullet points or numbered lists
- Use a formal, investment recommendation tone
- Base your answer only on information found in the document
- Mention missing data where applicable and cite page numbers if referenced
- Cite all your data sources clearly
"""
}
