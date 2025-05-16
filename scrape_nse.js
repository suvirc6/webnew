const puppeteer = require('puppeteer-extra');


  async function scrapeFinancials(tickers) {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: "/snap/bin/chromium",
    args: [
      "--disable-blink-features=AutomationControlled",
      "--disable-features=IsolateOrigins,site-per-process",
      "--disable-notifications",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--single-process",
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
    await page.goto("https://www.nseindia.com", { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 3000)); // wait for session cookies

    let results = [];

    for (const ticker of tickers) {
      const url = `https://www.nseindia.com/get-quotes/equity?symbol=${ticker}`;
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

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

// function compileToTable(dataArray) {
//   if (!dataArray || dataArray.length === 0) return {};

//   // Get all variable names (keys) except ticker
//   const variables = Object.keys(dataArray[0]).filter(k => k !== 'ticker');

//   // Initialize table with each variable as a row
//   const table = {};

//   for (const variable of variables) {
//     table[variable] = {};
//     for (const entry of dataArray) {
//       table[variable][entry.ticker] = entry[variable] || null;
//     }
//   }

//   return table;
// }

// Export functions for external use
module.exports = { scrapeFinancials };

// If run directly, parse tickers from CLI args and run
if (require.main === module) {
  (async () => {
    const tickers = process.argv.slice(2);
    if (tickers.length === 0) {
      console.log("Please provide one or more ticker symbols as command line arguments.");
      process.exit(1);
    }
    try {
      const data = await scrapeFinancials(tickers);
      // const table = compileToTable(data);
      // console.log("Compiled Table Format:");
      // console.log(JSON.stringify(table, null, 2));
      console.log(JSON.stringify(data));

    } catch (e) {
      console.error(e);
    }
  })();
}
