import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import List


async def fetch_table(page, company: str):
    input_selector = 'input[placeholder*="Search by Company name"]'

    # Focus and fill company name
    await page.click(input_selector)
    await page.fill(input_selector, company)
    await page.wait_for_timeout(2000)  # wait for dropdown suggestions to appear

    # Press ArrowDown then Enter to select first suggestion
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(500)  # slight pause before enter
    await page.keyboard.press("Enter")

    # Wait for navigation/network and extra buffer
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(3000)

    # Scroll down to load any lazy content
    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)

    rows = await page.query_selector_all('#topFinancialResultsTable tbody tr')
    data = []

    for row in rows:
        cells = await row.query_selector_all('td')
        values = [await cell.inner_text() for cell in cells]
        if values and len(values) >= 4:
            values = values[:4]  # first 4 columns only
            values.append(company)
            data.append(values)

    return data


async def scrape_financials(companies: List[str]):
    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()

        await page.goto("https://www.nseindia.com/")
        await page.wait_for_timeout(3000)

        for company in companies:
            try:
                table_data = await fetch_table(page, company)
                all_data.extend(table_data)
                await page.goto("https://www.nseindia.com/")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Error scraping {company}: {e}")

        await browser.close()

    df = pd.DataFrame(all_data, columns=["Quarter Ended", "Total Income", "Net Profit/Loss", "EPS", "Company"])
    return df


def format_and_pivot(df: pd.DataFrame) -> pd.DataFrame:
    # Parse the Quarter Ended column as datetime for proper sorting
    df["Parsed Quarter"] = pd.to_datetime(df["Quarter Ended"], errors="coerce")
    latest_quarter = df["Parsed Quarter"].iloc[0]  # Get the latest quarter
    latest_data = df[df["Parsed Quarter"] == latest_quarter].copy()

    latest_data["Column"] = latest_data["Company"] + " - " + latest_data["Quarter Ended"]

    df_melted = latest_data.melt(
        id_vars=["Column"],
        value_vars=["Total Income", "Net Profit/Loss", "EPS"],
        var_name="Metric",
        value_name="Value"
    )

    pivoted = df_melted.set_index(["Column"]).T
    return pivoted

async def get_financial_comparison(companies: List[str]) -> pd.DataFrame:
    df = await scrape_financials(companies)
    if df.empty:
        return pd.DataFrame()
    return format_and_pivot(df)

# # For standalone test
# if __name__ == "__main__":
#     companies = ["apar"]
#     import asyncio
#     df = asyncio.run(get_financial_comparison(companies))
#     print(df)


