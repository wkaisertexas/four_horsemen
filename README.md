# The Four Horsemen

This project came from the observation that Tik Tok contains four key horsemen: the "family guy clip", the "splitscreen", the "AITA" and the "comment section". During this project, I will be recreating all of these projects and recreating an account for each.

`FFMPEG` is the library which makes all of this possible and is required for the installation

## The Family Guy Clip

The family guy clip is a staple of the Tik Tok community. In this video, a clip of a movie, tv show or short is playing on the top of the screen and below, a clip of an overstaturated game (typically "Subway Surfers") plays below.

These clips have the following defining characteristics: 
- Averaging a minute in length
- Being a part of a series which leads to watch streaks
    - Parts overlapp by an average of 5 seconds
- The original clip is edited from it's 16:9 resolution to 4:3 to make it take up more space on the screen

## The MultiMeme

The MultiMeme is another staple of the Tik Tok community. Because one could never know which meme someone would actually like to watch. The multi-meme gets around this by displaying more than one meme at once in an attempt to hack the watch time algorithm. All in all, a dirty but effective trick.

These clips have the following defining characteristics:
- Background which is either someone pointing their phone at their desk or opening up their mouth in awe
- 1-4 memes are placed on the same screen without regard for consistent spacing or sizing
- Between 15 and 30 seconds in length

## Tik Tok Notes
Videos uploaded are in 1080p, but 1080x1920 versus the traditional 1920x1080.

## Future Work

The end goal of this project is to create a web-based tool which uses [FFmpeg.js](https://github.com/Kagami/ffmpeg.js/) and the [Tik Tok API](https://developers.tiktok.com/doc/web-video-kit-with-web/) 

## Scheduling Uploads

Uploads can be schedule with either a `schtasks.exe` job or a `cron` job if you are on Windows or MacOS and Linux, repectively.

- [Windows Guide for Scheduling Tasks](https://active-directory-wp.com/docs/Usage/How_to_add_a_cron_job_on_Windows/Scheduled_tasks_and_cron_jobs_on_Windows/index.html)
- [Cron Scheduling](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)

### Sample Commands

#### Windows
```powershell
schtasks.exe /create /tn upload /sc daily /st 13:00 /tr uploadVideo.py
```

This creates a daily task named `upload` which runs `uploadVideo.py` at 1:00pm

#### MacOS + Linux

Open your `crontab`
```bash
crontab -e 
```
Add the following command:
```bash
0 13 * * * python uploadVideo.py 
```
Save and exit the file

## TODOs

## References