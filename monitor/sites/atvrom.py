// CONFIGURARE
// Asigură-te că link-ul este cel corect
var FEED_URL = "https://www.atvrom.ro/storage/feed/vehicleFeed.xml"; 
var SHEET_NAME = "DateFeed_ATV"; // Numele foii unde scriem datele

function importXmlToSheet() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(SHEET_NAME);
  
  // Dacă foaia nu există, o creăm
  if (!sheet) {
    sheet = spreadsheet.insertSheet(SHEET_NAME);
  }
  
  // 1. Preluăm conținutul XML
  // Folosim un User-Agent de browser pentru a nu fi blocați de server
  var options = {
    "method": "get",
    "headers": {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "muteHttpExceptions": true
  };
  
  try {
    var response = UrlFetchApp.fetch(FEED_URL, options);
    
    if (response.getResponseCode() !== 200) {
      Logger.log("Eroare HTTP: " + response.getResponseCode());
      Browser.msgBox("Eroare la descărcare. Cod: " + response.getResponseCode());
      return;
    }
    
    var xmlContent = response.getContentText();
    
    // 2. Parsăm XML-ul folosind funcția dedicată structurii tale
    var items = parseMyXml(xmlContent);
    
    if (!items || items.length === 0) {
      Browser.msgBox("Nu s-au găsit produse (iteme) în feed.");
      return;
    }

    // 3. Scriem datele în Google Sheet
    sheet.clear(); // Ștergem tot conținutul vechi pentru a nu suprapune date
    
    // Definim coloanele exact așa cum apar în XML-ul tău
    var headers = [
      "id", 
      "title", 
      "description", 
      "link", 
      "image_link", 
      "images", 
      "brand", 
      "price", 
      "price_ron", 
      "sale_price", 
      "sale_price_ron", 
      "categories", 
      "category", 
      "attributes"
    ];
    
    // Scriem antetul (Primul rând)
    sheet.getRange(1, 1, 1, headers.length)
         .setValues([headers])
         .setFontWeight("bold")
         .setBackground("#e0e0e0"); // Un gri deschis pentru header
    
    // Pregătim datele pentru scriere
    var rows = items.map(function(item) {
      return headers.map(function(header) {
        // Returnăm valoarea din obiect sau un string gol dacă lipsește
        return item[header] || ""; 
      });
    });
    
    // Scriem toate rândurile deodată (Bulk write) - este mult mai rapid
    if (rows.length > 0) {
      sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
      Logger.log("Succes! Au fost importate " + rows.length + " produse.");
    }
    
    // Înghețăm primul rând (header-ul)
    sheet.setFrozenRows(1);

  } catch (e) {
    Logger.log("Eroare: " + e.toString());
    Browser.msgBox("A apărut o eroare: " + e.toString());
  }
}

/**
 * Funcție personalizată pentru structura:
 * <products>
 * <script.../> (trebuie ignorat)
 * <item>...</item>
 * </products>
 */
function parseMyXml(xmlText) {
  try {
    // Curățăm spațiile goale de la început care pot da erori de parsare
    xmlText = xmlText.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
    
    var document = XmlService.parse(xmlText);
    var root = document.getRootElement(); // Acesta este tag-ul <products>
    
    // Metoda getChildren("item") este perfectă aici deoarece:
    // 1. Caută doar copiii direcți ai lui <products>
    // 2. Selectează DOAR tag-urile <item>, ignorând automat tag-ul <script> sau altele
    var xmlItems = root.getChildren("item");

    var jsonList = [];
    
    // Lista câmpurilor pe care le căutăm în fiecare item
    var fields = [
      "id", "title", "description", "link", "image_link", "images", 
      "brand", "price", "price_ron", "sale_price", "sale_price_ron", 
      "categories", "category", "attributes"
    ];
    
    for (var i = 0; i < xmlItems.length; i++) {
      var xmlItem = xmlItems[i];
      var itemObj = {};
      
      // Extragem textul pentru fiecare câmp definit
      fields.forEach(function(field) {
        var element = xmlItem.getChild(field);
        if (element) {
          itemObj[field] = element.getText();
        } else {
          itemObj[field] = ""; // Dacă câmpul lipsește din XML, punem gol
        }
      });
      
      jsonList.push(itemObj);
    }
    
    return jsonList;
    
  } catch (e) {
    Logger.log("Eroare la parsarea XML: " + e.toString());
    throw e;
  }
}
