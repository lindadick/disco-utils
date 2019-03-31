import os
import string
import plyr
import shutil
from pydub import AudioSegment
from time import localtime, strftime
from mutagen.id3 import ID3, TPE1, TIT2, TRCK, TALB, APIC, TDEN, TDTG, ID3NoHeaderError

DEBUG = True

DISCO_DIR = os.path.join(os.sep, 'home', 'pi', 'disco')
ART_DIR = os.path.join(DISCO_DIR, 'Art')
DATA_DIR = os.path.join(DISCO_DIR, 'Data')
MEDIA_DIR = os.path.join(DISCO_DIR, 'Media')
ENCODED_DIR = os.path.join(DISCO_DIR, 'Encoded')
USER_AGENT = 'disco-utils/1.0 +(https://github.com/lindadick)'
ENCODER_FORMAT = 'mp3'
IMAGE_FORMAT = 'png'
ENCODED_PATH_NUMBERED = os.path.join(ENCODED_DIR, 'numbered')
ENCODED_PATH_FLAT = os.path.join(ENCODED_DIR, 'flat')
ENCODED_PATH_FOLDERS = os.path.join(ENCODED_DIR, 'folders')

def format_track_number_string(track_number):
    return '{0:02d}'.format(track_number)

def format_disc_number_string(disc_number):
    return '{0:04d}'.format(disc_number)

def delete_all_symlinks():
    if os.path.isdir(ENCODED_PATH_FLAT):
        shutil.rmtree(ENCODED_PATH_FLAT)
    if os.path.isdir(ENCODED_PATH_FOLDERS):
        shutil.rmtree(ENCODED_PATH_FOLDERS)

def create_track_symlinks(disc_number, track_number, artist, title, album_artist, album_title):
    encoded_path_flat = os.path.join(ENCODED_PATH_FLAT, album_artist)
    encoded_path_folders = os.path.join(ENCODED_PATH_FOLDERS, album_artist, album_title)
    disc_number_string = format_disc_number_string(disc_number)
    track_number_string = format_track_number_string(track_number)
    real_file_path = os.path.join(ENCODED_PATH_NUMBERED, disc_number_string + '_' + track_number_string + '.' + ENCODER_FORMAT)
    if DEBUG:
        print("Creating symlinks for " + real_file_path)
    if not os.path.isdir(encoded_path_flat):
        os.makedirs (encoded_path_flat)
    if not os.path.isdir(encoded_path_folders):
        os.makedirs (encoded_path_folders)

    if album_artist == 'Various Artists':
        track_title = artist + ' - ' + title
    else:
        track_title = title

    track_number_string = format_track_number_string(track_number)
    encoded_filename_flat = format_filename(album_artist + ' - ' + album_title + ' - ' + track_number_string + ' - ' + track_title) + '.' + ENCODER_FORMAT
    encoded_filename_folders = format_filename(track_number_string + ' - ' + track_title) + '.' + ENCODER_FORMAT
    encoded_filepath_flat = os.path.join(encoded_path_flat, encoded_filename_flat)
    encoded_filepath_folders = os.path.join(encoded_path_folders, encoded_filename_folders)
    if not os.path.islink(encoded_filepath_flat):
        os.symlink(real_file_path, encoded_filepath_flat)
    if not os.path.islink(encoded_filepath_folders):
        os.symlink(real_file_path, encoded_filepath_folders)    

def format_filename(s):
    '''Take a string and return a valid filename constructed from the string.
Uses a whitelist approach: any characters not present in valid_chars are
removed. Also spaces are replaced with underscores.
 
Note: this method may produce invalid filenames such as ``, `.` or `..`
When I use this method I prepend a date string like '2009_01_15_19_46_32_'
and append a file extension like '.txt', so I avoid the potential of using
an invalid filename.

https://gist.github.com/seanh/93666 
'''
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

def encode_track(disc_number, track_number, artist, title, album_artist, album_title):
    if not os.path.isdir(ENCODED_PATH_NUMBERED):
        os.makedirs (ENCODED_PATH_NUMBERED)
    disc_number_string = format_disc_number_string(disc_number)
    track_number_string = format_track_number_string(track_number)
    if DEBUG:
        print('Processing disc ' + disc_number_string)
    disco_file_prefix = disc_number_string + '_' + track_number_string
    encoded_file_path = os.path.join(ENCODED_PATH_NUMBERED, disco_file_prefix) + '.' + ENCODER_FORMAT
    if not os.path.isfile(encoded_file_path):
        wav_file_path = os.path.join(MEDIA_DIR, disco_file_prefix + '.wav')
        wav_file_size = os.path.getsize(wav_file_path)
        if wav_file_size < 150000000:
            # Only encode if file is < 150MB (otherwise we will get a MemoryError)
            if DEBUG:
                print(strftime('%T', localtime()) + ': Encoding ' + encoded_file_path)
            track_audio = AudioSegment.from_wav(wav_file_path)
            track_audio.export(encoded_file_path, format = ENCODER_FORMAT, bitrate = '128k')
            if DEBUG:
                print(strftime('%T', localtime()) + ': Encoding done')
            insert_id3_tags(disc_number, track_number, artist, title, album_title)
            create_track_symlinks(disc_number, track_number, artist, title, album_artist, album_title)
        else:
            print('- Skipping ' + wav_file_path + ' - source file too large')
    else:
        if DEBUG:
            print('- Skipping ' + encoded_file_path + ' - file exists')

def insert_id3_tags(disc_number, track_number, artist, title, album):
    disc_number_string = format_disc_number_string(disc_number)
    track_number_string = format_track_number_string(track_number)
    disco_filename = disc_number_string + '_' + track_number_string
    encoded_file_path = os.path.join(ENCODED_PATH_NUMBERED, disco_filename + '.' + ENCODER_FORMAT)
    if os.path.isfile(encoded_file_path):
        if DEBUG:
            print("Updating ID3 tags for " + encoded_file_path)
        try: 
            audio = ID3(encoded_file_path)
        except ID3NoHeaderError:
            print("Adding ID3 header")
            audio = ID3()        
        audio['TPE1'] = TPE1(encoding=3, text=artist)
        audio['TIT2'] = TIT2(encoding=3, text=title)
        audio['TRCK'] = TRCK(encoding=3, text=track_number_string)
        audio['TALB'] = TALB(encoding=3, text=album)
        audio['TDTG'] = TDTG(encoding=3, text=strftime('%Y-%m-%d %H:%M:%S %z', localtime()))
        if not 'TDEN' in audio: 
            # Only include the encoding time the first time we tag the file
            audio['TDEN'] = TDEN(encoding=3, text=strftime('%Y-%m-%d %H:%M:%S %z', localtime()))
        album_art_path = os.path.join(ART_DIR, disc_number_string + '.' + IMAGE_FORMAT)
        if os.path.isfile(album_art_path):
            with open(album_art_path, 'rb') as albumart:
                audio['APIC'] = APIC(
                                encoding=3,
                                mime='image/' + IMAGE_FORMAT,
                                type=3, desc=u'Cover',
                                data=albumart.read()
                                )            
        return audio.save(encoded_file_path)
    return False

def download_album_art(disc_number, artist, album, replace_existing):
    disc_number_string = format_disc_number_string(disc_number)
    art_file_path = os.path.join(ART_DIR, disc_number_string + '.' + IMAGE_FORMAT)
    if replace_existing or not os.path.isfile(art_file_path):
        if DEBUG:
            print("Downloading art for " + art_file_path)
        qry = plyr.Query(artist=artist, album=album, get_type='cover', allowed_formats=[IMAGE_FORMAT])        
        qry.useragent = USER_AGENT
        items = qry.commit()
        if len(items) > 0:        
            items[0].write(art_file_path)
        else:
            print("Couldn't find art for disc " + disc_number_string + ' (' + artist + ' - ' + album + ')')

def get_disc_info(disc_number):
    data_file_path = os.path.join(DATA_DIR, 'cd' + '{0:04d}'.format(disc_number))
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
        while track_artist != '':        
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
        print('Cannot find file: ' + data_file_path)

    return disc
