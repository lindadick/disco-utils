#compress_disco_wavs_to_mp3.py

import os
import glob
import string
from pydub import AudioSegment
from time import localtime, strftime

ENCODER_FORMAT = "mp3"
ENCODER_COMMENT = "Encoded from the Robinet Disco " + strftime("%Y-%m-%d", localtime())

DISCO_DIR = os.path.join(os.sep, "home", "pi", "disco")
ENCODED_DIR = os.path.join(os.sep, "mnt", "external1", "DiscoFilesEncoded", ENCODER_FORMAT)
DATA_DIR = os.path.join(DISCO_DIR, "Data")
MEDIA_DIR = os.path.join(DISCO_DIR, "Media")

FOLDER_STYLE = "flat"

def get_disc_info(disc_number):
    data_file_path = os.path.join(DATA_DIR, "cd" + '{0:04d}'.format(disc_number))
    try:
        f = open(data_file_path)
        disc_artist = f.readline().strip()
        disc_title = f.readline().strip()
        disc_meta = f.readline().strip()
        disc = { 'artist': disc_artist,
                 'title': disc_title,
                 'disc_number': disc_number,
                 'online_tracks': 0
                 }
        disc['tracks'] = []
        track_artist = f.readline().strip()
        track_number = 1
        while track_artist != "":        
            track_title = f.readline().strip()
            track_meta = f.readline().strip().split(' ')
            track_runtime = track_meta[0]
            track_shortlist = True if track_meta[1] == 'S' else False
            track_online = True if track_meta[3] == '1' else False
            disc['tracks'].append({'artist': track_artist,
                                   'title': track_title,
                                   'runtime': track_runtime,
                                   'shortlist': track_shortlist,
                                   'online': track_online,
                                   'track_number': track_number
                                   })
            if track_online:
                disc['online_tracks'] += 1
            # Read ahead for next track
            track_artist = f.readline().strip()
            track_number += 1
        f.close()
    except IOError:
        print("Cannot find file: " + data_file_path)

    return disc

def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
Uses a whitelist approach: any characters not present in valid_chars are
removed. Also spaces are replaced with underscores.
 
Note: this method may produce invalid filenames such as ``, `.` or `..`
When I use this method I prepend a date string like '2009_01_15_19_46_32_'
and append a file extension like '.txt', so I avoid the potential of using
an invalid filename.

https://gist.github.com/seanh/93666 
"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

def create_track_symlinks(disc, track, track_number_string, real_file_path):
    encoded_path_flat = os.path.join(ENCODED_DIR, 'flat', disc['artist'])
    encoded_path_folders = os.path.join(ENCODED_DIR, 'folders', disc['artist'], disc['title'])

    if not os.path.isdir(encoded_path_flat):
        os.makedirs (encoded_path_flat)

    if not os.path.isdir(encoded_path_folders):
        os.makedirs (encoded_path_folders)

    if disc['artist'] == "Various Artists":
        track_title = track['artist'] + " - " + track['title']
    else:
        track_title = track['title']

    encoded_filename_flat = format_filename(disc['artist'] + " - " + disc['title'] + " - " + track_number_string + " - " + track_title) + "." + ENCODER_FORMAT
    encoded_filename_folders = format_filename(track_number_string + " - " + track_title) + "." + ENCODER_FORMAT
    encoded_filepath_flat = os.path.join(encoded_path_flat, encoded_filename_flat)
    encoded_filepath_folders = os.path.join(encoded_path_folders, encoded_filename_folders)
    if not os.path.islink(encoded_filepath_flat):
        os.symlink(real_file_path, encoded_filepath_flat)
    if not os.path.islink(encoded_filepath_folders):
        os.symlink(real_file_path, encoded_filepath_folders)    

#def add_album_art(disc, track, track_number_string, real_file_path):
    # TODO create from https://github.com/amorphic/coverlovin/blob/master/coverlovin/coverlovin.py

for root, subdirs, files in os.walk(DATA_DIR):
    for filename in files:
        disc_number = int(filename.replace("cd", ""))
        disc = get_disc_info(disc_number)
        if disc['online_tracks'] > 0:
            encoded_path = os.path.join(ENCODED_DIR, 'numbered')
            disc_number_string = '{0:04d}'.format(disc_number)
            print("Processing disc " + disc_number_string + " in " + encoded_path)
            if not os.path.isdir(encoded_path):
                os.makedirs (encoded_path)
            for track in disc['tracks']:
                if track['online']:
                    track_number_string = '{0:02d}'.format(track['track_number'])
                    disco_filename = disc_number_string + "_" + track_number_string
                    encoded_file_path = os.path.join(encoded_path, disco_filename) + "." + ENCODER_FORMAT
                    if not os.path.isfile(encoded_file_path):
                        wav_file_path = os.path.join(MEDIA_DIR, disco_filename + ".wav")
                        wav_file_size = os.path.getsize(wav_file_path)
                        if wav_file_size < 150000000:
                            # Only encode if file is < 150MB (otherwise we will get a MemoryError)
                            print(strftime("%T", localtime()) + ": Encoding " + encoded_file_path)
                            track_audio = AudioSegment.from_wav(wav_file_path)
                            track_audio.export(encoded_file_path,
                                           format = ENCODER_FORMAT,
                                           bitrate = "128k",
                                           tags={
                                               'artist': track['artist'],
                                               'album': disc['title'],
                                               'title': track['title'],
                                               'track': track_number_string,
                                               'comment': ENCODER_COMMENT
                                               })
                            print(strftime("%T", localtime()) + ": Encoding done")
                            create_track_symlinks(disc, track, track_number_string, encoded_file_path)
#                            add_album_art(disc, track, track_number_string, encoded_file_path)
                        else:
                            print("- Skipping " + wav_file_path + " - source file too large")
                    else:
                        print("- Skipping " + encoded_file_path + " - file exists")
                        # Temporarily re-create symlinks and add album art - this can be removed after first successful run.
                        create_track_symlinks(disc, track, track_number_string, encoded_file_path)
#                        add_album_art(disc, track, track_number_string, encoded_file_path)

    print("Done.")
