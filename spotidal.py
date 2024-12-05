import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import sqlite3
import hashlib
from pathlib import Path
import tidalapi
import jellyfish
import re
import time
import os

load_dotenv(override=True)

remastered_regex = r"^(.+) [(\[\/\-][^()\[\]]*?re-?mastere?d?[^)\[\]]*?([)\]\-\/]|$)"



def print_divider():
    print("====================")
  


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


class SpotifyHelper:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ['SPOT_CLIENT_ID'],
                                               client_secret=os.environ['SPOT_CLIENT_SECRET'],
                                               redirect_uri='http://127.0.0.1:8084',
                                               scope="playlist-read-private playlist-modify-private playlist-read-collaborative playlist-modify-public user-library-read user-library-modify",
                                               open_browser=False),
                                               requests_timeout=10, retries=5
                                               )
        pass


    def create_playlist(self, name):
        try:
            playlist =self.sp.user_playlist_create(user=self.sp.me()['id'], name=name, public=False)
            return playlist["id"]
        except:
            print("Error while creating playlist!")

    def spotify_get_user_playlists(self):
        playlists = list()
        max_playlists = int(os.environ['MAX_PLAYLIST_COUNT'])
        for offset in range(0, max_playlists, 50):
            results = self.sp.current_user_playlists(limit=50, offset=offset)
            items = results['items']
            for item in items:
                if item is None:
                    pass
                elif item['owner']['id'] != self.sp.me()['id']:
                    pass
                else:
                    track = item['name']
                    id = item['id']
                    playlist = {
                        "name": track,
                        "id": id,
                    }
                    playlists.append(playlist)
        return playlists
    
    def search_song(self, song, artist):
        results = self.sp.search(q='artist:' + artist + ' track:' + song, type='track', limit=7)
        tracks = list()
        for idx, track in enumerate(results['tracks']['items']):
            if track["is_playable"] == False:
                continue
            else: tracks.append({
                "id": track['id'],
                "title": track['name'],
                "artist": track['artists'][0]['name'],
                "album": track['album']['name'],
                "popularity": track['popularity']
            })
        return tracks


    def get_liked_songs(self):
        print(color.PURPLE, "Obtaining Spotify <3-Songs...", color.END)
        tracks = list()
        for offset in range(0, 4000, 50):
            for track in (self.sp.current_user_saved_tracks(limit=50, offset=offset))['items']:
                tracks.append({
                    "id": track['track']['id'],
                    "title": track['track']['name'],
                    "artist": track['track']['artists'][0]['name'],
                    "album": track['track']['album']['name'],
                    "popularity": track['track']['popularity']
                })
        return tracks


    def add_song_to_liked_songs(self, song_id):
        self.sp.current_user_saved_tracks_add([song_id])
    

    def add_song_to_playlist(self, playlist_id, song_id):
        self.sp.user_playlist_add_tracks(user=self.sp.me()['id'], playlist_id=playlist_id, tracks=[song_id])

    def spotify_get_playlist(self, id):
        print(color.PURPLE, "Obtaining Spotify playlist...", color.END)
        tracks = list()
        for offset in range(0, 8000, 50):
            playlist = self.sp.playlist_tracks(playlist_id=id, limit=50, offset=offset)
            for track in playlist["items"]:
                if track is None:
                    pass
                else:
                    artists = list()
                    for artist in track["track"]["artists"]:
                        if artist is None:
                            pass
                        else:
                            artists.append(artist["name"])
                    tracks.append({
                        "id": track["track"]["id"],
                        "title": track["track"]["name"],
                        "artist": ', '.join(artists)
                    })
        return tracks
        
        
def hash_list(list_to_hash):
    hash_object = hashlib.sha256(str(list_to_hash).encode())
    return hash_object.hexdigest()

class TidalHelper:
    def __init__(self):
        self.session_file1 = Path("tidal-session-oauth.json")
        self.session = tidalapi.Session()
        self.session.login_session_file(self.session_file1)
        pass
        
    def search_song(self, song, artist):
        results = self.session.search(song + " " + artist, [tidalapi.media.Track], limit=15)
        tracks = list()
        for idx, track in enumerate(results["tracks"]):
            if track is results["top_hit"]:
                top_hit = True
            else: top_hit = False
            tracks.append({
                "id": track.id,
                "title": track.name,
                "artist": track.artist.name,
                "album": track.album.name,
                "popularity": track.popularity,
                "top_hit": top_hit,
            })
        return tracks

    def get_liked_songs(self):
        print(color.PURPLE, "Obtaining TIDAL <3-Songs...", color.END)

        tracks = list()
        for offset in range(0, 8000, 1000):
            for track in self.session.user.favorites.tracks(limit=1000, offset=offset):
                tracks.append({
                    "id": track.id,
                    "title": track.name,
                    "artist": track.artist.name,
                    "album": track.album.name,
                    "popularity": track.popularity,
                })
        return tracks


    def get_playlists(self):
        playlists = list()
        for playlist in self.session.user.playlists():
            tracks = list()
            for track in playlist.tracks():
                tracks.append({
                    "id": track.id,
                    "title": track.name,
                    "artist": track.artist.name
                })
                # print(track.name, track.artist.name)
            playlists.append({
                "id": playlist.id,
                "name": playlist.name, 
                "hash": hash_list(tracks)
            })
        return playlists
    

    def add_song_to_playlist(self, playlist_id, song_id):
        self.session.playlist(playlist_id).add([song_id])

    
    def add_song_to_liked_songs(self, song_id):
        self.session.user.favorites.add_track(song_id)

    def get_playlist(self, id):
        print(color.PURPLE, "Obtaining TIDAL playlist...", color.END)
        playlist = self.session.playlist(id)
        tracks = list()
        for offset in range(0, 8000, 1000):
            for track in playlist.tracks(limit=1000, offset=offset):
                tracks.append({
                    "id": track.id,
                    "title": track.name,
                    "artist": track.artist.name
                })
        return tracks

    def create_playlist(self, name):
        try:
            playlist = self.session.user.create_playlist(title=name, description="Created by SpoTIDAL")
            return playlist.id
        except:
            print("Error while creating TIDAL-playlist!")
    

        
        
class Db:
    def __init__(self) -> None:
        self.con = sqlite3.connect("database.db")
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS spotify_playlists(id INTEGER PRIMARY KEY AUTOINCREMENT, spotify_id STRING, name STRING, hash STRING NULLABLE)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS tidal_playlists(tidal_id STRING PRIMARY KEY, name STRING, hash STRING NULLABLE)")
    
    def write_spotify_playlists_to_db(self, playlists):
        for playlist in playlists:
            sp = SpotifyHelper()
            playlist_one = sp.spotify_get_playlist(playlist["id"])
            hash = playlist_one[1]
            self.cur.execute("INSERT OR IGNORE INTO spotify_playlists(spotify_id, name, hash) VALUES(?, ?, ?)", (playlist["id"], playlist["name"], hash))
            self.con.commit()
        
    def write_tidal_playlist_to_db(self, playlists):
        for playlist in playlists:
            self.cur.execute("INSERT OR IGNORE INTO tidal_playlists(tidal_id, name, hash) VALUES(?, ?, ?)", (playlist["id"], playlist["name"], playlist["hash"]))
            self.con.commit()



class Syncer:
    def __init__(self) -> None:
        print("""
 ▗▄▄▖▄▄▄▄   ▄▄▄▗▄▄▄▖▄    ▐▌▗▞▀▜▌█ 
▐▌   █   █ █   █ █  ▄    ▐▌▝▚▄▟▌█ 
 ▝▀▚▖█▄▄▄▀ ▀▄▄▄▀ █  █ ▗▞▀▜▌     █ 
▗▄▄▞▘█           █  █ ▝▚▄▟▌     █ 
     ▀                            
        """)


        self.db = Db()
        self.tidal = TidalHelper()
        self.sp = SpotifyHelper()
        pass

    def sync_existing_playlists(self):
        print("""
##############################
Starting playlist sync...
##############################
              """)
        spotify_playlists = self.sp.spotify_get_user_playlists()
        tidal_playlists = self.tidal.get_playlists()
        playlists = list()
        
        # Sync Spotify Playlists to TIDAL
        print("===== Syncing Spotify Playlists to TIDAL =====")
        for spotify_playlist in spotify_playlists:
            print("\nSearching for " + spotify_playlist["name"] + " on TIDAL")
            existing_tidal_playlist = None
            tidal_playlist_id = ""
            spotify_playlist_id = spotify_playlist["id"]
            for tidal_playlist in tidal_playlists:
                name_similarity = jellyfish.jaro_similarity(spotify_playlist["name"], tidal_playlist["name"])
                if name_similarity > 0.75:
                    print(color.GREEN + "Found Match: TIDAL:", spotify_playlist["name"] + color.END)
                    print("Similarity:", name_similarity)
                    existing_tidal_playlist = tidal_playlist
                    tidal_playlist_id = tidal_playlist["id"]
                    break
            if existing_tidal_playlist is None:
                # Create playlist
                print(color.RED + "No Match found: Creating playlist on Tidal! (", spotify_playlist["name"], ")"+ color.END)
                tidal_playlist_id =self.tidal.create_playlist(spotify_playlist["name"])
            playlists.append({
                "tidal_id": tidal_playlist_id,
                "spotify_id": spotify_playlist_id
            })

        

        # Sync TIDAL playlists to Spotify        
        for tidal_playlist in tidal_playlists:
            print("\nSearching for " + tidal_playlist["name"] + " on Spotify")
            existing_playlist = None
            for spotify_playlist in spotify_playlists:
                name_similarity = jellyfish.jaro_similarity(spotify_playlist["name"], tidal_playlist["name"])
                if name_similarity > 0.8:
                    print(color.GREEN+"SPOTIFY:", color.END, "Found Match!", spotify_playlist["name"])
                    print("Similarity:", name_similarity)
                    existing_playlist = spotify_playlist
            if existing_playlist is None:
                    # Create playlist    
                print(color.RED + "No Match found: Creating playlist on Spotify! (", tidal_playlist["name"], ")" + color.RED)
                spotify_return_playlist_id = self.sp.create_playlist(tidal_playlist["name"])
                playlists.append({
                    "tidal_id": tidal_playlist["id"],
                    "spotify_id": spotify_return_playlist_id
                })
        print(color.BOLD + "Finished playlist sync!" + color.END)
        return playlists


    def sync_playlist_songs(self, spotify_playlist_id, tidal_playlist_id, liked_songs):
        tidal_found = 0
        spotify_found = 0
        tidal_added = 0
        tidal_failed = 0
        spotify_added = 0
        spotify_failed = 0


        if liked_songs is True:
            print("""
##############################
Starting <3-Songs sync...
##############################\n\n
              """)
            spotify_playlist = self.sp.get_liked_songs()
            tidal_playlist = self.tidal.get_liked_songs()
        else:
            print("""
##############################
Starting playlist sync...
##############################\n\n
              """)
            tidal_playlist = self.tidal.get_playlist(tidal_playlist_id)
            spotify_playlist = self.sp.spotify_get_playlist(spotify_playlist_id)
        
        print("""
***********************
FROM TIDAL TO SPOTIFY
***********************
              """)
        for tidal_track in tidal_playlist:
            track_found = None
            # Check if track is already in spotify playlist
            for spotify_track in spotify_playlist:
                # Check if track title is about the same as the tidal one
                title_difference = jellyfish.jaro_similarity(re.sub(remastered_regex, r"\1", tidal_track["title"], flags=re.IGNORECASE).lower(), 
                                                             re.sub(remastered_regex, r"\1", spotify_track["title"],flags=re.IGNORECASE).lower())
                artist_difference = jellyfish.jaro_similarity(str(tidal_track["artist"]).lower(), 
                                                              str(spotify_track["artist"]).lower())
                if title_difference > 0.75 and artist_difference > 0.6:
                    print(color.CYAN, "SPOTIFY:","Track already in Playlist",color.END,"Found Match: " + tidal_track["title"] + " by " + tidal_track["artist"] + "(Similarity: "+ str(title_difference) + ")")
                    spotify_found += 1
                    track_found = spotify_track
                    break
            if track_found is None:
                # Perform Search
                print(color.CYAN, "SPOTIFY:", "Searching for:", re.sub(remastered_regex, r"\1", tidal_track["title"], flags=re.IGNORECASE).lower() + " by " + tidal_track["artist"], color.END)
                spotify_search = self.sp.search_song(re.sub(r"\(feat\. .*?\)", "", re.sub(remastered_regex, r"\1", str(tidal_track["title"]).lower(), flags=re.IGNORECASE).lower()), str(tidal_track["artist"]).lower())
                # When Results from search:
                if spotify_search is not None:
                    search_track = None
                    popularity_of_search_track = 0
                    for spotify_search_track in spotify_search:
                        # Check if track title is about the same as the tidal one
                        title_difference = jellyfish.jaro_similarity(re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", tidal_track["title"], flags=re.IGNORECASE).lower()),
                                                                     re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", spotify_search_track["title"],flags=re.IGNORECASE).lower()))
                        artist_difference = jellyfish.jaro_similarity(str(tidal_track["artist"]).lower(), str(spotify_search_track["artist"]).lower())
                        if title_difference > 0.70 and artist_difference > 0.62 and spotify_search_track["popularity"] > popularity_of_search_track:
                            search_track = spotify_search_track
                            popularity_of_search_track = spotify_search_track["popularity"]
                    if search_track is None:
                        print(color.CYAN, "SPOTIFY:",color.END, color.RED + "Search found, but no Matching Results: " + tidal_track["title"] + " by " + tidal_track["artist"], color.END)
                        spotify_failed += 1
                        # TODO: Save File with missing tracks
                    else:
                        print(color.CYAN, "SPOTIFY:", color.END, color.GREEN, "Search found Match: " + tidal_track["title"] + " by " + tidal_track["artist"], " (Similarity: Title: " + str(title_difference) + ")", color.END)
                        spotify_added += 1
                        if liked_songs is True:
                            self.sp.add_song_to_liked_songs(search_track["id"])
                        else:
                            self.sp.add_song_to_playlist(spotify_playlist_id, search_track["id"])

                else:
                    print(color.CYAN, "SPOTIFY:", color.END, color.RED + "Search returned no results!: " + tidal_track["title"] + " by " + tidal_track["artist"] + color.END)
                    spotify_failed += 1
                    # TODO: Save File with missing tracks
        
        print("""
***********************
FROM SPOTIFY TO TIDAL
***********************
              """)
        # spotify to tidal
        title_difference = 0
        artist_difference = 0
        for spotify_track in spotify_playlist:
            track_found = None
            for tidal_track in tidal_playlist:
                title_difference = jellyfish.jaro_similarity(re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", tidal_track["title"], flags=re.IGNORECASE).lower()), 
                                                             re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", spotify_track["title"],flags=re.IGNORECASE).lower()))
                artist_difference = jellyfish.jaro_similarity(str(tidal_track["artist"]).lower(), 
                                                              str(spotify_track["artist"]).lower())
                if title_difference > 0.75 and artist_difference > 0.6:
                    print(color.CYAN, "TIDAL:", color.END, color.GREEN + "Track already in Playlist", color.END, "Found Match: " + spotify_track["title"] + " by " + spotify_track["artist"], " (Similarity: " + str(title_difference) + ")")
                    tidal_found += 1
                    track_found = tidal_track
            if track_found is None:
                # Peform search
                try:
                    search_title=re.sub(r"\(feat\. .*?\)", "", re.sub(remastered_regex, r"\1", spotify_track["title"], flags=re.IGNORECASE).lower())
                    print(color.CYAN, "TIDAL:", color.END, "Searching for track: " + search_title + " by " + spotify_track["artist"])
                    tidal_search = self.tidal.search_song(search_title,
                                                        str(spotify_track["artist"]).lower())
                except:
                    print(color.RED + "Error searching for track!" + color.END)
                    tidal_search = None
                if tidal_search is None:
                    print(color.CYAN, "TIDAL:", color.END, color.RED + "Search returned no results. No Match found: " + spotify_track["title"] + " by " + spotify_track["artist"] + color.END)
                    tidal_failed += 1
                else:
                    search_track = None
                    artist_difference = 0
                    title_difference = 0
                    for track in tidal_search:
                        if track["top_hit"] is True:
                            search_track = track
                            artist_difference = jellyfish.jaro_similarity(str(track["artist"]).lower(), str(spotify_track["artist"]).lower)
                            title_difference = jellyfish.jaro_similarity(
                                re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", spotify_track["title"], flags=re.IGNORECASE).lower()),
                                re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", track["title"], flags=re.IGNORECASE).lower())
                            )
                        else:
                            temp_artist_difference = jellyfish.jaro_similarity(str(track["artist"]).lower(), str(spotify_track["artist"]).lower())
                            temp_title_difference = jellyfish.jaro_similarity(
                                re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", spotify_track["title"], flags=re.IGNORECASE).lower()),
                                re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", track["title"], flags=re.IGNORECASE).lower())
                            )
                            if temp_artist_difference > 0.6 and temp_title_difference > 0.72 and temp_artist_difference > artist_difference and temp_title_difference > title_difference:
                                search_track = track
                                artist_difference = jellyfish.jaro_similarity(str(track["artist"]).lower(), str(spotify_track["artist"]).lower())
                                title_difference = jellyfish.jaro_similarity(
                                    re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", spotify_track["title"], flags=re.IGNORECASE).lower()),
                                    re.sub('[^A-Za-z0-9]+', '', re.sub(remastered_regex, r"\1", track["title"], flags=re.IGNORECASE).lower())
                                )
                    if search_track is None:
                        print(color.CYAN, "TIDAL:", color.END, color.RED + "Search returned results, but could not match any song!: "+ spotify_track["title"] + " by " + spotify_track["artist"])
                        tidal_failed += 1
                    else:
                        print(color.CYAN, "TIDAL:", color.END, color.GREEN + "Found matching track after search! Adding track to playlist...", spotify_track["title"], "by", spotify_track["artist"])
                        tidal_added += 1
                        if liked_songs is True:
                            self.tidal.add_song_to_liked_songs(search_track["id"])
                        else:
                            self.tidal.add_song_to_playlist(tidal_playlist_id, search_track["id"])
        # print stats
        print("\n")
        print(color.BOLD + "Finished playlist sync!" + color.END, "\n")
        print(color.CYAN,"TIDAL - Added:",color.END, tidal_added)
        print(color.CYAN,"TIDAL - Found:", color.END, tidal_found)
        print(color.CYAN,"TIDAL - Failed:",color.END, tidal_failed)
        print(color.CYAN,"Spotify - Added:",color.END, spotify_added)
        print(color.CYAN,"Spotify - Found:", color.END, spotify_found)
        print(color.CYAN,"Spotify - Failed:",color.END, spotify_failed)

    
    def sync_liked_songs(self):
        self.sync_playlist_songs("", "", True)

    def perform_full_sync(self):
        
        self.sync_liked_songs()
        all_playlists =self.sync_existing_playlists()

        for playlist in all_playlists:
            self.sync_playlist_songs(playlist["spotify_id"], playlist["tidal_id"], False)




                        



            


# db.write_tidal_playlist_to_db(tidal.get_playlists())
#syncer = Syncer()
#syncer.perform_full_sync()
#syncer.sync_liked_songs()
#print(syncer.sync_existing_playlists())
#syncer.sync_playlist_songs("", "")
#sp = SpotifyHelper()
#print(len(sp.spotify_get_playlist("3tyL0ex9ShVIQT0jsX6phT")))
#print(sp.search_song("Island In The Sun", "Weezer"))
td = TidalHelper()
print(len(td.get_playlist("67e6ac20-b0e5-47d3-8470-40b1f8f4b961")))
#print(td.search_song("it might have to be you", "Vulfmon"))
#print(jellyfish.jaro_similarity("it might have to be you", "(The Ripe & Ruin)"))