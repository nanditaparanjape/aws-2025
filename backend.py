#spotify imports
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials
import backenddupe as dupe

#claude
import boto3
import botocore
region = "us-west-2"

db = boto3.client("dynamodb")


BASE_ADDRESS = "https://api.spotify.com."
ENERGY_RANGE = 5
KEY_RANGE = 2
TEMPO_RANGE = 5


sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="4c0a7a2e5a1e4c18996837995251779e",
    client_secret="a6b0858c688147d2b57fd001b55b2739", 
))

#search bar
# input: song name; artist
# album cover, artist, song name, track id
#output: json data


def song_json(song_name, artist_name):
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)

    return results

#saves/parses current song info and displays
# input: json data
#output: parsed json data - 
#    to USER on a card: album cover, song name, artist, genre, duration
#in db: track id, energy, duration, bpm, key
# returns data structure containing current song info to pick next songs: bpm, key, energy, 
def frontend_card(results, song_info):
    album_cover_url = results['tracks']['items'][0]['album']['images'][1]['url']
    split_data = song_info.split(", ")
    bpm = split_data[0]
    key = split_data[1]
    valence = split_data[2] #valence is on a 0-1 scale, 1 being happy and 0 being sad
    duration = split_data[3]
    card_info = [album_cover_url, bpm, key, valence, duration]
    return card_info
    #print("\n\n", album_cover_url, "duration: ", duration)
    

# Create Bedrock client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)

# Model IDs
MODELS = {
    "Claude 3.7 Sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "Claude 3.5 Haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "Amazon Nova Pro": "amazon.nova-pro-v1:0",
    "Amazon Nova Micro": "amazon.nova-micro-v1:0",
    "DeepSeek-R1": "deepseek.r1-v1:0",
    "Meta Llama 3.1 70B Instruct": "meta.llama3-1-70b-instruct-v1:0"
}

#Prompting function
def editable_prompt_function(initial_data, prompt):

    full_prompt = f"""{prompt}
    <text>
    {initial_data}
    </text>
    """

    # Request body for Claude 3.7 Sonnet
    claude_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.5,
        "top_p": 0.9,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": full_prompt}]
            }
        ],
    }

    # Make request
    try:
        response = bedrock.invoke_model(
            modelId=MODELS["Claude 3.7 Sonnet"],
            body=json.dumps(claude_body),
            accept="application/json",
            contentType="application/json"
        )
        # Parse body
        response_body = json.loads(response['body'].read())
        summary = response_body['content'][0]['text']
        return summary

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print(f"\n[ACCESS DENIED] {error.response['Error']['Message']}")
            print("Check IAM permissions and policies for Bedrock.\n")
            print("More help: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html")
        else:
            raise


#Database information







if __name__ == "__main__":
    song_title = "Blinding Lights"
    song_artist = "The Weeknd"
    results = song_json(song_title, song_artist)

    #input text
    initial_song = f"""{song_title}, {song_artist}"""
    initial_prompt = """Based on the song provided, please give me the BPM, Key, Valence and Duration of the song.
    Give it to me in this format:
    BPM Value, Key Value, Valence Value on a 0-1 scale, Duration Value
    And no other text. 
    """

    initial_song_info = editable_prompt_function(initial_song, initial_prompt)
    frontend_card(results, initial_song_info)

    #while not end set: 

    next_song = f"""{song_title}, {song_artist}"""
    repeated_prompt = """Based on the song provided, please give me the BPM, Key, Valence and Duration of the song.
    Give it to me in this format:
    BPM Value, Key Value, Valence Value on a 0-1 scale, Duration Value
    And no other text. 
    """


    





'''
def audio_features(results):
    track_id = results['tracks']['items'][0]['id']
    
    try:
        sp.auth_manager.get_access_token(as_dict=False)
    except:
        pass
    
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


'''


