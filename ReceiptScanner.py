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
    def parse_receipts(self, file_paths,counter=0):
        error_messages = {
            "Duplicate":[],
            "NO AWS": False};
        try:
            client = boto3.client("rekognition",
                                    aws_access_key_id=config.ACCESS_KEY,
                                    aws_secret_access_key=config.SECRET_KEY,
                                    region_name=config.REGION)
        except:
            error_messages["NO AWS"] = True;
            eel.error_message(error_messages);
            return;
        for receipt in self.receipts.iterdir():
            receipt.unlink();
        self.correspondence = {};
        #get unread receipts
        images = [];
        for path in file_paths:
            if("%20" in path):
                path = path.replace("%20"," ")
            path = str(pathlib.PurePath("/"+path));
            images.append(cv.imread(path));
            self.correspondence[path[path.rfind("/")+1:]] = [];
        #len(images) > 0
        if(images):
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
                #deskew
                for index, receipt in enumerate(receipts):
                    # cv.imshow("receipt"+str(index+1),receipt);
                    angle = determine_skew(receipt);
                    # print("Angle: "+str(angle))
                    center_point = (receipt.shape[0]//2,receipt.shape[1]//2)
                    rot_mat = cv.getRotationMatrix2D(center=center_point,angle=angle,scale=1.0);
                    rotated = cv.warpAffine(receipt,rot_mat,(receipt.shape[1],receipt.shape[0]))
                    ret, mask = cv.threshold(rotated,190,255,cv.THRESH_BINARY)
                    pth = self.receipts / ("receipt"+str(counter)+".jpg");
                    cv.imwrite(str(pth),mask);
                    response = self.client.detect_text(Image={"Bytes": pth.read_bytes()});
                    detections = response["TextDetections"];
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
                    self.correspondence[file_paths[i][file_paths[i].rfind("/")+1:]].append({f"receipt{counter}" : bounding_boxes[datetime_date[max(set(dates), key= dates.count)]]});
                    counter += 1;
        # for receipt in self.receipts.iterdir():
        #     receipt_name = re.findall("receipt\d+",str(receipt))[0]
        #     error_messages[receipt_name] = [];
        #     image = receipt.read_bytes()
        #     try:
        #         response = client.detect_text(Image={"Bytes":image});
        #     except:
        #         error_messages["NO AWS"] = True;
        #         eel.error_message(error_messages);
        #         return;
        #     detections = response["TextDetections"];
                            # eel.highlight(bounding_boxes[date], "Date");
                            # switch = True;
                    # if(switch):
                    #     break;
            # times = [];
            # switch = False;
            # for pattern in self.time_patterns:
            #     pos_times = re.findall(pattern, string);
            #     if(len(pos_times) != 0):
            #         for time in pos_times:
            #             if(time not in times): 
            #                 if(not("pm" in time.lower() or "am"  in time.lower())):
            #                     for i in range(len(time)-1,-1,-1):
            #                         if(time[i].isdigit()):
            #                             time = time[:i+1] 
            #                             break;
            #                 times.append(time);
            #                 switch= True;
            #     if(switch):
            #         break;
            # cards = [];
            # switch = False;
            # for pattern in self.card_patterns:
            #     pos_cards = re.findall(pattern,string.upper())
            #     if(len(pos_cards) != 0):
            #         for card in pos_cards:
            #             if(card not in cards):
            #                 cards.append(card[-4:]);
            #                 switch = True;
            #         if(switch):
            #             break;
            # total_pos_totals = [];
            # for pattern in self.total_patterns:
            #     pos_total = re.findall(pattern,string.upper())
            #     for total in pos_total:
            #         total_pos_totals.append(total);
            # nuf


        eel.progress_bar(i+1);


    def amazon_ocr(self, path, check=False):
        error_messages = {
            "Duplicate":[],
            "NO AWS": False};
        try:
            client = boto3.client("rekognition",
                                    aws_access_key_id=config.ACCESS_KEY,
                                    aws_secret_access_key=config.SECRET_KEY,
                                    region_name=config.REGION)
        except:
            error_messages["NO AWS"] = True;
            eel.error_message(error_messages);
            return;
        
        expenses_folder = path / "expenses";
        excel_files = [];
        has_errors = False;
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
        else:
            expenses_folder.mkdir();
        expense = { 
                "Filename": [],
                "DateTime": [],
                "Type":[],
                "Card":[],
                "Total":[]
        }
        if excel_files:
            df = pd.concat(pd.read_excel(excel_files[0], index_col=0, parse_dates=["DateTime"],date_format="%m/%d/%y %I:%M:%S %p",sheet_name=None),ignore_index=True);
            for excel_file in excel_files[1:]:
                df = pd.concat([df,pd.concat(pd.read_excel(path / excel_file, index_col=0, 
                                parse_dates=["DateTime"],date_format="%m/%d/%y %I:%M:%S %p",sheet_name=None),
                                ignore_index=True)],
                            ignore_index=True); 
        else:
            df = pd.DataFrame()

        # digits = re.compile(r'receipt(\d+).jpg')

        # for receipt in filter(
        #     lambda file: int(digits.match(file.name)[1]) >= counter, 
        #     receipts.iterdir()
        # ):
        for receipt in self.receipts.iterdir():
            receipt_name = re.findall("receipt\d+",str(receipt))[0]
            error_messages[receipt_name] = [];
            image = receipt.read_bytes()
            try:
                response = client.detect_text(Image={"Bytes":image});
            except:
                error_messages["NO AWS"] = True;
                eel.error_message(error_messages);
                return;
            detections = response["TextDetections"]
            string = ''
            for detection in detections:
                textType = detection["Type"]
                text = detection["DetectedText"]
                if(textType.lower() == "line"):
                    string += text + "\n";
            dates = [];
            switch = False;
            for pattern in self.date_patterns:
                pos_dates = re.findall(pattern,string)
                if(len(pos_dates) != 0 ):
                    for date in pos_dates:
                        if(date not in dates):
                            dates.append(date);
                            switch = True;
                    if(switch):
                        break;
            times = [];
            switch = False;
            for pattern in self.time_patterns:
                pos_times = re.findall(pattern, string);
                if(len(pos_times) != 0):
                    for time in pos_times:
                        if(time not in times): 
                            if(not("pm" in time.lower() or "am"  in time.lower())):
                                for i in range(len(time)-1,-1,-1):
                                    if(time[i].isdigit()):
                                        time = time[:i+1] 
                                        break;
                            times.append(time);
                            switch= True;
                if(switch):
                    break;
            cards = [];
            switch = False;
            for pattern in self.card_patterns:
                pos_cards = re.findall(pattern,string.upper())
                if(len(pos_cards) != 0):
                    for card in pos_cards:
                        if(card not in cards):
                            cards.append(card[-4:]);
                            switch = True;
                    if(switch):
                        break;
            total_pos_totals = [];
            for pattern in self.total_patterns:
                pos_total = re.findall(pattern,string.upper())
                for total in pos_total:
                    total_pos_totals.append(total);
            numbers = [];
            for total in total_pos_totals:
                str_number = '';
                for char in total:
                    if(char.isdigit()):
                        str_number += char;
                numbers.append(int(str_number));
            expense["Filename"].append(receipt)
            if(numbers):
                total = max(numbers)/100;
            else:
                error_messages[receipt_name].append("Total was not found!")
                has_errors= True;
                total = None;
            expense["Total"].append(total)
            if(len(cards) != 0):
                expense["Card"].append(int(cards[0]))
            else:
                error_messages[receipt_name].append("Card was not found!")
                has_errors= True;
                expense["Card"].append(None)
            if(len(dates) > 0):
                expense["DateTime"].append(dateutil.parser.parse(dates[0]+" "+times[0]));
            else:
                error_messages[receipt_name].append("Date was not found!");
                has_errors= True;
                expense["DateTime"].append(None);
            if(
                re.search("FUEL", string.upper()) != None 
                or re.search("PUMP#\s*\d+", string.upper()) != None
            ):
                expense["Type"].append("GAS")
            elif(
                re.search("HOME\s*DEPOT",string.upper()) != None 
                or re.search("HOW\s*DOERS\s*GET\s*MORE\s*DONE",string.upper()) != None
            ):
                expense["Type"].append("MATERIALS")
            elif(re.search("OFFICE",string.upper())!= None 
            ):
                expense["Type"].append("OFFICE SUPPLIES");
            elif(re.search("GROCERY",string.upper())!= None):
                expense["Type"].append("GROCERIES");
            else:
                error_messages[receipt_name].append("Type not found!");
                has_errors= True;
                expense["Type"].append(None);

        for key in error_messages:
            if(error_messages[key]):
                eel.error_message(error_messages);
                break;

        if(len(expense["DateTime"]) > 0):
            database = pd.DataFrame(expense);
            if(check):
                df = pd.concat([df, database], ignore_index=True);
            else:
                for index in database.index:
                    df = pd.concat([df, database.loc[[index]]], ignore_index=True)
                    drop_col = df.drop(columns=["Filename"])
                    if(not drop_col.equals(df.drop(columns=["Filename"]).drop_duplicates())):
                        string = str(database["Filename"][index])
                        error_messages["Duplicate"].append(re.findall("receipt\d+",string)[0]);
                        df.drop(df.tail(1).index, inplace=True);
                if(error_messages["Duplicate"] and not (has_errors)):
                    eel.error_message(error_messages);
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
    