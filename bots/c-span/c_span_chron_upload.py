"""
Uploads a C_Span video using a cron job (going to be run on desktop)

Cron Tab: 0 0 0/3 * * * *
"""
import pandas as pd
from os import system

COOKIES = "cookies.txt"
INFO = "info.xslx"
KEY = "uploaded"

def main(): 
    frame = pd.read_excel(INFO)
    
    # gets index of video
    unposted = frame.loc[frame[KEY]==0]
    
    # TODO: Maybe write a bunch of files to my desktop to notify me that things have not been posted

    index = uposted[0]

    # gets the row from the data frame
    video_info = frame.iloc[index]

    system(f"tiktok-uploader -v {video_info['file_path']} -description {video_info['description'] -c {COOKIES}")   

    video_info[KEY] = True # Registers the video has been uploaded
    frame.to_excel(INFO)
