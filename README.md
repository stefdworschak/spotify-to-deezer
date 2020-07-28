# Spotify To Deezer

## Introduction

The contents of the `spotify_backup` folder with minor changes have been adapted from the [spotify_backup](https://github.com/caseychu/spotify-backup) repo.

The contents of the `deezer_upload` folder with some bigger modifications have been adapted from the [spotify-playlists-2-deezer](https://github.com/helpsterTee/spotify-playlists-2-deezer) repo.

The contents of the root folder have been created to link the two scripts in order to be able to run them as a cronjob in daily intervals.

## Main changes

### spotify_backup

1) Change to the scope to use both `playlist-read-collaborative` and `playlist-read-private` as default
2) Change to the format to use `json` as default

### spotify-playlists-2-deezer

1) The script requested user confirmation in the browser each time the script ran. To avoid this the scope was changed to include `offline_access` which means the token does not expire. It will also save the token in a file and retrieve the token from the file if it exists to avoid the prompt in the browser for every run.
2) The script was designed to only adding playlists if they are not already on the user's Deezer account. This did not allow for updating Deezer playlists if any songs are added to the Spotify playlist. In addition, if the song did not have an isrc code it was skipped. The script was adjusted to allow for updating existing playlists and added a backfall search by artist and track name to try and find songs without an isrc code.
3) Error logging was added to be able to add missing tracks manually and monitor the progresss when running as cronjob.

### compare_playlists

This is a completely new script which will create three `.txt` files. It will backup the current list of playlists (last.playlists.txt) if it exists, it will create a new list of playlists (playlists.txt) and it will create the difference between the last and the current list of playlists (new_playlists.txt) which will be used to update Deezer.

## Pre-requesists

### Accounts

- Spotify
- Deezer

### Software

- python3 and pip

## Installation

1) Clone the repository in a local folder

```
git clone git@github.com:stefdworschak/spotify-to-deezer.git && cd spotify-to-deezer
```

2) Install required pip modules

```
pip3 install -r requirements.txt 
```

3) Create a new Deezer application (instructions [here](https://github.com/helpsterTee/spotify-playlists-2-deezer#how-to-use))
4) Create a new secrets.py file in the root directory and add your Deezer Client ID, Client Secret and User ID (see example below)

```
import os

os.environ.setdefault('DEEZER_CLIENT_ID', '123456')
os.environ.setdefault('DEEZER_CLIENT_SECRET', '123asd123asd123asd123asd123asd123asd')
os.environ.setdefault('DEEZER_USER_ID', '123123123123')
```

3) Execute the script
```
./run_all.py
```
