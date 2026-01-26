/**
 * Momentum Phinance - Google Sheets Scanner Integration
 * 
 * SETUP:
 * 1. In your Google Sheet: Extensions > Apps Script
 * 2. Paste this code
 * 3. Deploy > New deployment > Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 4. Copy the Web App URL to your .env as GOOGLE_SHEETS_WEBHOOK
 * 
 * FEATURES:
 * - Auto-creates tabs per strategy name
 * - Dynamic columns (sends whatever the scanner produces)
 * - Adds CurrentPrice column with GOOGLEFINANCE formula
 * - Dark header styling
 */

function doPost(e) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const rawData = JSON.parse(e.postData.contents);
    const data = rawData.data;
    const timestamp = rawData.timestamp;

    // Use strategy name for the tab, sanitized
    let strategyName = rawData.strategy || "Scanner Results";
    strategyName = strategyName.substring(0, 100).replace(/[\/\\?*\[\]]/g, '_');

    if (!data || data.length === 0) {
        return ContentService.createTextOutput(JSON.stringify({ status: "no data" }));
    }

    // Get or Create Sheet (Tab)
    let sheet = ss.getSheetByName(strategyName);
    if (!sheet) {
        sheet = ss.insertSheet(strategyName);
    }

    // Get headers dynamically from the first data object
    const keys = Object.keys(data[0]);

    // Setup Headers if sheet is empty
    if (sheet.getLastRow() === 0) {
        const headers = ["ScanTime", ...keys, "CurrentPrice"];
        sheet.appendRow(headers);

        // Style header row
        const headerRange = sheet.getRange(1, 1, 1, headers.length);
        headerRange.setFontWeight("bold");
        headerRange.setBackground("#1f2937");
        headerRange.setFontColor("#ffffff");
        sheet.setFrozenRows(1);

        // Auto-resize columns for readability
        for (let i = 1; i <= headers.length; i++) {
            sheet.autoResizeColumn(i);
        }
    }

    // Map data to rows
    const newRows = data.map(item => {
        const row = [timestamp];
        keys.forEach(key => {
            let val = item[key];
            // Handle null/undefined
            if (val === null || val === undefined) {
                val = "";
            }
            row.push(val);
        });
        return row;
    });

    // Append rows
    if (newRows.length > 0) {
        const startRow = sheet.getLastRow() + 1;
        sheet.getRange(startRow, 1, newRows.length, newRows[0].length).setValues(newRows);

        // Add GOOGLEFINANCE formula for CurrentPrice
        // Symbol is column 2 (after ScanTime)
        const priceColIndex = newRows[0].length + 1;
        const formulas = newRows.map((_, i) => {
            return [`=IFERROR(GOOGLEFINANCE(B${startRow + i},"price"),"")`];
        });
        sheet.getRange(startRow, priceColIndex, newRows.length, 1).setFormulas(formulas);
    }

    return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        rows: newRows.length,
        sheet: strategyName,
        columns: keys.length
    }));
}

/**
 * Test function - run manually to verify deployment
 */
function testDoPost() {
    const mockData = {
        postData: {
            contents: JSON.stringify({
                data: [
                    { Symbol: "TEST", Company: "Test Corp", close: 100.50, IV: "25%" },
                    { Symbol: "DEMO", Company: "Demo Inc", close: 50.25, IV: "30%" }
                ],
                timestamp: new Date().toISOString(),
                strategy: "Test Strategy"
            })
        }
    };

    const result = doPost(mockData);
    Logger.log(result.getContent());
}
