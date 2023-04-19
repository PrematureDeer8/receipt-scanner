import eel
import tkinter
from tkinter import filedialog
import cv2 as cv;
import re;
import os
from parse_receipts import parse_receipts
from amazon_ocr import amazon_ocr


pattern = re.compile(r"[\w,-]+.jpg")

eel.init("web");

@eel.expose
def windowfilepicker():
    for file in os.listdir("web/images/scanned_receipts"):
        os.remove("web/images/scanned_receipts/{}".format(file))
    tkinter.Tk().withdraw(); # prevents an empty tkinter window from appearing
    file_paths = list(filedialog.askopenfilenames());
    #use os.replace instead
    file_names = [];
    for index, path in enumerate(file_paths):
        image_mat = cv.imread(path);
        file_names.append(pattern.findall(path)[0])
        cv.imwrite("web/images/scanned_receipts/{}".format(file_names[index]),image_mat);
    eel.display_images(file_names);

@eel.expose
def parse():
    directory="web/images/parsed_receipts/";
    for file in os.listdir(directory):
        os.remove(directory+file)
    images = parse_receipts();
    eel.display_parsed_images(images);

@eel.expose
def ocr():
    # os.remove("expenses.xlsx")
    amazon_ocr();
    # print("done")

eel.start("index.html");