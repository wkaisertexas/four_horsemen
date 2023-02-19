from argparse import ArgumentParser
from os.path import join
from os import listdir, system
import re
import random
import math
import subprocess
import requests # Will be implemented later
from time import time

from pytube import YouTube

import pandas as pd

from four_horsemen.srt import xml_to_srt

VALID_CAPTIONS = ['en', 'en-US', 'a.en', 'a.en-US']
VIDEO_EXTENSIONS = ['mov', 'mp4', 'avi', 'mkv', 'webm'] # must be supported by ffmpeg
VIDEO_QUALITY = ['720p', '480p', '360p', '240p', '144p'] # must be supported by pytube

def main():
    """
    Main function
    """
    args = get_args()
    args = validate_args(args)

    videos = [f for f in open(args.videos, 'r', encoding='utf-8').read().strip().split('\n')]
    random.shuffle(videos)

    print(f'Found {len(videos)} videos')

    clear(args.output)

    # Gets a glob of all the backgrounds
    backgrounds = [join(args.backgrounds, f) for f in listdir(args.backgrounds) 
                        if is_video(f)]
    print(f'Found {len(backgrounds)} backgrounds')

    # video information storage
    failed = []
    info = []
    for id in map(get_video_id, videos):
        try:
            curr_time = time()

            info += split_clip(id, length=args.length, overlap=args.overlap, output=args.output, backgrounds=backgrounds)
            save_data(info, args.info) # excel, csv or json

            print(f'Time taken to split video: {time() - curr_time:.2f} seconds')
        except Exception as e:
            print(f'Failed to create video: {id}\nException:\n {e}')
            failed.append(id)

    return failed

def get_args():
    """
    Gets the arguments
    """
    args = ArgumentParser("Make clip")

    args.add_argument('-b', '--backgrounds', help='Contains backgrounds to be randomly cut')
    args.add_argument('-v', '--videos', help='text file containing video ids')
    args.add_argument('-a', '--auth', help='Auth code for Tik Tok API')
    args.add_argument('-u', '--user', help='User ID for Tik Tok API')
    args.add_argument('-o', '--overlap', help='Overlap between clips', default=5, type=float)
    args.add_argument('-l', '--length', help='Max clip length', default=90, type=float) # Clips are now 90 seconds by default
    args.add_argument('-i', '--info', help='Where to save video info (xlsx, csv or json)', default='info.xlsx')
    args.add_argument('output', help='Output directory for the clips (tmp)')

    return args.parse_args()


def validate_args(args):
    """
    Validates the arguments
    """
    return args


def get_duration(filename: str) -> float:
    """
    Gets the duration and frame rate of a video
    """
    raw_info = subprocess.Popen(f'ffmpeg -i {filename}', stdout=subprocess.PIPE, stderr = subprocess.STDOUT, shell=True).communicate()[0].decode('utf-8') # Gets rid of the standard error

    # Regex to match the pattern Duration: 00:00:00.00
    duration = raw_info.split('Duration: ')[1].split(',')[0].strip().split(':')

    return int(duration[0]) * 3600 + int(duration[1]) * 60 + float(duration[2])


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


def clear(output: str = 'output'):
    """
    Clears the temporary directory from the previous run
    """
    system('mkdir -p tmp')
    system('rm -rf tmp/*.mp4')
    system(f'rm -rf {output}')
    system(f'mkdir -p {output}')


def get_valid_languages(captions) -> list:
    """
    Checks if the captions are valid
    """
    valid_captions = []
    captions = list(captions.keys())
    for caption in captions:
        if caption.code in VALID_CAPTIONS:
            valid_captions.append(caption)
    
    return valid_captions


def is_video(path: str) -> bool:
    """
    Checks whether or not a video is valid

    Typically used in conjunction with a listdir
    """
    return path.split('.')[-1] in VIDEO_EXTENSIONS


def get_video_id(url: str) -> str:
    """
    Gets the video id from a url
    """
    if 'v=' in url:
        return url.split('v=')[1]
    elif 'youtu.be' in url:
        return url.split('/')[-1]
    
    # check if the url is a video id
    if len(url) == 11:
        return url
    
    raise Exception(f'Invalid URL: {url}')


def download_video(video_id: str, output: str = 'tmp'):
    """
    Downloads a video from a id
    """
    print(f'Downloading video: {video_id}')

    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')

    # saves a little bit of time by not downloading the highest quality video
    streams = yt.streams.filter(resolution= lambda res: res in VIDEO_QUALITY).order_by('resolution').desc()
    if streams:
        streams.first().download(output, f'{video_id}.mp4')
    else:  
        yt.streams.filter(progressive=True).order_by('resolution').desc().first().download(output, f'{video_id}.mp4')

    return yt


def get_output_props(duration, length=90, overlap=5):
    """
    Calculates the clip length and the number of clips
    """
    clips = int(math.ceil(duration / (length - overlap)))
    clip_duration = duration / clips
    return clips, clip_duration


def get_random_clip(duration, clip_duration, overlap=5):
    """
    Gets a random clip of the background
    """
    time_range = duration - (clip_duration + overlap) # Duration of the background clip
    start = random.random() * time_range
    return time_range, start


def upload_clip(index: int, id: str, backgrounds: list, output: str, captions: str, clip_duration: float, overlap: float, quality_settings: str = None):
    """
    Creates a single clip using ffmpeg
    
    Parameters
    ----------
    index: int
        The index of the subclip
    id: str
        The id of the YouTube video
    backgrounds: list
        A list of all the background videos to choose from
    captions: list
        .srt or other valid captions file for the video
    clip_duration: float
        Duration of each clip
    overlap: float
        Overlap time between clips
    quality_settings: str
        Custom quality settings for the output image
        Default: "-r 30 -vsync 2 -c:v libx264 -crf 29 -preset ultrafast"
    """
    print(f'Making clip {index + 1:3} for video {id}')

    quality_settings = quality_settings or '-r 30 -vsync 2 -c:v libx264 -crf 32 -preset ultrafast'
        
    background = random.choice(backgrounds) # Randomly chooses a background which remains the same of all clips 
    bg_duration = get_duration(background)
        
    time_range, start = get_random_clip(bg_duration, clip_duration, overlap)

    sub = f"subtitles=tmp/{id}.srt:force_style='Fontname=Consolas,BackColour=&H80000000,Spacing=0.2,Outline=0,Shadow=0.75'," if captions else ""

    system(f'ffmpeg -v quiet -y -i {background} -i {join("tmp", f"{id}.mp4")} -filter_complex "[1:v]{sub}trim=start={index * clip_duration}:duration={clip_duration + overlap},setpts=PTS-STARTPTS,crop=4*min(iw/4\,ih/3):3*min(iw/4\,ih/3),scale=1080:810,pad=iw:ih+10:0:0:black[top],[0:v]trim=start={start}:duration={clip_duration + overlap},setpts=PTS-STARTPTS,crop=1080*min(iw/1080\,ih/1100):1100*min(iw/1080\,ih/1100),scale=1080:1100,[top]vstack=inputs=2:shortest=1,drawtext=fontsize=180:fontcolor=white:x=80:y=750:text=\'{index + 1}\':enable=\'between(t,0,10)\':box=1:boxborderw=10:line_spacing=500:boxcolor=black[out],[1:a]atrim=start={index * clip_duration}:duration={clip_duration + overlap},asetpts=PTS-STARTPTS[aout]" -map \'[out]\' -map \'[aout]\' {quality_settings} {join(output, f"{id}+{index}.mp4")}')


def split_clip(id: str, length: float, overlap: float, backgrounds: list, output: str, use_captions: bool = False) -> list:
    """
    Splits a clip into multiple clips
    
    Parameters
    ----------
    id: str
        The id of the YouTube video
    length: float
        The length of each clip
    overlap: float
        The overlap between clips  
    backgrounds: list
        A list of all the background videos to choose from (must be full path)
    output: str
        The output directory
    """
    yt = download_video(id)

    valid_langs = get_valid_languages(yt.captions)

    if use_captions and valid_langs:
        srt_captions = xml_to_srt(yt.captions[valid_langs[0]].xml_captions)
        save_string(srt_captions, f'tmp/{id}.srt')

    duration = get_duration(f'tmp/{id}.mp4')

    print(f'Duration: {duration:0.2f} seconds')

    num_clips, clip_duration = get_output_props(duration, length, overlap)

    information = []
    for i in range(num_clips):
        upload_clip(
            index=i, 
            id=id, 
            backgrounds=backgrounds, 
            output=output, 
            captions=None,
            clip_duration=clip_duration, 
            overlap=overlap
        )

        information.append({
            'id': id,
            'title': yt.title,
            'description': f'Part {i + 1}/{num_clips} of {yt.title}',
            'part': i + 1,
            'file_path': join(output, f'{id}+{i}.mp4'),
            'uploaded': False
        })

    system(f'rm tmp/{id}.mp4 tmp/{id}.srt')

    return information


def save_string(string: str, path: str) -> None:
    """Saves a string to a file"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(string)
        f.close()


def save_data(info: list, path: str) -> None:
    """
    Saves the data based on the ending of the string

    Parameters
    ----------
    info
        A list of dictionaries with video information
    path
        The path to save the data to
    """
    # convert info from a list of dictionaries to a dictionary of lists
    info = {key: [d[key] for d in info] for key in info[0]}
    frame = pd.DataFrame(info)

    if path.endswith('.csv'):
        frame.to_csv(path, index=False)
    elif path.endswith('.json'):
        frame.to_json(path, orient='records')
    elif path.endswith('.xlsx'):
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False)