#!/usr/bin/env python3
from spotify_backup.spotify_backup import main as export_from_spotify
from deezer_upload.upload_to_deezer import main as import_to_deezer
from compare_playlists import main as compare_playlists

import os
import secrets

if __name__ == '__main__':
    export_from_spotify()
    compare_playlists()
    import_to_deezer()