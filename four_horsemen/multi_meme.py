#!/usr/bin/env python3
"""
Create a TikTok video from a subreddit's memes

Used to Rank SubReddits by virality

TEST_CMD:
python3 four_horsemen/multi_meme.py -i subreddits.txt -b backgrounds\
    -n 50 -l 30 -m meta.xlsx -o output
"""
import os
from typing import List
from argparse import ArgumentParser
from random import choice, randint, random, shuffle

import pandas as pd
import shutup

from four_horsemen.utils import get_posts, download_image, get_media_length

ALLOWED_IMG_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv']
ALLOWED_AUDIO_EXTENSIONS = ['mp3', 'wav', 'm4a']

OUTPUT_ENDING = 'mp4'

REQUESTYPES = ['top', 'hot', 'new', 'rising', 'controversial']
API_KEYS_OF_INTEREST = ['id', 'subreddit', 'title', 'ups', 'downs',
                        'upvote_ratio', 'permalink', 'url']

NUM_IMAGES = [ i for i in range(1, 5) ]
BACKGROUND_SPEED = [0, 0.5, 1, 1.5, 2, 2.5, 3]
LENGTHS = [5, 10, 15]

DIMENSIONS = {
    'output': (1080, 1920),
    'imgs': (800, 1450),
    'imgs_center': (500, 800)
}

SMALLER = 20
RAND_SHIFT = 15

# IMPLEMENTATION

def main():
    """
    Main function for the program
    """
    args = get_args()
    args = parse_args(args)

    os.system('rm tmp/*')
    os.system(f'rm {args.output}/*')

    subreddits = [
        f for f in open(args.input, 'r', encoding='utf-8').read().strip().split('\n')
        ]
    backgrounds = [
        f for f in os.listdir(args.backgrounds)
        if any(f.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)
        ]
    audios = [
        f for f in os.listdir(args.audio)
        if any(f.endswith(ext) for ext in ALLOWED_AUDIO_EXTENSIONS)
        ]
    
    print(f'Found {len(backgrounds)} backgrounds')
    print(f'Found {len(audios)} audios')
    print(f'Found {len(subreddits)} subreddits')

    if os.path.isfile(args.meta):
        frame = pd.read_excel(args.meta, index_col=False)
    else:
        frame = get_subreddits(args, subreddits)
        frame.to_excel(args.meta, index=False)

    # Determines the number of videos per subreddit
    videos_per_subreddit = int(args.number) // len(subreddits) + 1
    videos_per_category = videos_per_subreddit // len(REQUESTYPES) + 1
    print("--------------------------------------------------")
    print(f'Creating {videos_per_subreddit} videos per subreddit')

    video_info = make_info(frame, backgrounds, audios, videos_per_category)

    shuffle(video_info)

    pd.DataFrame(video_info).to_excel('video_info.xlsx', index=False)

    print("--------------------------------------------------")
    success, failed = create_videos(video_info, args.output)

    print(f'Successfully created {len(success):4d} videos')
    print(f'Failed to create     {len(failed):4d} videos')

    success = pd.DataFrame(success)
    success['posted'] = False
    success['posted_at'] = None
    success.to_excel('success.xlsx', index=False)

    failed = pd.DataFrame(failed)
    failed.to_excel('failed.xlsx', index=False)


def get_args():
    """
    Gets the cli arguments for a grid post
    """
    args = ArgumentParser()
    args.add_argument('-i', '--input', help='Input subreddits list')
    args.add_argument('-b', '--backgrounds', help='Backgrounds directory')
    args.add_argument('-n', '--number', help='Number of memes to create', default=50)
    args.add_argument('-l', '--length', help='Length of the output video in seconds', default=30)
    args.add_argument('-t', '--token', help='Token for Reddit API') # Could be optional
    args.add_argument('-m', '--meta', help='Meta data for each video', default='meta.xlsx')
    args.add_argument('-a', '--audio', help='Audio directory', default='audios')
    args.add_argument('-o', '--output', help='Output directory', default='output')

    args = args.parse_args()
    return args


def parse_args(args):
    """
    Parses the cli arguments
    """
    return args


def get_subreddits(args, subreddits: List[str]) -> pd.DataFrame:
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
                ending = post['url'].split('.')[-1]

                if ending not in ALLOWED_IMG_EXTENSIONS:
                    continue

                with shutup.mute_warnings:
                    frame = frame.append(
                        {key: post[key] for key in API_KEYS_OF_INTEREST} |
                        {
                            'from': post_type, 
                        }
                , ignore_index=True)

    return frame


def make_info(frame: pd.DataFrame, backgrounds: List, audios: List, videos_per_category: int):
    """
    Makes the information for each video
    """
    return_array = []

    for subreddit, posts in frame.groupby('subreddit'):
        return_array += make_subreddit_info(
            videos_per_category, posts, subreddit, backgrounds, audios
            )

    return return_array


def make_subreddit_info(count: int, posts: pd.DataFrame,
    subreddit, backgrounds: List, audios: List):
    """
    Makes a list of dictionaries containing the information for each video
    """
    return_array = []

    for category in REQUESTYPES:
        for _ in range(count):
            return_array.append(make_video_info(posts, subreddit, backgrounds, audios, category))

    return return_array


def make_video_info(posts: pd.DataFrame, subreddit: str,
    backgrounds: List, audios: List, category: str) -> dict:
    '''
    Creates the video which can contain multiple images
    '''

    image_count = choice(NUM_IMAGES)
    post_imgs = posts.sample(image_count, replace=True)

    return {
        # Metadata
        'id': randint(0, 1000000),
        'subreddit': subreddit,
        'category': category,

        # Video information
        'images': post_imgs['url'].tolist(),
        'n': image_count,
        'audio': choice(audios),
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
        except Exception as e:
            print('Video creation failed')
            print(e)
            failed.append(i)

    return sucess, failed


def create_video(info: dict, output: str = 'output'):
    """
    Creates a video from the information
    """
    download_images(info['images'])

    command = [
        'ffmpeg',
        *get_input_settings(),
        *get_inputs(info['images'], info['background'], info['audio']),
        '-filter_complex', f'"{get_filter_complex(info)}"',
        *get_output_settings(output, info['id']),
    ]

    command = ' '.join(command)

    print(f'Creating video for {info["id"]} with subreddit'
          f' r/{info["subreddit"]} and category {info["category"]}')

    os.system(command)

    if not os.path.exists(output):
        raise VideoCreationError(f'Failed to create video for {info["id"]}')

def download_images(urls: List[str]) -> None:
    """
    Downloads the images from the posts
    """
    for url in urls:
        download_image(url)

def get_input_settings() -> List[str]:
    """
    Gets the input settings for ffmpeg
    """
    return [
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
    ]

def get_output_settings(output: str, video_id: int) -> List[str]:
    """
    Get the output settings for the FFmpeg command
    """
    return [
        '-map', '\'[vout]\'',
        '-map', '\'[aout]\'',

        '-shortest',

        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',
        f'{output}/{video_id}.{OUTPUT_ENDING}',
    ]

def get_inputs(images, background, audio):
    """
    Gets the inputs for the FFmpeg command
    """
    return [
        '-i', f'../../Desktop/backgrounds/{background}',
        '-i', f'audios/{audio}',
        *sum([['-i', f'{os.path.join("tmp", f.split("/")[-1])}'] for f in images], []),
    ]

def get_filter_complex(info: dict):
    """
    Creates the filter_complex command for ffmpeg
    """
    # Gets the layout of the posts
    num_images = len(info['images'])
    layout = get_post_layout(DIMENSIONS['imgs'], DIMENSIONS['imgs_center'], num_images)
    x_post_dim, y_post_dim = get_media_dims(DIMENSIONS['imgs'], num_images)
    img_filter = ','.join([
        f'scale={x_post_dim - SMALLER}:{y_post_dim - SMALLER}:force_original_aspect_ratio=decrease',
    ])
    x_rand = lambda: SMALLER + randint(-RAND_SHIFT, RAND_SHIFT)
    y_rand = lambda: SMALLER + randint(-RAND_SHIFT, RAND_SHIFT)

    layout = [
        f'[{i+2}:v]{img_filter},[base{i + 1}]overlay=({x + x_rand()}):({y + y_rand()})[base{i+2}]' if i > 0 else 
        f'[2:v]{img_filter},[v0]overlay=({x + x_rand()}):({y + y_rand()})[base2]'
        for i, (x, y) in enumerate(layout)
        ]

    length = info['length']
    speed = info['speed']

    video_length = get_media_length(f'../../Desktop/backgrounds/{info["background"]}')
    start_time = random() * (video_length - length)
    end_time = start_time + length

    filter_complex = [
        f'[0:v]trim={start_time:.2f}:{end_time:.2f}',
        'setpts=PTS-STARTPTS[v0]',

        *layout,
        f'[base{num_images + 1}]unsharp=3:3:1.5[vout]',
        *get_randomized_audio(info["audio"], info["length"]),
    ]

    return ','.join(filter_complex)


def get_randomized_audio(audio: str, length: int) -> List[str]:
    """
    Gets a randomized audio file
    """
    audio = f'audios/{audio}'
    audio_length = get_media_length(audio)

    start_time = random() * (audio_length - length)
    end_time = start_time + length

    audio_filter = [
        f'[1:a]atrim={start_time:.2f}:{end_time:.2f}',
        'asetpts=PTS-STARTPTS[aout]',
    ]

    return audio_filter

def get_post_layout(dimensions: tuple, center: tuple, num_images: int):
    """
    Gets the layout of the posts
    """
    rows, columns = get_rows_columns(num_images)

    return [
        get_pos(post_index, num_images, rows, columns, dimensions, center)
        for post_index in range(num_images)
    ]

def get_media_dims(dimensions: tuple, num_images: int) -> tuple:
    """
    Gets the dimensions of each post
    """
    rows, columns = get_rows_columns(num_images)
    width, height = dimensions

    return width // columns, height // rows


def get_pos(curr_index: int, num_posts: int, rows: int, columns: int, dimensions: tuple, center: tuple):
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
    x_dim, y_dim = dimensions
    x_center, y_center = center

    width, height = x_dim // columns, y_dim // rows

    row = curr_index // columns
    column = curr_index % columns

    x_offset = (columns * rows - num_posts) * width // 2 if row == rows - 1 else 0

    x, y = column * width + x_offset, row * height
    return x + x_center - x_dim // 2, y + y_center - y_dim / 2


def get_rows_columns(num_posts: int):
    """
    Gets the number of rows and columns for the posts
    """
    if num_posts == 1:
        return 1, 1
    elif num_posts == 2:
        return 2, 1
    elif num_posts == 3:
        return 3, 1
    elif num_posts == 4:
        return 2, 2
    elif num_posts == 5:
        return 3, 2
    elif num_posts == 6:
        return 3, 2
    elif num_posts == 7:
        return 3, 3
    elif num_posts == 8:
        return 3, 3
    elif num_posts == 9:
        return 3, 3
    else:
        raise ValueError(f'Number of posts {num_posts} is not supported')


class VideoCreationError(Exception):
    """
    Raised when a video failes to be created.

    Due to a problem with the FFmpeg command
    """


if __name__ == '__main__':
    main()
