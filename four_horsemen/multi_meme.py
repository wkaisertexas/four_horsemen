# !/usr/bin/env python3
import os
from argparse import ArgumentParser
import pandas as pd

from utils import *

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

REQUESTYPES = ['top', 'hot', 'new', 'rising', 'controversial']
API_KEYS_OF_INTEREST = ['id', 'subreddit', 'title', 'ups', 'downs', 'upvote_ratio', 'permalink', 'url']

def main():
    args = get_args()
    args = parse_args(args)

    os.system('rm tmp/*')
    os.system(f'rm {args.ouput}/*')

    subreddits = [f for f in open(args.input, 'r').read().strip().split('\n')]
    backgrounds = [f for f in os.listdir(args.backgrounds) if any(f.endswith(ext) for ext in ALLOWED_EXTENSIONS)]

    frame = get_subreddits(args, subreddits)

    print(frame.head()) # TODO: Remove strictly debugging

    # Determines the number of videos per subreddit
    videos_per_subreddit = args.number // len(subreddits) + 1 # +1 to account for rounding down
    videos_per_category = videos_per_subreddit // len(REQUESTYPES) + 1 # +1 to account for rounding down

    # Downloads all the videos
    download_subreddits(args, subreddits, frame, videos_per_category, backgrounds)

    # Creates the videos 
    pass


def get_args():
    args = ArgumentParser()
    args.add_argument('-i', '--input', help='Input subreddits list')
    args.add_argument('-b', '--backgrounds', help='Backgrounds directory')
    args.add_argument('-n', '--number', help='Number of memes to create', default=500)
    args.add_argument('-l', '--length', help='Length of the output video in seconds', default=30)
    args.add_argument('-t', '--token', help='Token for Reddit API') # Could be optional
    args.add_argument('-m', '--meta', help='Meta data for each video', default='meta.xlsx')
    args.add_argument('-o', '--output', help='Output directory', default='output')

    args = args.parse_args()
    return args


def parse_args(args):
    """Parses the arguments"""
    return args


def get_subreddits(args, subreddits):
    frame = pd.DataFrame(columns=API_KEYS_OF_INTEREST + ['background', 'video', 'posted'])

    for subreddit in subreddits:
        for type in REQUESTYPES:
            posts = get_posts(subreddit, type, args.number, args.token)

            posts = filter(lambda post: post['url'].endswith(ALLOWED_EXTENSIONS), posts) # Filter out non-image posts
    
            for post in posts:
            # Append the post to the dataframe
                frame = frame.append({key: post[key] for key in API_KEYS_OF_INTEREST} | {
            'background': '',
            'video': '',
            'posted': False
            }, ignore_index=True)

        frame.to_excel(args.meta, index=False)
    return frame


def download_subreddits(s: requests.Session, args, subreddits, frame, videos_per_category, backgrounds):
    """Downloads all the images from the subreddits"""
    # Downloads all the images
    for subreddit in subreddits:
        for cat in REQUESTYPES:
            # filters the dataframe to only include posts from the current subreddit and category
            posts = frame[(frame['subreddit'] == subreddit) & (frame['category'] == cat)]

            posts = posts.sample(videos_per_category) # Randomly samples the posts

            successful_downloads = posts.apply(lambda post: download_image(post, cat, s), axis=1)
            # Filters the posts again to only include posts that have been downloaded
            posts = posts[posts['image'] != ''] # -> Sucesfully downloaded

            # Makes the videos
            for i, post in enumerate(posts):
                extension = post['url'].split('.')[-1]
                save_path = f'tmp/{subreddit}_{cat}_{i}.{extension}'
                background = backgrounds.choice()

                make_video(subreddit, cat, posts, background, args.output, args.length) # TODO: Grep the output or something to see if it was successful

                # Updates the dataframe
                post['background'] = background
                post['video'] = f'{post["subreddit"]}_{cat}_{post["id"]}.mp4'

