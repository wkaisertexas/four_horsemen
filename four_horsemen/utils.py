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


def download_image(post, cat, session: requests.Session) -> bool:
    '''Downloads the image from the post'''
    extension = post['url'].split('.')[-1]
    save_path = f'tmp/{post["subreddit"]}_{cat}_{post["id"]}.{extension}'

    # Starts downloading the image
    req = s.get(post['url'])

    if req.status_code != 200:
        print(f'Failed to download {post.get("url", "unknown")}')
        return False

    # Saves the image
    with open(save_path, 'wb') as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                
    # Updates the dataframe
    post['image'] = save_path
    return True


def get_dimensions(post):
    '''Gets the dimensions of the post'''
    output = subprocess.Popen(f'ffmpeg -i tmp/{i}.mp4', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0].decode('utf-8')
