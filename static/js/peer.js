document.addEventListener('DOMContentLoaded', () => {
    const fetchPeersButton = document.getElementById('fetchPeersButton');
    const tickersInput = document.getElementById('tickersInput');
    const peersResult = document.getElementById('peersResult');

    fetchPeersButton.addEventListener('click', async () => {
        const tickers = tickersInput.value.trim();
        if (!tickers) {
            alert('Please enter at least one ticker');
            return;
        }
        peersResult.textContent = "Loading...";
        try {
            const response = await fetch(`/scrape_nse?tickers=${encodeURIComponent(tickers)}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            if (!data.length) {
                peersResult.textContent = "No data found.";
                return;
            }

            peersResult.innerHTML = generateTableFromJSON(data);
        } catch (err) {
            peersResult.textContent = `Error: ${err.message}`;
        }
    });
});

function generateTableFromJSON(data) {
    const columnsToShow = ['ticker', 'quarter_ended', 'total_income', 'net_profit_loss', 'earnings_per_share'];

    let table = '<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">';

    // Header
    table += '<thead><tr>';
    columnsToShow.forEach(key => {
        table += `<th style="border: 1px solid black; padding: 4px;">${key}</th>`;
    });
    table += '</tr></thead>';

    // Body
    table += '<tbody>';
    data.forEach(row => {
        table += '<tr>';
        columnsToShow.forEach(col => {
            table += `<td style="border: 1px solid black; padding: 4px;">${row[col] ?? ''}</td>`;
        });
        table += '</tr>';
    });
    table += '</tbody></table>';

    return table;
}
