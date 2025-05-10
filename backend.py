import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

BASE_ADDRESS = "https://api.spotify.com."
ENERGY_RANGE = 5
KEY_RANGE = 2
TEMPO_RANGE = 5


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="4c0a7a2e5a1e4c18996837995251779e",
    client_secret="a6b0858c688147d2b57fd001b55b2739", 
    redirect_uri = "http://127.0.0.1:5500/",
    scope = "user-library-read user-read-private user-read-playback-state"
))

#search bar
# input: song name; artist
# album cover, artist, song name, track id
#output: json data

def init_song(song_name, artist_name):
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)

    return results

#saves/parses current song info and displays
# input: json data
#output: parsed json data - 
#    to USER on a card: album cover, song name, artist, genre, duration
#in db: track id, energy, duration, bpm, key
# returns data structure containing current song info to pick next songs: bpm, key, energy, 
def frontend_card(results):
    album_cover_url = results['tracks']['items'][0]['album']['images'][1]['url']
    duration_ms = results['tracks']['items'][0]['duration_ms']
    seconds = (duration_ms / 1000) % 60
    minutes = (duration_ms / (1000 * 60)) % 60
    duration = f"{int(minutes)}:{int(seconds):02d}"    
    frontend_info = []
    #print("\n\n", album_cover_url, "duration: ", duration)
    

#track id, energy, bpm, key, popularity, valence, danceability

def audio_features(results):
    track_id = results['tracks']['items'][0]['id']
    print("\n\n", track_id)
    audio_features = sp.audio_features([track_id])
    #energy = audio_features['energy']
    #bpm = audio_features['tempo']
    #key = audio_features['key']
    #features_dict = {'track_id': track_id}  
    #print(track_id)



#example: https://api.spotify.com/v1/artists/1vCWHaC5f2uS3yhpwWbIA6/albums?album_type=SINGLE&offset=20&limit=10
#selecting top 15 songs to give to claude into +- tempo and key
#input: current song data structure
#work we'd be doing: using xx algorithm on tempo, key, valence, popularity to pick top 15 songs
#data structure for claude: store the 15 song name - artists
def top_15_songs(current_song_info):
    min_energy = current_song['energy'] - ENERGY_RANGE
    max_energy = current_song['energy'] + ENERGY_RANGE

    min_key = current_song['key'] - KEY_RANGE
    max_key = current_song['key'] + KEY_RANGE

    min_tempo = current_song['bpm'] - TEMPO_RANGE
    max_tempo = current_song['bpm'] + TEMPO_RANGE

    min_valence = current_song['valence'] - VALENCE_RANGE
    max_valence = current_song['valence'] + VALENCE_RANGE






#claude
#input: current song + ds for 15 songs "Given x song , and genre House, suggest the best song to mix x with for DJing from this list."
#output: whatever song claude suggests


#after user puts init song, return bpm, energy, info... - make api call and parse json data

#make api call to return list of top xx number of songs that fit range

if __name__ == "__main__":
    results = init_song("Blinding Lights", "The Weeknd")
    frontend_card(results)
    audio_features(results)