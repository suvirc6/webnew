const fs = require('fs');
const xlsx = require('xlsx');
const { Parser } = require('json2csv');
const puppeteer = require('puppeteer');

// === Read tickers from tickers.xlsx ===
function readTickersFromExcel(filePath = 'tickers.xlsx') {
  try {
    const workbook = xlsx.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    const data = xlsx.utils.sheet_to_json(sheet);

    return data.map(row => row.Symbol).filter(Boolean); // Only read from 'Symbol' column
  } catch (err) {
    console.error('❌ Error reading tickers.xlsx:', err.message);
    return [];
  }
}

// === Real scraper using Puppeteer with per-ticker logging and error handling ===
async function scrapeFinancials(tickers) {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-features=site-per-process'
    ]
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
    let failedTickers = [];

    for (const ticker of tickers) {
      console.log(`🔍 Scraping ticker: ${ticker}`);
      const url = `https://www.nseindia.com/get-quotes/equity?symbol=${ticker}`;

      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
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
          console.warn(`⚠️ No financial data found for ticker: ${ticker}`);
          failedTickers.push(ticker);
          continue;
        }

        // const cleanedData = {
        //   ticker,
        //   quarter_ended: latestData.quarter_ended,
        //   total_income: parseFloat(latestData.total_income.replace(/,/g, '')) || null,
        //   net_profit_loss: parseFloat(latestData.net_profit_loss.replace(/,/g, '')) || null,
        //   earnings_per_share: parseFloat(latestData.earnings_per_share.replace(/,/g, '')) || null,
        // };
        
        // results.push(cleanedData);

        results.push({ ticker, ...latestData });

        console.log(`✅ Successfully scraped ${ticker}`);

      } catch (err) {
        console.error(`❌ Failed to scrape ${ticker}: ${err.message}`);
        failedTickers.push(ticker);
      }
    }

    return { results, failedTickers };

  } catch (err) {
    console.error("Error scraping:", err.message);
    throw err;
  } finally {
    await browser.close();
  }
}

// === Main ===
(async () => {
  const tickers = readTickersFromExcel();

  if (tickers.length === 0) {
    console.log("⚠️ No tickers found in tickers.xlsx");
    process.exit(1);
  }

  try {
    const { results, failedTickers } = await scrapeFinancials(tickers);

    // Save JSON
    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
    console.log("✅ Saved output to output.json");

    // Convert JSON to CSV and save
    const fields = ['ticker', 'quarter_ended', 'total_income', 'net_profit_loss', 'earnings_per_share'];
    const parser = new Parser({ fields });
    const csv = parser.parse(results);
    fs.writeFileSync('output.csv', csv);
    console.log("✅ Saved output to output.csv");

    // Log failed tickers if any
    if (failedTickers.length > 0) {
      fs.writeFileSync('failed_tickers.log', failedTickers.join('\n'));
      console.warn(`⚠️ Some tickers failed to scrape. See failed_tickers.log`);
    }

  } catch (err) {
    console.error("Fatal error during scraping process:", err.message);
    process.exit(1);
  }
})();
