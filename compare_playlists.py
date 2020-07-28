#import enumerate
import json
from dateutil import parser
from os import path
import pprint
import pytz

PLAYLISTS_FILE = './playlists.txt'
LAST_PLAYLISTS_FILE = './last_playlists.txt'
NEW_PLAYLISTS_FILE = './new_playlists.txt'

def main():
    print('Comparing playlists...')
    with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as playlists_file:
        playlists = json.load(playlists_file)

    if not path.exists(LAST_PLAYLISTS_FILE):
        save_file(playlists, NEW_PLAYLISTS_FILE)
        return

    prev_playlists = {}
    with open(LAST_PLAYLISTS_FILE, 'r', encoding='utf-8') as playlists_file:
        last_playlists = json.load(playlists_file)

    for playlist in last_playlists:
        tracks = playlist.get('tracks')
        track_ids = []
        for track in tracks:
            track_ids.append(track.get('track').get('id'))
        new_playlist = {playlist.get('id'): track_ids}
        prev_playlists.update(new_playlist)

    kept_playlists = []
    for playlist in playlists:
        kept_tracks = []
        for track in playlist.get('tracks'):
            prev_playlist = prev_playlists.get(playlist.get('id'))
            if prev_playlist is None or track.get('track').get('id') not in prev_playlist:
                kept_tracks.append(track)
        playlist['tracks'] = kept_tracks
        if len(kept_tracks) > 0:
            kept_playlists.append(playlist)

    save_file(kept_playlists, NEW_PLAYLISTS_FILE)
    print('Done.')


def save_file(data, filename):
    with open(filename, 'w+', encoding='utf-8') as output_file:
        json.dump(data, output_file)

if __name__ == '__main__':
    main()