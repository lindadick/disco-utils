#! /usr/bin/python3
# recreate_all_symlinks.py

import os
import glob
import string

from common_utils import delete_all_symlinks, get_disc_info, create_track_symlinks, DATA_DIR

delete_all_symlinks()

for root, subdirs, files in os.walk(DATA_DIR):
    files.sort()
    for filename in files:
        disc_number = int(filename.replace('cd', ''))
        disc = get_disc_info(disc_number)
        disc_number_string = '{0:04d}'.format(disc_number)
        if disc['online_tracks'] > 0:
            for track in disc['tracks']:
                if track['online']:
                    create_track_symlinks(disc_number, track['track_number'], track['artist'], track['title'], disc['artist'], disc['title'])
print('Done.')