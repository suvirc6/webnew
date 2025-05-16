const puppeteer = require('puppeteer');

async function scrapeFinancials(tickers) {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: "/usr/bin/chromium-browser",  // keep if using snap chromium; else remove this line
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-notifications',
    ],
  });

  try {
    const page = await browser.newPage();

    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
      "AppleWebKit/537.36 (KHTML, like Gecko) " +
      "Chrome/114.0.0.0 Safari/537.36"
    );

    await page.setExtraHTTPHeaders({
      'accept-language': 'en-US,en;q=0.9',
    });

    // Go to NSE homepage once to get cookies/session
    await page.goto("https://www.nseindia.com", { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 3000)); // wait for session cookies

    let results = [];

    for (const ticker of tickers) {
      const url = `https://www.nseindia.com/get-quotes/equity?symbol=${ticker}`;
      console.log(`Navigating to ${url}`);
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

      // Take screenshot for debugging page load issues
      await page.screenshot({ path: `screenshot-${ticker}.png`, fullPage: true });

      try {
        await page.waitForSelector('#topFinancialResultsTable', { timeout: 10000 });

        // Extract only the first row (latest quarter) as JSON
        const latestData = await page.evaluate(() => {
          const table = document.querySelector('#topFinancialResultsTable');
          if (!table) return null;

          const firstRow = table.querySelector('tbody tr');
          if (!firstRow) return null;

          const cells = firstRow.querySelectorAll('td');
          return {
            quarter_ended: cells[0]?.innerText.trim(),
            total_income: cells[1]?.innerText.trim(),
            net_profit_loss: cells[2]?.innerText.trim(),
            earnings_per_share: cells[3]?.innerText.trim(),
          };
        });

        if (!latestData) {
          console.warn(`No financial data found for ticker: ${ticker}`);
          continue;
        }

        results.push({ ticker, ...latestData });
      } catch (e) {
        console.warn(`Failed to get data for ticker ${ticker}: ${e.message}`);
      }
    }

    return results;

  } catch (err) {
    console.error("Error scraping:", err.message);
    throw err;
  } finally {
    await browser.close();
  }
}

// Export functions for external use
module.exports = { scrapeFinancials };

// Run script with tickers from command line
if (require.main === module) {
  (async () => {
    const tickers = process.argv.slice(2);
    if (tickers.length === 0) {
      console.log("Please provide one or more ticker symbols as command line arguments.");
      process.exit(1);
    }
    try {
      const data = await scrapeFinancials(tickers);
      console.log(JSON.stringify(data, null, 2));
    } catch (e) {
      console.error(e);
    }
  })();
}
