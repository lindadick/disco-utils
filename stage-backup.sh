#!/bin/bash
# MUST BE RUN AS ROOT!

# Synchronize important files to backup-staging directory, to be picked up by plex server and ultimately backed up to off-site storage.
rsync -avzh /lib/systemd/system/disco-* /etc /home/git/gogs /home/pi/disco/disco.cfg /home/pi/disco/disco_local.h /mnt/external1/gogs-repositories /mnt/external1/backup-staging

# Dump GoGs database to backup-staging directory
/usr/bin/sqlite3 /mnt/external1/gogs-sqlite3-data/gogs.db .dump > /mnt/external1/backup-staging/gogs-dbbackup.bak

# Make everything accessible to the Pi user
chown -R pi.users /mnt/external1/backup-staging
