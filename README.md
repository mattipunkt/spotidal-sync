# SpoTiDAL-Sync
Sync all your Spotify-Likes and Playlist with TIDAL. 

This tool can be used once to transfer all data to TIDAL (or to Spotify), but can also be used with a cron job, to have two synced streaming service librarys.

## Installation
Modify the .env-File with your Spotify Developer Data. ![You can get them here](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)

At redirect URL type `http://127.0.0.1:8084`

**Important**: You have to set the number of your playlists in MAX_PLAYLIST_COUNT (in multiples of 50, so for example, if you have 142 playlists you should set the environment variable to 150 or 200, do so as you like). This is due to Spotify may responses your requests with timeouts and then the application can't do shit. You should really this much higher than your playlist count.

**Limits**:

Number of Playlists: You set yourself

Number of Songs in Playlist: 8000 *This also applies to liked-songs*


Then, run the following commands in your shell:
```bash
mkdir /opt/spotidal-sync
cd /opt/spotidal-sync # or every other folder you want to have the app saved

python3 -m venv venv
source venv/bin/activate # or activate.fish if you don't use bash
pip install -r requirements.txt
python3 spotidal.py # run the program

```

### First Run
When running for the first time, you should be prompted to authenticate on Spotify and then on TIDAL. This is necessary to access your music data.

Then the program does it's magic for itself!


## TODO
- [] Make application faster (hashes on playlists, if hash stays the same, no resync)
- [] Make application more customizable. Currently all personal playlists get synced, but maybe someone also wants to sync a playlist not created by himself