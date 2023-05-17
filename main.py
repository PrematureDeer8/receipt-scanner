import eel
import tkinter
from tkinter import filedialog
import cv2 as cv;
import re;
import os
from parse_receipts import parse_receipts
from amazon_ocr import amazon_ocr
import pathlib

pattern = re.compile(r"[\w,-]+.jpg|[\w,-]+.png|[\w,-]+.pdf")
file_types = [".jpg",".png",".pdf"]
DEFAULT_PATH = list(pathlib.Path.home().glob("*/Desktop"))[0]

eel.init("web");

@eel.expose
def windowfilepicker():
    error = {
        "Exists": False,
        "message": "",
        "delete": []
    }
    directory="web/images/parsed_receipts/";
    tkinter.Tk().withdraw(); # prevents an empty tkinter window from appearing
    file_paths = list(filedialog.askopenfilenames());
    for path in file_paths:
        counter = 0;
        for type in file_types:
            if(type in path):
                break;
            else:
                counter += 1;
        #path is not a valid image type
        if(counter == len(file_types)):
            error["delete"].append(path);
            error["Exists"] = True;
            error["message"] += str(re.findall("[\w\s-]+[.]\w+",str(path))[0]) +", ";
    error["message"] += " is not an image!";
    for delete in error["delete"]:
        file_paths.remove(delete);
    if(file_paths):
        error["message"] += "\n Proceding with other files.";
        for file in os.listdir(directory):
            os.remove(directory+file)
        for file in os.listdir("web/images/scanned_receipts"):
            os.remove("web/images/scanned_receipts/{}".format(file))
        #use os.replace instead
        file_names = [];
        for index, path in enumerate(file_paths):
            image_mat = cv.imread(path);
            file_names.append(pattern.findall(path)[0])
            cv.imwrite("web/images/scanned_receipts/{}".format(file_names[index]),image_mat);
        eel.display_images(file_names);
    if(error["Exists"]):
        eel.error_message(error);
    eel.reable_browse();

@eel.expose
def parse():
    correspondence = parse_receipts();
    eel.display_parsed_images(correspondence);
    eel.enable_convert();

@eel.expose
def ocr():
    error = {
        "Exists": False
    }
    p = eel.get_path()();
    checked = eel.count_duplicates()();
    path = pathlib.Path(p)
    exists = path.exists()
    if(exists and str(p) != ""):
        amazon_ocr(path=path,check=checked);
    else:
        if(not exists):
            error["Exists"] = True;
            error["message"] = f"Path {p} does not exists! Proceding with default path."
            eel.error_message(error)
        amazon_ocr(check=checked);
    eel.reable_excel_button(); 
@eel.expose
def default_file_path():
    return str(DEFAULT_PATH)

eel.start("index.html");