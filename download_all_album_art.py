#! /usr/bin/python3
# download_all_album_art.py

import os
import glob
import string

from common_utils import get_disc_info, download_album_art, DATA_DIR

for root, subdirs, files in os.walk(DATA_DIR):
    files.sort()
    for filename in files:
        disc_number = int(filename.replace('cd', ''))
        disc = get_disc_info(disc_number)
        download_album_art(disc_number, disc['artist'], disc['title'], False)
print('Done.')
