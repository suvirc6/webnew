import asyncio
import os
from playwright.async_api import async_playwright
import openai

# Set your OpenAI API key (or ensure it's in your environment)
client = openai.OpenAI(api_key=os.getenv("OPENAI_KEY"))  # or pass your key directly

async def run():
    search_term = input("Enter stock/company name to search on Trendlyne: ")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://trendlyne.com/")

        await page.fill('input#feature-search', search_term)
        await page.wait_for_timeout(2000)

        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(1000)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)

        await page.wait_for_load_state('load')

        trendlyne_url = page.url
        print("Navigated URL from Trendlyne:", trendlyne_url)
        trendlyne_url_new= url = trendlyne_url.replace( "equity","research-reports")
        print("Buy/Sell/Hold URL", trendlyne_url_new)

        jina_url = f"https://r.jina.ai/{trendlyne_url_new}"
        print("Navigating to Jina.ai URL:", jina_url)
        await page.goto(jina_url)

        await page.wait_for_load_state('load')
        page_text = await page.inner_text('body')
        print("Extracted Text from Jina.ai:", page_text[:1000])  # Just a preview

        await browser.close()

        print("Summarizing with OpenAI...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial research assistant.Tell me how many brokers suggest Buy / Sell /Hold. Respond like Buy: X number of brokers, Sell: Y number of brokers, etc."
                },
                {
                    "role": "user",
                    "content": f"You are a financial research assistant.Tell me how many brokers suggest Buy / Sell /Hold. Respond like Buy: X number of brokers, Sell: Y number of brokers, etc. using the following page content:\n\n{page_text}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        web_summary = response.choices[0].message.content
        print("\n📝 Web Summary:\n", web_summary)

asyncio.run(run())
