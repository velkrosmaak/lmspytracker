#!/usr/bin/env python

from pylms.server import Server
from pylms.player import Player
import sqlite3
import time
import datetime

global playermacaddress
playermacaddress = "CHANGE_ME" #your Squeezebox playback device MAC address
global lmshost
lmshost = "192.168.0.110" #your Logitech Media Server host IP
global dbtablename
dbtablename = "CHANGE_ME" #the name of the table in the sqlite3 db. NB: the filename of the database is currently hardcoded on line 27
global pollinterval
pollinterval = 5 #how frequently we check to see if there is a new track playing
global prevtrack
prevtrack = "" #define the previous track so that you can check if the track has changed

def csvoutput(logfile, logstring):
    file = open(logfile + ".txt","a")
    file.write(logstring)
    file.close()

def connectsqlite3():
    global conn
    conn = sqlite3.connect('lmspytracks.db')

def connectserver(): #connect to the LMS server
    sc = Server(hostname=lmshost, port=9090, username="", password="")
    sc.connect()

    print "Logged in: %s" % sc.logged_in
    print "Version: %s" % sc.get_version()

    global sq
    sq = sc.get_player(playermacaddress)

    print "Name: %s \nMode: %s \nConnected: %s \nWiFi: %s" % (sq.get_name(), sq.get_mode(), sq.is_connected, sq.get_wifi_signal_strength())

def updateprevtrack():
    global prevtrack
    prevtrack = sq.get_track_artist().encode('utf-8')
    prevtrack += " - " + sq.get_track_current_title().encode('utf-8')

def getcurrenttitle(tablename): #get the current title of the playing track from LMS
    global prevtrack
    global timenow
    timenow = str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))

    currtrack = sq.get_track_artist().encode('utf-8')
    currtrack += " - " + sq.get_track_current_title().encode('utf-8')
    trackalbum = ""
    trackgenre = ""
    trackpath = ""

    if (currtrack != prevtrack):
        trackdiff = True
        #only show song info when its a new song to save api calls
        trackalbum = sq.get_track_album()
        trackgenre = sq.get_track_genre()
        trackpath = sq.get_track_path()
        writetosqlite3 (tablename, timenow, currtrack, trackalbum, trackgenre, trackpath)
        csvoutput (dbtablename,(timenow + "," + currtrack + "," + trackalbum + "," + trackgenre + "," + trackpath + "\n"))
    else:
        trackdiff = False

    return currtrack, trackalbum, trackgenre, prevtrack, trackpath, trackdiff

def writetosqlite3(tablename, timestamp2, currenttitle, currentalbum, currentgenre, currentpath): #write current track to sqlite3
    global conn
    global timenow
    c = conn.cursor()

    tblquery = "INSERT INTO "
    tblquery += tablename
    tblquery += (''' VALUES (?,?,?,?,?)''')
    c.execute(tblquery, (timestamp2,currenttitle,currentalbum,currentgenre,currentpath))
    conn.commit()

def createsqlite3table(tablename):
    global conn
    global pollinterval
    global dbtablename
    c = conn.cursor()

    try:
        query = "CREATE TABLE "
        query += tablename
        query += " (date text, trackname text, album text, genre text, trackpath text)"
        c.execute(query)
        conn.commit()
        print "INFO: Created new table " + tablename
    except:
        print "WARNING: Error creating sqlite3 table. The table probably already exists, which is cool."
        pass

def closesqlite3conn():
    conn.close()

###main script begins here - end of definitions###
connectsqlite3() #connect to sqlite3
connectserver() #connect to LMS
createsqlite3table(dbtablename)
while True: #main loop to constantly check for a new track and then act on it
    try:
        print getcurrenttitle(dbtablename)
        updateprevtrack()
        time.sleep(pollinterval)
    except KeyboardInterrupt:
        print "INFO: Forcefully ended the script. Closing sqlite3 connection"
        print "INFO: Saved file " + dbtablename + ".txt"
        closesqlite3conn()
        break
    except:
        print "ERROR: Something bad happened. Retrying in 30 seconds..."
        time.sleep(30)
