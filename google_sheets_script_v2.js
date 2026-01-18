function doPost(e) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const rawData = JSON.parse(e.postData.contents);
    const data = rawData.data; // Array of objects
    const timestamp = rawData.timestamp;

    // Use strategy name for the tab, or default if missing
    // Clean name to be safe (max 100 chars, no invalid chars)
    let strategyName = rawData.strategy || "Scanner Results";
    strategyName = strategyName.substring(0, 100);

    if (!data || data.length === 0) {
        return ContentService.createTextOutput(JSON.stringify({ status: "no data" }));
    }

    // 1. Get or Create Sheet (Tab)
    let sheet = ss.getSheetByName(strategyName);
    if (!sheet) {
        sheet = ss.insertSheet(strategyName);
    }

    // 2. Get headers (dynamic)
    const keys = Object.keys(data[0]);

    // 3. Setup Headers if sheet is empty
    if (sheet.getLastRow() === 0) {
        const headers = ["Scan Time", ...keys];
        sheet.appendRow(headers);
        sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#d9d9d9");
        sheet.setFrozenRows(1);
    }

    // 4. Map the data to rows
    const newRows = data.map(item => {
        const row = [timestamp];
        keys.forEach(key => {
            row.push(item[key]);
        });
        return row;
    });

    // 5. Append all rows
    if (newRows.length > 0) {
        const startRow = sheet.getLastRow() + 1;
        sheet.getRange(startRow, 1, newRows.length, newRows[0].length).setValues(newRows);

        // 6. Add GOOGLEFINANCE formula for CurrentPrice column
        // Find the Symbol column index (should be column 2, after Scan Time)
        const symbolColIndex = 2; // Symbol is the first data column after timestamp
        const numCols = newRows[0].length;

        // Add header for CurrentPrice if not present (next column after data)
        const headerRow = sheet.getRange(1, 1, 1, numCols + 1).getValues()[0];
        if (headerRow[numCols] !== 'CurrentPrice') {
            sheet.getRange(1, numCols + 1).setValue('CurrentPrice').setFontWeight('bold').setBackground('#d9d9d9');
        }

        // Add GOOGLEFINANCE formulas for each new row
        const formulas = [];
        for (let i = 0; i < newRows.length; i++) {
            // Formula references the Symbol cell in the same row
            formulas.push([`=IFERROR(GOOGLEFINANCE(B${startRow + i},"price"),"")`]);
        }
        sheet.getRange(startRow, numCols + 1, newRows.length, 1).setFormulas(formulas);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: "success", rows: newRows.length, sheet: strategyName }));
}
