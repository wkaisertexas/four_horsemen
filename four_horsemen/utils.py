'''
Utility functions for the four horsemen 
'''
import json
import subprocess
from typing import List

import requests


def get_posts(subreddit: str, post_type: str, limit: int, api_key: str) -> List[dict]:
    '''
    Gets the posts from the subreddit
    '''
    url = f'https://www.reddit.com/r/{subreddit}/{post_type}.json?limit={limit}'

    print(f'Getting posts from {url}')
    headers = {'User-Agent': 'Mozilla/5.0'}
    if api_key:
        posts = requests.get(url, headers=headers, auth=api_key, timeout=20)
    else:
        posts = requests.get(url, headers=headers, timeout=20)
    body = json.loads(posts.text)

    return list(map(
                lambda x: x.get('data', {}),
                body.get('data', {}).get('children', []))
            )


def download_image(url: str) -> bool:
    '''Downloads the image from the post'''

    image = requests.get(url, timeout=20)

    save_path = f'tmp/{url.split("/")[-1]}'

    if image.status_code != 200:
        print(f'Failed to download {url}')
        return False

    with open(save_path, 'wb') as file:
        for chunk in image.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

    return True


def get_dimensions(file_path: str):
    '''Gets the dimensions of the post'''
    output = subprocess.Popen(
        f'ffprobe -i {file_path}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
        ).communicate()[0].decode('utf-8')

    dimensions_line = output.rsplit('Video:', maxsplit=1)[-1].split(',')[2].split(' ')[-1].strip()
    dimensions_line = dimensions_line[:dimensions_line.find(' ')]

    return tuple(map(int, dimensions_line.split('x')))

def get_length(file_path: str):
    '''Get the length of a video or audio file'''
    output = subprocess.Popen(
        f'ffprobe -i {file_path}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    ).communicate()[0].decode('utf-8')

    seg = output.split('Duration:')[1].split(',')[0].split(':')
    return int(seg[0]) * 3600 + int(seg[1]) * 60 + float(seg[2])
