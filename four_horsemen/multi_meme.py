#!/usr/bin/env python3
"""
Create a TikTok video from a subreddit's memes

Used to Rank SubReddits by virality

TEST_CMD:
python3 four_horsemen/multi_meme.py -i subreddits.txt -b backgrounds -n 50 -l 30 -m meta.xlsx -o output
"""

import os
from argparse import ArgumentParser
from random import choice, randint

import pandas as pd

from four_horsemen.utils import *

import shutup


ALLOWED_IMG_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv']

REQUESTYPES = ['top', 'hot', 'new', 'rising', 'controversial']
API_KEYS_OF_INTEREST = ['id', 'subreddit', 'title', 'ups', 'downs', 'upvote_ratio', 'permalink', 'url']

NUM_IMAGES = [1, 2, 3, 4, 5, 6] # Up to six images per video
BACKGROUND_SPEED = [0, 0.5, 1, 1.5, 2, 2.5, 3]
LENGTHS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

DIMENSIONS = {
    'output': (1080, 1920),
    'imgs': (800, 1080),
    'imgs_center': (540, 540)
}

# IMPLEMENTATION

def main():
    """
    Main function for the program
    """
    args = get_args()
    args = parse_args(args)

    os.system('rm tmp/*')
    os.system(f'rm {args.output}/*')

    subreddits = [f for f in open(args.input, 'r', encoding='utf-8').read().strip().split('\n')]
    backgrounds = [f for f in os.listdir(args.backgrounds)
                   if any(f.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)]

    print(f'Found {len(subreddits)} subreddits')
    frame = get_subreddits(args, subreddits)
    frame.to_excel(args.meta, index=False)

    print(frame.head())

    # Determines the number of videos per subreddit
    videos_per_subreddit = int(args.number) // len(subreddits) + 1 # +1 to account for rounding down
    videos_per_category = videos_per_subreddit // len(REQUESTYPES) + 1 # +1 to account for rounding down

    video_info = make_info(frame, backgrounds, videos_per_category)

    input()
    print(video_info[:10])
    input()

    success, failed = create_videos(video_info, args.output)

    print(f'Successfully created {len(success):4d} videos')
    print(f'Failed to create     {len(failed):4d} videos')

def get_args():
    args = ArgumentParser()
    args.add_argument('-i', '--input', help='Input subreddits list')
    args.add_argument('-b', '--backgrounds', help='Backgrounds directory')
    args.add_argument('-n', '--number', help='Number of memes to create', default=50)
    args.add_argument('-l', '--length', help='Length of the output video in seconds', default=30)
    args.add_argument('-t', '--token', help='Token for Reddit API') # Could be optional
    args.add_argument('-m', '--meta', help='Meta data for each video', default='meta.xlsx')
    args.add_argument('-o', '--output', help='Output directory', default='output')

    args = args.parse_args()
    return args


def parse_args(args):
    """
    Parses the cli arguments
    """
    return args


def get_subreddits(args, subreddits):
    """
    Gets the releavant posts from the subreddits
    """
    frame = pd.DataFrame(columns=API_KEYS_OF_INTEREST + ['from'])

    for subreddit in subreddits:
        for post_type in REQUESTYPES:
            try:
                posts = get_posts(subreddit, post_type, args.number, args.token)
            except TimeoutError:
                print(f'Failed to get posts for {post_type} for {subreddit}')
                continue

            for post in posts:
                # post 'url' can also be a list of urls
                ending = post['url'].split('.')[-1]

                if ending not in ALLOWED_IMG_EXTENSIONS:
                    continue

                with shutup.mute_warnings:
                    frame = frame.append({key: post[key] for key in API_KEYS_OF_INTEREST} | {
                'from': post_type,
                }, ignore_index=True)

    return frame


def make_info(frame: pd.DataFrame, backgrounds: List, videos_per_category: int):
    """
    Makes the information for each video
    """
    return_array = []

    for subreddit, posts in frame.groupby('subreddit'):
        return_array += make_subreddit_info(videos_per_category, posts, subreddit, backgrounds)

    return return_array


def make_subreddit_info(count: int, posts: pd.DataFrame, subreddit, backgrounds: List):
    """
    Makes a list of dictionaries containing the information for each video
    """
    return_array = []

    for category in REQUESTYPES:
        for _ in range(count):
            return_array.append(make_video_info(posts, subreddit, backgrounds, category))

    return return_array


def make_video_info(posts: pd.DataFrame, subreddit: str, backgrounds: List, category: str):
    '''
    Creates the video which can contain multiple images
    '''

    n = choice(NUM_IMAGES)
    p = posts.sample(n)

    return {
        # Metadata
        'id': randint(0, 1000000),
        'subreddit': subreddit,
        'category': category,

        'images': p['url'].tolist(),
        'n': n,
        'background': choice(backgrounds),
        'speed': choice(BACKGROUND_SPEED),
        'length': choice(LENGTHS),
    }

def create_videos(info: List[dict], output: str = 'output'):
    """
    Creates the videos from the information

    Return (sucess, failed)
    """
    sucess = []
    failed = []
    for i in info:
        try:
            create_video(i, output)
            sucess.append(i)
        except VideoCreationError:
            print('error')
            failed.append(i)

    return sucess, failed

def create_video(info: dict, output: str = 'output'):
    """
    Creates a video from the information
    """
    output = f'{output}/{info["id"]}.mp4'

    command = [
        'ffmpeg',
        '-y',

        '-loop', '1',
        '-i', f'backgrounds/{info["background"]}',

        '-filter_complex', f'"{get_filter_complex(info)}"',

        # output is the info['id'] + '.mp4'
        output,
    ]

    command = ' '.join(command)

    os.system(command)

    # checks if output exists
    if not os.path.exists(output):
        print("video creatoin failed")
        raise VideoCreationError(f'Failed to create video for {info["id"]}')



def get_filter_complex(info: dict):
    """
    Creates the filter_complex command for ffmpeg
    """
    # Gets the layout of the posts
    num_images = len(info['images'])
    layout = get_post_layout(DIMENSIONS, num_images)

    filter_complex = [
        f'[0:v]scale={info["length"] * info["speed"]}:1080:force_original_aspect_ratio=decrease',
        f'pad={info["length"] * info["speed"]}:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v0]'

        # Overlays the images
        *[f'[v{i}][{i+1}:v]overlay={x}:{y}[v{i+1}]' for i, (x, y) in enumerate(layout)],
    ]

    filter_complex = ','.join(filter_complex)

    return filter_complex



def get_post_layout(dimensions: tuple, num_images: int):
    """
    Gets the layout of the posts
    """
    rows, columns = get_rows_columns(num_images)

    return [
        get_pos(i, num_images, rows, columns, dimensions) for i in range(num_images)
    ]


def get_pos(i: int, n: int, rows: int, columns: int, dimensions: tuple):
    """
    Gets the position of the post

    Changes depending on whether or not the post is in a full row or not

    Parameters
    i : int
        The index of the position to get
    n : int
        The number of posts
    rows : int
        The number of rows
    columns : int
        The number of columns
    dimensions : tuple (of ints)
        The dimensions of the space to take up
    """
    x, y = dimensions
    width, height = x // columns, y // rows

    row = i // columns
    column = i % columns

    x_offset = (columns * rows - n) * width // 2 if row == rows - 1 else 0

    return column * width + x_offset, row * height

def get_rows_columns(n):
    """
    Gets the number of rows and columns for the posts
    """
    if n == 1:
        return 1, 1
    elif n == 2:
        return 1, 2
    elif n == 3:
        return 2, 2
    elif n == 4:
        return 2, 2
    elif n == 5:
        return 2, 3
    elif n == 6:
        return 2, 3
    elif n == 7:
        return 3, 3
    elif n == 8:
        return 3, 3
    elif n == 9:
        return 3, 3
    else:
        raise ValueError(f'Number of posts {n} is not supported')


class VideoCreationError(Exception):
    """
    Raised when a video failes to be created.

    Due to a problem with the FFmpeg command
    """

if __name__ == '__main__':
    main()
