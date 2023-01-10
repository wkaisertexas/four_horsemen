from argparse import ArgumentParser
import os
import re
import random
import math
import subprocess
import requests # Will be implemented later

from pytube import YouTube

import pandas as pd

args = ArgumentParser("Make clip")

args.add_argument('-b', '--backgrounds', help='Contains backgrounds to be randomly cut')
args.add_argument('-v', '--videos', help='text file containing video ids')
args.add_argument('-a', '--auth', help='Auth code for Tik Tok API')
args.add_argument('-u', '--user', help='User ID for Tik Tok API')
args.add_argument('-l', '--overlap', help='Overlap between clips', default=5, type=float)

args.add_argument('output', help='Output directory for the clips (tmp)')

args = args.parse_args()

videos = [f for f in open(args.videos, 'r').read().strip().split('\n')]

def video_info(filename):
    """
    Gets the duration and frame rate of a video
    """
    raw_info = subprocess.Popen(f'ffmpeg -i tmp/{i}.mp4', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0].decode('utf-8') # Gets rid of the standard error

    # Regex to match the pattern Duration: 00:00:00.00
    duration = raw_info.split('Duration: ')[1].split(',')[0].strip().split(':')
    # Converts the duration to seconds
    duration = int(duration[0]) * 3600 + int(duration[1]) * 60 + float(duration[2]) # Last one is in seconds and could be an int or float

    # Gets the frame rate of the video

    # Regex matches to the pattern , 30.000 fps
    frame_rate = re.search(',\\s+(\\d+).(\\d+)\\s+fps', raw_info).groups()[0]
    frame_rate = float(frame_rate.split(' ')[-1])

    return duration, frame_rate


# Setup tmp directory to download the videos
os.system('mkdir -p tmp')
os.system('rm -rf tmp')
os.system(f'rm -rf {args.output}')
os.system(f'mkdir -p {args.output}')

# Gets a glob of all the backgrounds
backgrounds = [f for f in os.listdir(args.backgrounds)]

# info dataframe
info = pd.DataFrame(columns=['filename', 'title', 'description', 'i', 'j'])

for i, url in enumerate(videos):
    if i == 0:
        continue
    print(f'Processing {url} with {i} index...')
    if len(url) == 11: # YouTube ID
        url = f'https://www.youtube.com/watch?v={url}'

    yt = YouTube(url)
    print("Downloading video...")
    yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download('tmp', f'{i}.mp4')

    duration, frame_rate = video_info(f'tmp/{i}.mp4')

    # Video length is as close to 60 seconds as possible (includes overlap)
    clips = int(math.ceil(duration / (60 - args.overlap)))
    clip_duration = duration / clips # Duration of each clip (not quite 60 seconds because of overlap and the fact that you do not want to go over)
    background = random.choice(backgrounds) # Randomly chooses a background which remains the same of all clips 
    bg_duration, bg_frame_rate = video_info(f'{args.backgrounds}/{background}')

    for j in range(clips):
        # Constructs a tik tok video with the background and the clip
        print(f'Making clip {j}/{clips} for video {i}')
        
        # Crops the video to the correct length
        print("\n\n\nCuts the video\n\n\n")
        os.system(f'ffmpeg -y -i tmp/{i}.mp4 -ss {j * clip_duration} -t {clip_duration + args.overlap} -c copy tmp/{i}_{j}.mp4')

        # Crops with video to 4:3 aspect ratio and resizes to a width of 1080p
        print('\n\n\nResizes the video\n\n\n')
        os.system(f'ffmpeg -y -i tmp/{i}_{j}.mp4 -vf "crop=4*min(iw/4\\,ih/3):3*min(iw/4\\,ih/3),scale=-2:810" -c:v libx264 -preset ultrafast tmp/{i}_{j}_crop.mp4')

        # Edits the video with the background using a random clip from the backgroun
        
        range = bg_duration - (clip_duration + args.overlap) # Duration of the background clip
        start = random.random() * range
        
        print("\n\n\nClipping the background\n\n\n")
        os.system(f'ffmpeg -y -i {os.path.join(args.backgrounds,background)} -ss {start} -t {clip_duration + int(args.overlap):.2f} -c copy -c:v libx264 -preset ultrafast -crf 29 tmp/{i}_{j}_bg.mp4')

        # Sets the frame rate of the background to the frame rate of the clip
        os.system(f'cp tmp/{i}_{j}_bg.mp4 tmp/{i}_{j}_bg_fr.mp4')

        print('\n\n\nResizing the background\n\n\n')
        os.system(f'ffmpeg -y -i tmp/{i}_{j}_bg_fr.mp4 -vf "crop=1080*min(iw/1080\\,ih/1110):1110*min(iw/1080\\,ih/1110),scale=1080:1110" -c:v libx264 -preset ultrafast -crf 29 tmp/{i}_{j}_bg_final.mp4')

        # Stacks clips using ffmpeg, complex_filter, vstack and amerge() keeping only the audio from the first clip
        print("\n\n\nStacking clips\n-----------------------")
        os.system(f'ffmpeg -y -i tmp/{i}_{j}_crop.mp4 -i tmp/{i}_{j}_bg_final.mp4  -filter_complex "[0:v][1:v]vstack" -vsync 2 -map 0:a -c:v libx264 -preset ultrafast -crf 29 {args.output}/{i}_{j}_final.mp4')


        # Uploads the video to Tik Tok usign the API and the requests library
        info = pd.concat([info, pd.DataFrame([[f'{args.output}/{i}_{j}_final.mp4', yt.title, f"Part {i + 1}\n" + yt.title + "\n" + yt.description, i, j]], columns=info.columns)])

        os.system(f'rm tmp/{i}_{j}.mp4 tmp/{i}_{j}_crop.mp4 tmp/{i}_{j}_bg.mp4 tmp/{i}_{j}_bg_fr.mp4 tmp/{i}_{j}_bg_final.mp4')
    
        # Saves the dataframe to an excel file (just going to have to copy and paste for now lol)
        info.to_excel('info.xlsx')
        # input("Press enter to continue...")
    os.system(f'rm tmp/{i}.mp4')