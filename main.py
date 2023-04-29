import eel
import tkinter
from tkinter import filedialog
import cv2 as cv;
import re;
import os
from parse_receipts import parse_receipts
from amazon_ocr import amazon_ocr

pattern = re.compile(r"[\w,-]+.jpg|[\w,-]+.png|[\w,-]+.pdf")
file_types = [".jpg",".png",".pdf"]

eel.init("web");

@eel.expose
def windowfilepicker():
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
            file_paths.remove(path);
            message = str(path) + " is not a correct image file!";
            if(len(file_paths)):
                message += "\nPreceeding with other files.";
            eel.error_message(message);
    if(file_paths):
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
    eel.reable_browse();

@eel.expose
def parse():
    correspondence = parse_receipts();
    eel.display_parsed_images(correspondence);
    eel.enable_convert();

@eel.expose
def ocr():
    # os.remove("expenses.xlsx")
    amazon_ocr();
    eel.reable_excel_button();    

eel.start("index.html");