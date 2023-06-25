import cv2 as cv;
import numpy as np;
from sympy import Polygon, Point
from deskew import determine_skew
import pathlib
import eel
import warnings
from config import aws_config as config
import boto3
import re
import pandas as pd
import dateutil.parser
import concurrent.futures
import time
import sys

class ReceiptScanner:
    def __init__(self):
        self.correspondence = {};
        self.receipts = pathlib.Path(".") / 'web'/ 'images' / 'parsed_receipts';
        self.date_patterns = ["[0,1]*[0-9]\\/[0-3][0-9]\\/[0-9]{4}","[0,1]*[0-9]\\/[0-3][0-9]\\/[0-9]{2}"]
        self.time_patterns = ["\d+\:\d+\:*\d*\s*\D{2}","\d+\:\d+\:*\d*"];
        self.card_patterns = ["CARD\W+\s*\S*\d{4}","VISA\W+\d{4}","ACCOUNT\W+\d{4}","[X]{4}\s*[X]{4}\s*[X]{4}\s*\d{4}"]
        self.total_patterns = ["TOTAL\W*\d+[.]\d{2}","PAYMENT\s*AMOUNT\s*\d+[.]\d{2}", "USD\s*[$]\s*\d+[.]\d{2}","BALANCE\s*\d+[.]\d{2}"]
        self.preferences = {
                        "file_path": str(pathlib.Path.home()),
                        "count_duplicates": False,
                        "printerIP" : ""
        }
        self.client = boto3.client("rekognition",
                                    aws_access_key_id=config.ACCESS_KEY,
                                    aws_secret_access_key=config.SECRET_KEY,
                                    region_name=config.REGION)
        self.NO_HIGHLIGHT = {"width": 0, "height": 0, "top": 0, "left": 0, "value": ""};
        self.error_messages = {
            "Duplicate":[],
            "NO AWS": False,
            "Date": [],
            "Time": [],
            "Card": [],
            "Total":[]
            };
        if(sys.platform == "darwin"):
            self.os_constant = "/"
        else:
            self.os_constant = "\\"
        self.errors_exist = False;
    def parse_receipts(self, file_paths,counter=0):
        self.error_messages = {
            "Duplicate":[],
            "NO AWS": False,
            "Date": [],
            "Time": [],
            "Card": [],
            "Total":[]
            };
        for receipt in self.receipts.iterdir():
            receipt.unlink();
        self.correspondence = {};
        #get unread receipts
        images = [];
        for path in file_paths:
            if("%20" in path):
                path = path.replace("%20"," ");
            if(sys.platform == "darwin"):
                path = str(pathlib.PurePath("/"+path));
            else:
                path = str(pathlib.PurePath(path));
            images.append(cv.imread(path));
            self.correspondence[path[path.rfind(self.os_constant)+1:]] = [];
        #len(images) > 0
        if(images):
            child_parentImage = {};
            for i, image in enumerate(images):
                iwidth , iheight = image.shape[:2]
                gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
                blur = cv.blur(gray,(5,5))
                ret, mask = cv.threshold(blur,175,255,cv.THRESH_BINARY)
                contours, hieracrhy = cv.findContours(mask,cv.RETR_EXTERNAL ,cv.CHAIN_APPROX_NONE)
                # cv.drawContours(image, contours,-1,(0,0,255),thickness=5)
                sort = sorted(contours, key=lambda element: len(element),reverse=True)
                eel.progress_bar(i+.2)
                filtered = [];
                #cleanup
                for index in range(0,len(sort)):
                    rect = cv.minAreaRect(sort[index]);
                    box = cv.boxPoints(rect);
                    box = np.intp(box);
                    quad = Polygon(box[0],box[1],box[2],box[3])
                    if(type(quad) == type(Polygon(Point(1,2),Point(3,2),Point(3,6),Point(1,6)))):
                        if(quad.area > iwidth*iheight*.95):
                            pass
                        else:
                            # if(check(quad,copy,index)):
                            #has to be greater than 10% of the image area
                            if(quad.area > iwidth*iheight*.10):
                                # print(sort[index][:10])
                                filtered.append(sort[index])


                eel.progress_bar(i+.4)

                seperate_images = [];
                rotate = [];
                for index, cnt in enumerate(filtered):
                    rect = cv.minAreaRect(cnt)
                    # print(rect[0])
                    rotate.append([rect[0],rect[2],rect[1]])
                    box = cv.boxPoints(rect)
                    box = np.intp(box)
                    seperate_images.append(np.zeros(image.shape[:2],dtype="uint8"))
                    cv.drawContours(seperate_images[index],[box],0,255,-1)
                    cv.drawContours(image,[box],0,(0,255,0),thickness=5)
                eel.progress_bar(i+.6)
                receipts = []
                for index, seperate in enumerate(seperate_images):
                    receipt = cv.bitwise_and(seperate, gray)
                    center_point = (image.shape[1]//2,image.shape[0]//2)
                    shift_x = center_point[0] - rotate[index][0][0]
                    shift_y = center_point[1] - rotate[index][0][1]
                    trans_mat = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
                    receipt = cv.warpAffine(receipt,trans_mat,(image.shape[1],image.shape[0]))
                    if(abs(rotate[index][1])  <= 45):
                        rot_mat = cv.getRotationMatrix2D(center_point,rotate[index][1],1.0)
                    else:
                        rot_mat = cv.getRotationMatrix2D(center_point,rotate[index][1]-90,1.0)
                    receipt = cv.warpAffine(receipt, rot_mat,(image.shape[1],image.shape[0]))
                    if(rotate[index][2][0] > rotate[index][2][1]):
                        h = int(rotate[index][2][0]//2)
                        w = int(rotate[index][2][1]//2)
                    else:
                        w = int(rotate[index][2][0]//2)
                        h = int(rotate[index][2][1]//2)
                    y = center_point[1]-h 
                    x = center_point[0]-w
                    x1 = center_point[0]+w
                    y1 = center_point[1]+h
                    if(x < 0):
                        x =0;
                    if(y< 0):
                        y = 0
                    
                    cropped = receipt[y: y1, x:x1]
                    receipts.append(cropped);
                eel.progress_bar(i+.8)
                #deskew and finalize image
                for index, receipt in enumerate(receipts):
                    angle = determine_skew(receipt);
                    center_point = (receipt.shape[0]//2,receipt.shape[1]//2)
                    rot_mat = cv.getRotationMatrix2D(center=center_point,angle=angle,scale=1.0);
                    rotated = cv.warpAffine(receipt,rot_mat,(receipt.shape[1],receipt.shape[0]))
                    ret, mask = cv.threshold(rotated,190,255,cv.THRESH_BINARY)
                    pth = self.receipts / ("receipt"+str(counter)+".jpg");
                    cv.imwrite(str(pth),mask);
                    child_parentImage["receipt"+str(counter)+".jpg"] = file_paths[i][file_paths[i].rfind("/")+1:]
                    counter += 1;
            # multiprocessing
            start = time.perf_counter();
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for image, result in zip(
                    self.receipts.iterdir(), 
                    executor.map(
                        lambda image: self.client.detect_text(Image={'Bytes': image.read_bytes()}),
                        self.receipts.iterdir()
                    )
                ):
                    key = str(image)[str(image).rfind(self.os_constant)+1:];        
                    detections = result["TextDetections"];
                    string = '';
                    bounding_boxes = {};
                    for detection in detections:
                        textType = detection["Type"]
                        text = detection["DetectedText"]
                        bounding_boxes[text] = detection["Geometry"]["BoundingBox"];
                        if(textType.lower() == "line"):
                            string += text + "\n";
                    dates = [];
                    box_keys = list(bounding_boxes.keys());
                    datetime_date = {};
                    for x, pattern in enumerate(self.date_patterns):
                        pos_dates = re.findall(pattern,string)
                        if(len(pos_dates) != 0 ):
                            for date in pos_dates:
                                datetime_obj = dateutil.parser.parse(date);
                                if(date in box_keys):
                                    datetime_date[datetime_obj] = date;
                                    dates.append(datetime_obj);
                    receipt_dict = {}
                    if(dates):
                        value = max(set(dates), key=dates.count);
                        bounding_boxes[datetime_date[value]]["value"] = value.strftime("%Y-%m-%d")
                        receipt_dict["Date"] = bounding_boxes[datetime_date[value]];
                    else:
                        receipt_dict["Date"] = self.NO_HIGHLIGHT;
                        self.error_messages["Date"].append(key[:-4]);
                    times = [];
                    am_pm = False;
                    for pattern in self.time_patterns:
                        pos_times = re.findall(pattern, string);
                        if(len(pos_times) != 0):
                            for t in pos_times:
                                if("am" in t.lower() or "pm" in t.lower()):
                                    times.append(t);
                                    am_pm = True;
                                elif(not am_pm):
                                    times.append(t);
                    if(times):
                        hour = max(set(times), key=times.count);
                        if(am_pm):
                            # should give us "PM" OR "AM"
                            mm = hour[-2:]
                            if(mm in box_keys):
                                bounding_boxes[hour.replace(" ", "")[:-2]]["Width"] = bounding_boxes[hour.replace(" ", "")[:-2]]["Width"] + bounding_boxes[mm]["Width"] + (bounding_boxes[mm]["Left"]-(bounding_boxes[hour.replace(" ", "")[:-2]]["Left"]+bounding_boxes[hour.replace(" ", "")[:-2]]["Width"]));
                        
                        bounding_boxes[hour.replace(" ", "")[:-2]]["value"] = dateutil.parser.parse(hour).strftime("%H:%M:%S");
                        receipt_dict["Time"] = bounding_boxes[hour.replace(" ", "")[:-2]];
                    else:
                        receipt_dict["Time"] = self.NO_HIGHLIGHT;
                        self.error_messages["Time"].append(key[:-4]);
                    
                    if(
                        re.search("FUEL", string.upper()) != None 
                        or re.search("PUMP#\s*\d+", string.upper()) != None
                    ):
                        receipt_dict["Type"] = "GAS";
                    elif(
                        re.search("HOME\s*DEPOT",string.upper()) != None 
                        or re.search("HOW\s*DOERS\s*GET\s*MORE\s*DONE",string.upper()) != None
                    ):
                        receipt_dict["Type"] = "MATERIALS";
                    elif(re.search("OFFICE",string.upper())!= None 
                    ):
                        receipt_dict["Type"] = "OFFICE SUPPLIES";
                    elif(re.search("GROCERY",string.upper())!= None):
                        receipt_dict["Type"] = "GROCERIES";
                    else:
                        receipt_dict["Type"] = "";
                    
                    cards = [];
                    str_cards = [];
                    for pattern in self.card_patterns:
                        pos_cards = re.findall(pattern,string.upper())
                        if(len(pos_cards) != 0):
                            for card in pos_cards:
                                if(card not in cards):
                                    str_cards.append(card);
                                    cards.append(card[-4:]);
                    if(cards):
                        card = max(set(cards), key=cards.count);
                        bounding_boxes[str_cards[cards.index(card)]]["value"] = int(card);
                        receipt_dict["Card"] = bounding_boxes[str_cards[cards.index(card)]];
                    else:
                        receipt_dict["Card"] = self.NO_HIGHLIGHT;
                        self.error_messages["Card"].append(key[:-4]);

                    totals = [];
                    numbers = [];
                    for pattern in self.total_patterns:
                        pos_total = re.findall(pattern,string.upper())
                        for total in pos_total:
                            totals.append(total);
                            str_number = '';
                            for char in total:
                                if(char.isdigit()):
                                    str_number += char;
                            numbers.append(int(str_number)/100);
                    if(numbers):
                        total = totals[numbers.index(max(numbers))].split();
                        bounding_boxes[total[-1]]["value"] = max(numbers);
                        receipt_dict["Total"] = bounding_boxes[total[-1]];
                    else:
                        receipt_dict = self.NO_HIGHLIGHT;
                        self.error_messages["Total"].append(key[:-4]);
                    self.correspondence[child_parentImage[key]].append({key[:-4] : receipt_dict});
            print(f"Multiprocessing takes {time.perf_counter() - start} seconds to complete!")
        #if we encountered any errors send them
        for key in self.error_messages:
            if(self.error_messages[key]):
                self.errors_exist = True;
                break;
        eel.progress_bar(i+1);


    def amazon_ocr(self, path, data, check_duplicate=False):
        expenses_folder = path / "expenses";
        excel_files = [];
        self.error_messages = {
            "Duplicate": []
        };
        # see if the expesnes file exists 
        if(expenses_folder.exists()):
            excel_files = sorted(list(expenses_folder.glob("*.xlsx")));
            #check to see if excel file is already opened
            for file in excel_files:
                try:
                    with open(file, "r") as file:
                        pass;
                except IOError:
                    file_name = re.findall("\d+expenses[.]xlsx",str(file))[0];
                    error ={
                        "Open Excel": True,
                        "filename": file_name
                    }
                    eel.error_message(error);
                    return;
        # otherwise create a new one
        else:
            expenses_folder.mkdir();
        # change data into readable expense dictionary
        expense = { 
                "Filename": data["filename"],
                "DateTime": [],
                "Type": [],
                "Card": [],
                "Total": []
        };
        for index in range(len(data["filename"])):
            # date + time
            if(data['date'][index] == '' or data['date'][index] == None):
                eel.error_message({"Exists": True, 
                "message": f"{data['filename'][index][data['filename'][index].rfind('/')+1:-4]} doesn't have a date!"});
                eel.disable_convert();
                return;
            elif(data['time'][index] == '' or data['time'][index] == None):
                eel.error_message({"Exists": True, 
                "message": f"{data['filename'][index][data['filename'][index].rfind('/')+1:-4]} doesn't have a time!"})
                eel.disable_convert();
                return;
            else:
                datetime = dateutil.parser.parse(data["date"][index] +" "+ data["time"][index]);
                expense["DateTime"].append(datetime);
            # make sure the value in type is all uppercase
            if(data["type"][index] == ""):
                expense["Type"].append(None);
            else:
                expense["Type"].append(data["type"][index].upper());
            # change card and Total to number not string
            if(data["card"][index] == ''):
                expense["Card"].append(None);
            else:
                expense["Card"].append(int(data["card"][index]));
            if(data["total"][index] == ''):
                expense["Total"].append(None);
            else:
                # cant cast to int must cast to float ):(makes sense tho)
                expense["Total"].append(float(data["total"][index]));
        # check for old data
        if excel_files:
            df = pd.concat(pd.read_excel(excel_files[0], index_col=0, parse_dates=["DateTime"],date_format="%m/%d/%y %I:%M:%S %p",sheet_name=None),ignore_index=True);
            for excel_file in excel_files[1:]:
                df = pd.concat([df,pd.concat(pd.read_excel(path / excel_file, index_col=0, 
                                parse_dates=["DateTime"],date_format="%m/%d/%y %I:%M:%S %p",sheet_name=None),
                                ignore_index=True)],
                            ignore_index=True); 
        # create new dataframe
        else:
            df = pd.DataFrame()

        if(len(expense["DateTime"]) > 0):
            database = pd.DataFrame(expense);
            if(check_duplicate):
                df = pd.concat([df, database], ignore_index=True);
            else:
                for index in database.index:
                    df = pd.concat([df, database.loc[[index]]], ignore_index=True)
                    drop_col = df.drop(columns=["Filename"])
                    if(not drop_col.equals(df.drop(columns=["Filename"]).drop_duplicates())):
                        string = str(database["Filename"][index])
                        self.error_messages["Duplicate"].append(re.findall("receipt\d+",string)[0]);
                        df.drop(df.tail(1).index, inplace=True);
                if(self.error_messages["Duplicate"]):
                    eel.error_message(self.error_messages);
            df.sort_values(by="DateTime",inplace=True,ignore_index=True,na_position="first");
            for index, (y, year_df) in enumerate(df.groupby(pd.Grouper(key="DateTime", freq="Y"))):
                excel_name = (y.strftime('%Y')+"expenses.xlsx")
                # DEBUG: datetime_format and date_format parameters do not work when using openpyxl as the engin
                # See here for reference: https://github.com/pandas-dev/pandas/issues/44284
                # NOTE: Using mode 'a' doesn't work if file is completely empty, for example
                # after creating the file using .touch() (pathlib)
                # TODO: File issue on GitHub
                params = {
                        'mode': 'w',
                        'if_sheet_exists': None
                    }
                if(excel_files):
                    if excel_files[index].exists() and excel_files[index].stat().st_size != 0:
                        params = {
                            'mode': 'a',
                            'if_sheet_exists': 'replace'
                        }
                with warnings.catch_warnings(), pd.ExcelWriter(expenses_folder / excel_name, engine='openpyxl', **params) as writer:
                    warnings.simplefilter(action='ignore')
                    # for index, (_, group_df) in enumerate(combined_df.groupby(pd.Grouper(key='DateTime', freq='M'))):
                    for (_, group_df) in year_df.groupby(pd.Grouper(key='DateTime', freq='M')):
                        datetime_str = group_df['DateTime'].dt.strftime('%m/%d/%y %I:%M:%S %p')
                        group_df['DateTime'] = datetime_str
                        group_df.to_excel(writer, sheet_name=_.strftime("%B"))
    def autoscan(self):
        print("Auto Scan...")
    