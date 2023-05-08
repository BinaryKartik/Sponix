from flask import Blueprint, jsonify, render_template, redirect, url_for, request
import json
from flask.helpers import flash
import urllib.request
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from difflib import SequenceMatcher
import spotipy
import re
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
from werkzeug.security import generate_password_hash, check_password_hash
import pafy
from flask_login import login_user, login_required, logout_user, current_user
from flask_login import UserMixin
from bs4 import BeautifulSoup
import pymongo
import os, sys
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from flask_cors import cross_origin

cluster = MongoClient(os.environ.get("dbauth"), connect=False)
db = cluster["sponix"]

collection = db["login-user"]
playlistdb = db["playlists"]

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get("spotify-id"),
    client_secret=os.environ.get("spotify-secret")))


class User(UserMixin):
    def __init__(self, email, name, password, sign_up=True):
        super().__init__()
        if sign_up == True:
            find = collection.find_one({"Type": "ids"})
            id = find["value"]
            post = {
                "_id": id,
                "Name": name,
                "Email": email,
                "Password": password,
                "Playlists": []
            }
            collection.insert_one(post)
            collection.update_one({"_id": 0}, {"$inc": {"value": 1}})
        else:
            self.email = email
            obj = collection.find_one({"Email": email})
            self.id = obj["_id"]
            self.name = obj["Name"]
            self.admin = False
            try:
                if obj["Admin"]:
                    self.admin = True
            except:
                pass
            self.password = obj["Password"]
            self.playlists = obj["Playlists"]


auth = Blueprint('auth', __name__)

song = ''
repeat = 0


def rclyrics(s):
    try:
        s += " lyrics"
        s.replace(" ", "%20")
        html = requests.get(f"https://rclyricsband.com/?s={s}").text
        print(f"https://rclyricsband.com/?s={s}")
        soup = BeautifulSoup(html, features="html.parser")
        data = soup.find(class_='elementor-post__title')
        data = data.find("a")["href"]
        print(data)
        hi = soup.find(class_='elementor-post__title').find("a").text
        m = SequenceMatcher(None, hi, s).ratio()
        print(hi.replace("PDF/LRC File", "") ,s, sep="\n")
        if (0.55 < m) or (s.lower() in hi.lower()):
            html = requests.get(data).text
            soup = BeautifulSoup(html, features="html.parser")
            data = soup.find(class_='su-box-content su-u-clearfix su-u-trim').text
            backup = data
            lrc = []
            while data.find('[') != -1:
                lrc.append(data[data.find('[') + 1:data.find(']')])
                data = data.replace("[" + lrc[len(lrc) - 1] + "]", "")
            for i in range(lrc.index("00:00.00")):
                lrc.pop(0)
            lrc2 = []
            z = 0
            for t in lrc:
                z += 1
                try:
                    lrc2.append(backup[backup.find(t) + len(t) +
                                    1:backup.find(lrc[z]) - 1])
                except:
                    break
            lrc.pop(0)
            if lrc2[0] == "":
                lrc2.pop(0)
        else:
            lrc2 = lrc= False
    except Exception as e:
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       print(e,exc_type, fname, exc_tb.tb_lineno) 
       lrc2 = lrc= False
    return lrc2, lrc


def lyricsify(s, art, s3):
    try:
        art2 = art.replace(" ", "-")
        html = requests.get(f"https://www.lyricsify.com/lyrics/{art2}",
                            headers={
                                'Accept': 'application/xml; charset=utf-8',
                                'User-Agent': 'foo'
                            }).text
        soup = BeautifulSoup(html, features="html.parser")
        data = soup.find_all(class_="li")
        data2 = []
        for t in data:
            data2.append(t.find("a").text)
        t = 0
        ans = ""
        for i in data2:
            if s in i:
                ans = i
                t = 0.7
                break
            else:
                s2 = i.replace(f"{art} - ", "")
                m = SequenceMatcher(None, s2, s).ratio()
                if t < m:
                    t = m
                    ans = i
        link = data[data2.index(ans)]
        if t < 0.6:
            return rclyrics(s)
        else:
            return next2(link)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)
        return False,False


def next2(link):
    try:
        link = link.find("a")["href"]
        print(link)
        html = requests.get("https://www.lyricsify.com/" + link,
                            headers={
                                'Accept': 'application/xml; charset=utf-8',
                                'User-Agent': 'foo'
                            }).text
        soup = BeautifulSoup(html, features="html.parser")
        id = link[::-1].split(".")
        id = id[0][::-1]
        data = soup.find(id='lyrics_' + id + "_details").text
        data2 = data.split("\n")
        final = []
        m2 = []
        for m in data2:
            try:
                if (data2[0][data2[0].find('[') + 1:data2[0].find(']')][2] == ":") and (data2[0][data2[0].find('[') + 1:data2[0].find(']')][5] == "."):
                    break
                else:
                    data2.pop(0)
            except:
                data2.pop(0)
        print(data2)
        for i in data2:
            final.append(i[i.find('[') + 1:i.find(']')])
            try:
                i = i.split("]")[1]
                m2.append(i)
            except Exception as e:
                print(e)
                print(i)
        final2 = []
        print(m2, "m2")
        for s in m2:
            if s == " ":
                final2.append("")
            else:
                final2.append(s)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
    print(final2, final, sep="\n")
    return final2, final


def get_song(song):
    try:
        name =sp.search(song, type='track',  market="IN", limit=1)
        art = name["tracks"]['items'][0]['artists'][0]['name']
        sng = name["tracks"]['items'][0]['name']
        img = name["tracks"]['items'][0]['album']['images'][0]['url']
        if "Various Artist" in art:
            print("hello")
            art = art[0]
        base = 'https://www.youtube.com/watch?v='
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + song.replace(" ", "%20"))
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        link = base + video_ids[0]
        audio = pafy.new(link)
        duration = audio.length
        best = audio.getbestaudio()
        playurl = best.url
        # repeat = 0
        # srt = YouTubeTranscriptApi.get_transcript(suffix)
        # print(views, name, publish, date, playurl, img)
        # if type(views) != str:
        #   raise Exception("No song found")
        return sng, art, playurl, img, duration
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        # get_song(song + keywords[repeat])


@auth.route('/songs', methods=['GET', 'POST'])
def songs():
    global song
    if request.method == 'POST':
        print('pass1')
        if current_user.is_authenticated:
            print('pass2')
            song = request.form.get('song')
            try:
                name, publish, playurl, img, duration = get_song(song)
                lcs2, lcs = lyricsify(
                    name,
                    publish, song)
                if lcs:
                  for m in lcs2:
                   if not (bool(re.match('^[ ]+$', m)) or m == ""):
                    if lcs2.count(m) > 1:
                      print(lcs2.count(m), m)
                      for s in range(0, lcs2.count(m)):
                        lcs2[lcs2.index(m)] = m+(" "*s)
                else:
                   lcs = lcs2 = "NO"  
                    # if len(lcs2) == len(lcs):
                    #   if bool(re.match('^[ ]+$', m)) or m == "":
                    #     lcs2.pop(lcs2.index(m))
                    #     lcs.pop(lcs2.index(m))
                    #     print("balle balle")
                return render_template('song.html',
                                       user=current_user,
                                       song=song,
                                       name=name,
                                       publish=publish,
                                       lcs=lcs,
                                       lcs2=lcs2,
                                       url=playurl,
                                       img=img,
                                       index="index.js")
            except Exception as i:
                print(i)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                error = 'No song found, please try again with exact name or another song.'
                return render_template('song.html',
                                       song=song,
                                       error=error,
                                       index="index.js",
                                       user=current_user)
        else:
            email_login = request.form.get("email")
            pass_login = request.form.get("pass")
            find_login = collection.find_one({"Email": email_login})
            if find_login == None:
                flash("Wrong Email")
            elif check_password_hash(find_login["Password"], pass_login):
                user = User(email=email_login,
                            name=None,
                            password=None,
                            sign_up=False)
                login_user(user, remember=True)
            else:
                flash("Wrong Password")
            return render_template('song.html',
                                   index="index.js",
                                   user=current_user)
    else:
        return render_template('song.html',
                               index="index.js",
                               user=current_user)


@auth.route('/playlists', methods=['GET', 'POST'])
def playlists():
    if request.method == 'POST':
        playlist_link = request.form.get("playlist")
        playlist_id = playlist_link.split('/')
        json_object = json.dumps(sp.playlist(playlist_id[-1]), indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)
        result = sp.playlist(playlist_id[-1])
        playlist_songs_spotify = []
        for i in result["tracks"]["items"]:
            if not "artist" in i["track"]["album"]["artists"][0]["name"]:
                playlist_songs_spotify.append(
                    i["track"]["name"] + " by " +
                    i["track"]["album"]["artists"][0]["name"])
            else:
                playlist_songs_spotify.append(i["track"]["name"])
        playlistdb.insert_one({
            "Name": result["name"],
            "User-id": current_user.id,
            "Songs": playlist_songs_spotify
        })
        collection.update_one({"User-id": current_user.id},
                              {"$push": {
                                  "Playlists": result["name"]
                              }})
    return render_template('playlists.html',
                           index="index.js",
                           user=current_user,
                           playlists=current_user.playlists)


@auth.route('/playlists/add/<name>')
def playlists_add(name):
    playlistdb.update_one(
        {
            "Name": current_user.playlists[0],
            "User-id": current_user.id
        }, {"$push": {
            "Songs": name
        }})
    return redirect("/playlists/play/MyPlaylist")


@auth.route('/playlists/remove/<name>/<list>')
def playlists_remove(name, list):
    playlistdb.update_one({
        "Name": list,
        "User-id": current_user.id
    }, {"$pull": {
        "Songs": name
    }})
    list.replace(" ", "%20")
    return redirect("/playlists/play/" + list)


@auth.route('/songs/<song_name>')
@cross_origin(supports_credentials=True)
def songs_find(song_name):
    if '%20' in song_name:
        song_name = song_name.replace('%20', ' ')
    try:
        name, publish, playurl, img, duration, = get_song(song_name)
        return jsonify({
            "song": song,
            "name": name,
            "publish": publish,
            "url": playurl,
            "img": img
        })
    except Exception as i:
        print(i)
        error = 'No song found, please try again with exact name or another song.'
        return jsonify({"error": error})


@auth.route('/playlists/play/<playlist>')
def playlists_play(playlist):
    if len(current_user.playlists) > 0:
        if playlistdb.find_one({"Name": playlist, "User-id": current_user.id}):
            db_song_names = (playlistdb.find_one({
                "Name": playlist,
                "User-id": current_user.id
            }))["Songs"]
            songs = db_song_names
            return render_template('playlist_player.html',
                                   songs=songs,
                                   index="index.js",
                                   user=current_user,
                                   play=playlist)
        else:
            return "This playlist wasn't found in your account"
    else:
        return 'No playlists found.'


@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        name = request.form.get('firstName')
        email = request.form.get('email')
        password = request.form.get('password1')
        password2 = request.form.get('password2')
        if collection.find_one({"Email": email}) != None:
            flash("Email already exists. PLease Login.")
        elif password != password2:
            flash("Passwords do not match.")
        else:
            password_enc = generate_password_hash(password, method='sha256')
            new_user = User(email=email, name=name, password=password_enc)
            login_user(new_user, remember=True)
    return render_template('sign_up.html', index="index.js", user=current_user)
