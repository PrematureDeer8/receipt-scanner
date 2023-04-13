import eel
import base64
import asyncio

eel.init("web");

@eel.expose
def pass_images(bufferData):
    print(bufferData)
    # for data in bufferData:
    #     print(data);
    #     print("hello")

eel.start("index.html");