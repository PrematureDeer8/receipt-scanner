from config import aws_config as config
import boto3
import re
import pandas as pd
import dateutil.parser
import pathlib
import warnings

date_patterns = ["[0,1]*[0-9]\\/[0-3][0-9]\\/[0-9]{4}","[0,1]*[0-9]\\/[0-3][0-9]\\/[0-9]{2}"]
time_patterns = ["[0-9][0-9]\:[0-9][0-9]\:[0-9][0-9]\s*\D\D","[0-9][0-9]\:[0-5][0-9]\s*\D\D","[0-9]\:[0-5][0-9]\s*\D\D"]
card_patterns = ["CARD\W+\s*\S*\d{4}","VISA\W+\d{4}","ACCOUNT\W+\d{4}","[X]{4}\s*[X]{4}\s*[X]{4}\s*\d{4}"]
total_patterns = ["TOTAL\W*\d+[.]\d{2}","PAYMENT\s*AMOUNT\s*\d+[.]\d{2}", "USD\s*[$]\s*\d+[.]\d{2}","BALANCE\s*\d+[.]\d{2}"]


def amazon_ocr():

    client = boto3.client("rekognition",
                            aws_access_key_id=config.ACCESS_KEY,
                            aws_secret_access_key=config.SECRET_KEY,
                            region_name=config.REGION)

    excel_files = sorted(list(pathlib.Path('.').glob("*.xlsx")));

    expense = { 
            "Filename": [],
            "DateTime": [],
            "Type":[],
            "Card":[],
            "Total":[]
        }
    if excel_files:
        df = pd.concat(pd.read_excel(str(excel_files[0]), index_col=0, parse_dates=["DateTime"],
                            date_format="%m/%d/%y %I:%M %p",sheet_name=None),ignore_index=True);
        for excel_file in excel_files[1:]:
            df = pd.concat([df,pd.concat(pd.read_excel(str(excel_file), index_col=0, 
                            parse_dates=["DateTime"],date_format="%m/%d/%y %I:%M %p",sheet_name=None),
                            ignore_index=True)],
                           ignore_index=True); 
    else:
        df = pd.DataFrame()


    counter = len(df)
    receipts = pathlib.Path(".") / 'web'/ 'images' / 'parsed_receipts'

    digits = re.compile(r'receipt(\d+).jpg')

    for receipt in filter(
        lambda file: int(digits.match(file.name)[1]) >= counter, 
        receipts.iterdir()
    ):
        image = receipt.read_bytes()
        response = client.detect_text(Image={"Bytes":image})

        detections = response["TextDetections"]
        string = ''
        for detection in detections:
            textType = detection["Type"]
            text = detection["DetectedText"]
            if(textType.lower() == "line"):
                string += text + "\n";
        # print(string);
        dates = [];
        switch = False;
        for pattern in date_patterns:
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
        for pattern in time_patterns:
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
        for pattern in card_patterns:
            pos_cards = re.findall(pattern,string.upper())
            if(len(pos_cards) != 0):
                for card in pos_cards:
                    if(card not in cards):
                        cards.append(card[-4:]);
                        switch = True;
                if(switch):
                    break;
        total_pos_totals = [];
        for pattern in total_patterns:
            pos_total = re.findall(pattern,string.upper())
            for total in pos_total:
                total_pos_totals.append(total);
        numbers = [];
        for total in total_pos_totals:
            # print(total)
            str_number = '';
            for char in total:
                if(char.isdigit()):
                    str_number += char;
            numbers.append(int(str_number));
        if(numbers):
            total = max(numbers)/100;
        else:
            total = None;
        expense["Total"].append(total)
        if(len(cards) != 0):
            expense["Card"].append(int(cards[0]))
        else:
            expense["Card"].append(None)
        if(len(dates) > 0):
            expense["DateTime"].append(dateutil.parser.parse(dates[0]+" "+times[0]));
        else:
            expense["DateTime"].append(None);
        expense["Filename"].append(receipt)
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
            expense["Type"].append(None);

    print(expense);
    if(len(expense["DateTime"]) > 0):
        database = pd.DataFrame(expense);
        combined_df = pd.concat([df, database], ignore_index=True)
        combined_df.sort_values(by="DateTime",inplace=True,ignore_index=True,na_position="first");
        for index, (y, year_df) in enumerate(combined_df.groupby(pd.Grouper(key="DateTime", freq="Y"))):
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
            with warnings.catch_warnings(), pd.ExcelWriter(excel_name, engine='openpyxl', **params) as writer:
                warnings.simplefilter(action='ignore')
                # for index, (_, group_df) in enumerate(combined_df.groupby(pd.Grouper(key='DateTime', freq='M'))):
                for (_, group_df) in year_df.groupby(pd.Grouper(key='DateTime', freq='M')):
                    datetime_str = group_df['DateTime'].dt.strftime('%m/%d/%y %I:%M %p')
                    group_df['DateTime'] = datetime_str
                    group_df.to_excel(writer, sheet_name=_.strftime("%B"))
    