from typing import List
import requests
import json
import subprocess
import os


def get_posts(subreddit: str, type: str, limit: int, api_key: str):
    url = f'https://www.reddit.com/r/{subreddit}/{type}.json?limit={limit}'

    print(f'Getting posts from {url}')
    headers = {'User-Agent': 'Mozilla/5.0'}
    if api_key: 
        r = requests.get(url, headers=headers, auth=api_key, timeout=20)
    else:
        r = requests.get(url, headers=headers, timeout=20)
    body = json.loads(r.text)

    return list(map(
               lambda x: x.get('data', {}),
               body.get('data', {}).get('children', [])
            )) # Destructures into post-level data


def download_image(url: str) -> bool:
    '''Downloads the image from the post'''

    # Starts downloading the image
    req = requests.get(url, timeout=20)

    save_path = f'tmp/{url.split("/")[-1]}'

    if req.status_code != 200:
        print(f'Failed to download {url}')
        return False

    # Saves the image
    with open(save_path, 'wb') as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return True


def get_dimensions(post_url: str):
    '''Gets the dimensions of the post'''
    output = subprocess.Popen(f'ffprobe -i tmp/{post_url}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0].decode('utf-8')

    return tuple(map(int, output.split('Video:')[1].split(',')[1].split(' ')[1].split('x')))