#! /usr/bin/python3
# update_all_id3_tags.py

import os
import glob
import string

from common_utils import get_disc_info, insert_id3_tags, DATA_DIR

for root, subdirs, files in os.walk(DATA_DIR):
    files.sort()
    for filename in files:
        disc_number = int(filename.replace('cd', ''))
        disc = get_disc_info(disc_number)
        if disc['online_tracks'] > 0:
            for track in disc['tracks']:
                if track['online']:
                    insert_id3_tags(disc_number, track['track_number'], track['artist'], track['title'], disc['title'])
print('Done.')