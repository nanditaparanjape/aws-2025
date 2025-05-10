import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials

BASE_ADDRESS = "https://api.spotify.com."

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="4c0a7a2e5a1e4c18996837995251779e",
    client_secret="a6b0858c688147d2b57fd001b55b2739"
))

#search bar
# input: song name; artist
#output: json data

def init_song(song_name, artist_name):
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)
    print(results)
    return results

#saves/parses current song info and displays
# input: json data
#output: parsed json data - 
#    to USER on a card: album cover, song name, artist
#in db: track id, energy, duration, bpm, key
# returns data structure containing current song info to pick next songs: bpm, key, energy, 
def parse_current_song(results):
    
    



    
#selecting top 15 songs to give to claude into +- tempo and key
#input: current song data structure
#work we'd be doing: using xx algorithm on tempo, key, valence, popularity to pick top 15 songs
#data structure for claude: store the 15 song name - artists

#claude
#input: current song + ds for 15 songs "Given x song , and genre House, suggest the best song to mix x with for DJing from this list."
#output: whatever song claude suggests


#after user puts init song, return bpm, energy, info... - make api call and parse json data

#make api call to return list of top xx number of songs that fit range

if __name__ == "__main__":
    init_song("Blinding Lights", "The Weeknd")