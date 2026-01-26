# Batch Scanner Template

A template for running stock screening strategies in batch and exporting results to Google Sheets.

## Features

- Run multiple screening strategies sequentially
- Export results to Google Sheets (one tab per strategy)
- CLI options for dry-run, strategy selection
- Cron-ready for scheduled scans

---

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas requests python-dotenv
# Add your screener library (e.g., tradingview-screener, yfinance, etc.)
```

### 2. Create `.env` File

```bash
GOOGLE_SHEETS_WEBHOOK=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

### 3. Deploy Google Apps Script

1. Create a new Google Sheet
2. **Extensions → Apps Script**
3. Paste the Apps Script code (see `google_sheets_script.js`)
4. **Deploy → New Deployment → Web App**
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Copy Web App URL to `.env`

### 4. Define Your Strategies

Edit `batch_scanner_template.py`:

```python
def my_momentum_screen():
    """Your custom screening logic."""
    from tradingview_screener import Query, col
    
    query = (
        Query()
        .select('name', 'close', 'volume', 'change')
        .where(
            col('volume') > 1_000_000,
            col('close') > 10
        )
        .limit(50)
    )
    count, df = query.get_scanner_data()
    return df

STRATEGIES = [
    {
        "name": "My Momentum Screen",
        "query_fn": my_momentum_screen,
        "priority_cols": ["close", "volume", "change"],
    },
]
```

---

## Usage

```bash
# Run all strategies
python batch_scanner_template.py

# Dry run (print only, don't send)
python batch_scanner_template.py --dry-run

# Run specific strategies
python batch_scanner_template.py --strategies "Strategy A,Strategy B"

# List available strategies
python batch_scanner_template.py --list
```

---

## Cron Scheduling

Daily at 4:00 PM (market close):

```bash
0 16 * * 1-5 cd /path/to/project && python batch_scanner_template.py >> logs/batch.log 2>&1
```

---

## Google Sheets Output

Each strategy creates its own tab with:

| Column | Description |
|--------|-------------|
| ScanTime | When the scan ran |
| Symbol | Ticker symbol |
| Company | Company name |
| WeekEnding | Week ending date (for filtering) |
| *strategy columns* | Your custom columns |
| CurrentPrice | Live price (via GOOGLEFINANCE) |

---

## Apps Script (google_sheets_script.js)

```javascript
function doPost(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawData = JSON.parse(e.postData.contents);
  const data = rawData.data;
  const timestamp = rawData.timestamp;
  const strategyName = rawData.strategy || "Scanner Results";

  if (!data || data.length === 0) {
    return ContentService.createTextOutput(JSON.stringify({ status: "no data" }));
  }

  // Get or create sheet tab
  let sheet = ss.getSheetByName(strategyName);
  if (!sheet) {
    sheet = ss.insertSheet(strategyName);
  }

  // Dynamic headers from first row
  const keys = Object.keys(data[0]);
  
  if (sheet.getLastRow() === 0) {
    const headers = ["ScanTime", ...keys, "CurrentPrice"];
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  }

  // Append data rows
  const newRows = data.map(item => {
    const row = [timestamp];
    keys.forEach(key => row.push(item[key] ?? ""));
    return row;
  });

  if (newRows.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow, 1, newRows.length, newRows[0].length).setValues(newRows);
    
    // Add GOOGLEFINANCE formula for live price
    const formulas = newRows.map((_, i) => [`=IFERROR(GOOGLEFINANCE(B${startRow + i},"price"),"")`]);
    sheet.getRange(startRow, newRows[0].length + 1, newRows.length, 1).setFormulas(formulas);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: "success", rows: newRows.length }));
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GOOGLE_SHEETS_WEBHOOK not configured" | Create `.env` with your webhook URL |
| "Sheets error: 302" | Redeploy Apps Script with "Anyone" access |
| Empty results | Check your strategy query logic |
