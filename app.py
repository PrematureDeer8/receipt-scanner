import cv2 as cv;
import numpy as np;
from sympy import Polygon, Point
import sys
from deskew import determine_skew
from dateutil.parser import parse
import os

#get the counter value
parsed_receipts = os.listdir("parsed_receipts");
if(len(parsed_receipts) > 0):
    maximum = max(parsed_receipts);
    str_counter = "";
    for char in maximum:
        if(char.isdigit()):
            str_counter += char;
    counter = int(str_counter)+1
else:
    counter = 0;
#get unread receipts
images = [];
names = os.listdir("scanned_receipts")
for name in names:
    images.append(cv.imread("scanned_receipts/{}".format(name)));
    #move unread receipts to read receipts
    os.replace("scanned_receipts/{}".format(name),"read_receipts/{}".format(name))
if(len(images) > 0):
    for image in images:
        if(type(image) == type(None)):
            sys.exit("Image cannot be read")
        iwidth , iheight = image.shape[:2]
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blur = cv.blur(gray,(5,5))
        ret, mask = cv.threshold(blur,175,255,cv.THRESH_BINARY)
        contours, hieracrhy = cv.findContours(mask,cv.RETR_EXTERNAL ,cv.CHAIN_APPROX_NONE)
        cv.drawContours(image, contours,-1,(0,0,255),thickness=5)
        sort = sorted(contours, key=lambda element: len(element),reverse=True)
        filtered = [];
        copy = sort.copy()
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
            cv.circle(image,(int(rotate[index][0][0]),int(rotate[index][0][1])),50,(0,0,255),thickness=-1)
            cv.line(image,(int(rotate[index][0][0]-w), int(rotate[index][0][1])),(int(rotate[index][0][0]+w),int(rotate[index][0][1])),(index*100,255,0),30)
            cv.line(image,(int(rotate[index][0][0]),int(rotate[index][0][1]-h)),(int(rotate[index][0][0]),int(rotate[index][0][1]+h)),(255,0,index*100),30)
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
        #deskew
        for index, receipt in enumerate(receipts):
            # cv.imshow("receipt"+str(index+1),receipt);
            angle = determine_skew(receipt);
            # print("Angle: "+str(angle))
            center_point = (receipt.shape[0]//2,receipt.shape[1]//2)
            rot_mat = cv.getRotationMatrix2D(center=center_point,angle=angle,scale=1.0);
            rotated = cv.warpAffine(receipt,rot_mat,(receipt.shape[1],receipt.shape[0]))
            ret, mask = cv.threshold(rotated,190,255,cv.THRESH_BINARY)
            # img_dilation = cv.dilate(mask, kernel, iterations=1)
            cv.imwrite("parsed_receipts/receipt"+str((counter))+".jpg",mask);
            counter += 1;
