/* Boostyou.ai newsletter backend — Google Apps Script
   Lives in the "Boostyou subscribers" Google Sheet (Extensions → Apps Script).
   Deployed as a web app (Execute as: Me / Access: Anyone); the /exec URL is
   NEWSLETTER_ENDPOINT in assets/cta.js. This file is the tracked copy of the
   script — after editing it here, paste the new version into Apps Script and
   redeploy.

   Accepts POST with a text/plain JSON body: {"email": "...", "website": ""}
   ("website" is the honeypot — filled means bot, we pretend success).
   Appends [email, timestamp] to the Subscribers sheet, skipping duplicates.
   Always answers {"ok": true|false} as JSON. */

var SHEET_NAME = 'Subscribers';

function doPost(e) {
  var ok = false;
  try {
    var data = JSON.parse(e.postData.contents);
    var email = String(data.email || '').trim().toLowerCase();
    var honeypot = String(data.website || '').trim();

    if (honeypot) {
      ok = true; // bot: pretend success, store nothing
    } else if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      var lock = LockService.getScriptLock();
      lock.waitLock(10000);
      try {
        var ss = SpreadsheetApp.getActiveSpreadsheet();
        var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
        if (sheet.getLastRow() === 0) {
          sheet.appendRow(['Email', 'Signed up']);
          sheet.getRange('A1:B1').setFontWeight('bold');
          sheet.setFrozenRows(1);
          sheet.setColumnWidth(1, 260);
          sheet.setColumnWidth(2, 180);
        }
        var lastRow = sheet.getLastRow();
        var exists = false;
        if (lastRow > 1) {
          var rows = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
          for (var i = 0; i < rows.length; i++) {
            if (String(rows[i][0]).trim().toLowerCase() === email) { exists = true; break; }
          }
        }
        if (!exists) sheet.appendRow([email, new Date()]);
        ok = true; // duplicate signups also report success
      } finally {
        lock.releaseLock();
      }
    }
  } catch (err) {
    ok = false;
  }
  return ContentService.createTextOutput(JSON.stringify({ ok: ok }))
    .setMimeType(ContentService.MimeType.JSON);
}
