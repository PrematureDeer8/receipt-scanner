from gevent import monkey
monkey.patch_all();
import eel
import eel.browsers
import re
import pathlib
import sys
import json
from ReceiptScanner import ReceiptScanner
import sys

if(sys.platform == "darwin"):
    eel.browsers.set_path('electron', 'node_modules/electron/dist/Electron.app/Contents/MacOS/Electron');
    local = pathlib.Path.home() / "Library" / "Preferences";
else:
    eel.browsers.set_path('electron', 'node_modules/electron/dist/electron');
    local = pathlib.Path.home() / "AppData" / "Local";  
receipt_folder = local / "receipt-scanner";
pattern = re.compile(r"[\w,-]+.jpg|[\w,-]+.png|[\w,-]+.pdf");
scanner = ReceiptScanner();
if(receipt_folder.exists()):
    pref_file = receipt_folder / "pref.json";
    with open(pref_file, "r") as f:
        scanner.preferences = json.load(f);
def store_preferences(page, web_sockets):
    if(local.exists()):
        if(not receipt_folder.exists()):
            receipt_folder.mkdir();
        pref_file = receipt_folder / "pref.json"
        with open(pref_file, "w") as f:
            json.dump(scanner.preferences, f,indent=4);
    sys.exit()



eel.init("web");
@eel.expose
def updateperferences(file_path, count_duplicates):
    scanner.preferences["file_path"] = file_path;
    scanner.preferences["count_duplicates"] = count_duplicates;

@eel.expose
def parse(file_paths):
    scanner.parse_receipts(file_paths);
    eel.display_parsed_images(scanner.correspondence);
    if(scanner.errors_exist):
        print(scanner.error_messages)
        eel.error_message(scanner.error_messages);
    # eel.enable_convert();

@eel.expose
def ocr():
    error = {
        "Exists": False
    }
    path = pathlib.Path(scanner.preferences["file_path"])
    exists = path.exists()
    if(exists and str(scanner.preferences["file_path"]) != ""):
        scanner.amazon_ocr(path=path,check=scanner.preferences["count_duplicates"]);
    else:
        if(not exists):
            error["Exists"] = True;
            error["message"] = f"Path {scanner.preferences['file_path']} does not exists! Proceding with default path."
            eel.error_message(error)
        scanner.amazon_ocr(check=scanner.preferences["count_duplicates"], path=pathlib.Path.home());
    eel.reable_excel_button(); 
@eel.expose
def default_file_path():
    return scanner.preferences["file_path"]
@eel.expose
def default_count_dup():
    return scanner.preferences["count_duplicates"]

eel.start("index.html", mode="electron", close_callback=store_preferences, size=(800,600));