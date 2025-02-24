import os
import base64


with open(r'C:\Users\505362\RA\ownimage.png', "rb") as image_file:
    base64_str = base64.b64encode(image_file.read()).decode("utf-8")