from argparse import ArgumentParser
import os
import re
import random
import math
import subprocess
import requests # Will be implemented later

from pytube import YouTube

import pandas as pd

from srt import xml_to_srt

VALID_CAPTIONS = ['en', 'en-US', 'a.en', 'a.en-US']

args = ArgumentParser("Make clip")

args.add_argument('-b', '--backgrounds', help='Contains backgrounds to be randomly cut')
args.add_argument('-v', '--videos', help='text file containing video ids')
args.add_argument('-a', '--auth', help='Auth code for Tik Tok API')
args.add_argument('-u', '--user', help='User ID for Tik Tok API')
args.add_argument('-o', '--overlap', help='Overlap between clips', default=5, type=float)
args.add_argument('-l', '--length', help='Max clip length', default=90, type=float) # Clips are now 90 seconds by default
args.add_argument('output', help='Output directory for the clips (tmp)')

args = args.parse_args()

videos = [f for f in open(args.videos, 'r').read().strip().split('\n')]

videos = random.shuffle(videos)

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
    frame_rate = re.search(r', (\d+\.\d+|\d+) fps', raw_info).groups()[0]
    frame_rate = float(frame_rate.split(' ')[-1])

    return duration, frame_rate

def split_into_lines(text: str, max_length: int):
    """
    Splits a string into lines of max_length
    """
    words = text.split(' ')
    lines = []
    line = ''
    for word in words:
        if len(line) + len(word) < max_length:
            line += word + ' '
        else:
            lines.append(line)
            line = word + ' '
    lines.append(line)
    return lines


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
    print(f'Processing {url} with {i} index...')
    if len(url) == 11: # YouTube ID
        url = f'https://www.youtube.com/watch?v={url}'
        print("Video ID converted to URL")

    yt = YouTube(url)
    print("Downloading video...")
    yt.streams.filter(progressive=True).order_by('resolution').desc().first().download('tmp', f'{i}.mp4')

    # check if captions contains 'en' or 'en-US' or 'a.en' or 'a.en-US'
    captions = None
    for caption in yt.captions:
        if caption.code in VALID_CAPTIONS:
            captions = caption
            break
    
    if False:
        # Converts the xml captions to srt captions with a function that will be importted from another file
        srt_captions = xml_to_srt(captions.xml_captions)
        with open(f'tmp/{i}.srt', 'w') as f:
            print(srt_captions)
            f.write(srt_captions)
            f.close()

    duration, frame_rate = video_info(f'tmp/{i}.mp4')

    # Video length is as close to 60 seconds as possible (includes overlap)
    clips = int(math.ceil(duration / (args.length - args.overlap)))
    clip_duration = duration / clips # Duration of each clip (not quite 60 seconds because of overlap and the fact that you do not want to go over)

    for j in range(clips):
        # Constructs a tik tok video with the background and the clip
        print(f'Making clip {j}/{clips} for video {i}')
        
        background = random.choice(backgrounds) # Randomly chooses a background which remains the same of all clips 
        bg_duration, bg_frame_rate = video_info(os.path.join(args.backgrounds, background))
        time_range = bg_duration - (clip_duration + args.overlap) # Duration of the background clip
        start = random.random() * time_range

        # TODO: ADD the title and the part to a video 

        sub = f"subtitles=tmp/{i}.srt:force_style='Fontname=Consolas,BackColour=&H80000000,Spacing=0.2,Outline=0,Shadow=0.75'," if captions else ""
        sub = ""
        os.system(f'ffmpeg -v quiet -y -i {os.path.join(args.backgrounds, background)} -i {os.path.join("tmp", f"{i}.mp4")} -filter_complex "[1:v]{sub}trim=start={j * clip_duration}:duration={clip_duration + args.overlap},setpts=PTS-STARTPTS,crop=4*min(iw/4\,ih/3):3*min(iw/4\,ih/3),scale=1080:810,pad=iw:ih+10:0:0:black[top],[0:v]trim=start={start}:duration={clip_duration + args.overlap},setpts=PTS-STARTPTS,crop=1080*min(iw/1080\,ih/1100):1100*min(iw/1080\,ih/1100),scale=1080:1100,[top]vstack=inputs=2:shortest=1,drawtext=fontsize=180:fontcolor=white:x=80:y=750:text=\'{j + 1}\':enable=\'between(t,0,10)\':box=1:boxborderw=10:line_spacing=500:boxcolor=black[out],[1:a]atrim=start={j * clip_duration}:duration={clip_duration + args.overlap},asetpts=PTS-STARTPTS[aout]" -map \'[out]\' -map \'[aout]\' -r 30 -vsync 2 -c:v libx264 -crf 29 -preset ultrafast {os.path.join(args.output, f"{i}+{j}.mp4")}')
        
        # Uploads the video to Tik Tok usign the API and the requests library
        info = pd.concat([info, pd.DataFrame([[f'{args.output}/{i}_{j}_final.mp4', yt.title, f"Part {j + 1}\n" + yt.title + "\n" + yt.description, i, j]], columns=info.columns)])

        info.to_excel('info.xlsx')
    os.system(f'rm tmp/{i}.mp4 tmp/{i}.srt')