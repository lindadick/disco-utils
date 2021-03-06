#! /usr/bin/python3
# compress_disco_wavs_to_mp3s.py

import os
import glob

from common_utils import download_album_art, encode_track, get_disc_info, DATA_DIR

for root, subdirs, files in os.walk(DATA_DIR):
    files.sort()
    for filename in files:
        disc_number = int(filename.replace('cd', ''))
        disc = get_disc_info(disc_number)
        download_album_art(disc_number, disc['artist'], disc['title'], False)
        if disc['online_tracks'] > 0:
            for track in disc['tracks']:
                if track['online']:
                    encode_track(disc_number, track['track_number'], track['artist'], track['title'], disc['artist'], disc['title'])
print('Done.')
