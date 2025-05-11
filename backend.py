start = True
end_set = False
bpms = []
energies = []
image_paths = []
songs = []

#flask imports
from flask import Flask, render_template, request, jsonify

#spotify imports
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials

#claude
import boto3
import botocore
region = "us-west-2"


#all_sets_db = boto3.client("dynamodb")
app = Flask(__name__)

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
    if (type(song_info) != list):
        split_data = song_info.split(", ")
    else:
        split_data = song_info
    bpm = split_data[0]
    key = split_data[1]
    valence = split_data[2] #valence is on a 0-1 scale, 1 being happy and 0 being sad
    duration = split_data[3]
    energy = split_data[4]
    card_info = [album_cover_url, bpm, key, valence, duration, energy]
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


#parsing within main
def parse_song(pre_parsed_string):
    parts = pre_parsed_string.split(", ")
    title = parts[0].split(": ", 1)[1].strip()

    return {
        "title": title,
        "artist": parts[1],
        "bpm": parts[2].replace(" BPM", ""),
        "key": parts[3],
        "valence": parts[4],
        "duration": parts[5],
        "energy": parts[6]
    }

def main():
    already_named_songs = []
    bpms = []
    energies = []
    image_paths = []
    songs = []
    
    song = []
    @app.route("/vibe", methods=["POST"])
    def initial_vibe():
        data = request.json

        song_title = data.get("title")
        song_artist = data.get("artist")

        song = [song_title, song_artist]

        return jsonify({
            "message": "Song data received successfully",
            "title": song_title,
            "artist": song_artist,
        }), 200
    
    
    


    #initial input text
    initial_song = f"""{song[0]}, {song[1]}"""
    initial_prompt = """Based on the song provided, please give me the BPM, Key, Valence, Duration, and Energy of the song.
    Give it to me in this format:
    BPM Value (Just the number), Key Value, Valence Value on a 0-1 scale, Duration Value, Energy Value.
    And no other text. 
    """

    initial_results = song_json(song[0], song[1])
    image = initial_results['tracks']['items'][0]['album']['images'][1]['url']
    initial_song_info = editable_prompt_function(initial_song, initial_prompt)
    card_info = frontend_card(initial_results, initial_song_info)
    image_paths.append(image)
    bpms.append(card_info[1])
    energies.append(card_info[5])
    print(song)
    already_named_songs.append(f"{song[0]} by {song[1]}")


    i = 1
    while (song != None and i <= 3):
        if (end_set == True):
            song = None

        song_title = song[0]
        song_artist = song[1]
        results = song_json(song_title, song_artist)
        
        next_song = f"""{song_title}, {song_artist}"""
        repeated_prompt = f"""Based on the song provided and its information, what are the 3 most
        recommended songs from DIFFERENT ARTISTS to mix it with? Base this on BPM, Key, Valence, Energy and Genre. 

        IMPORTANT: DO NOT recommend any of these songs that have already been used:
        {", ".join(already_named_songs)}

        The Energy value of each of the three should have 1) higher energy, 2) same energy, 3) lower energy. 
        The BPM, Key, Valence, and Genre should be AS SIMILAR AS POSSIBLE to the initial song, but should be from different artists.

        Represent it as:
        Higher Energy: Song Name, Artist Name, BPM Value (eg 171 BPM), Key Value, Valence Value on a 0-1 scale (just the number), Duration Value, Energy Value (just the number)-
        Same Energy: Song Name, Artist Name, BPM Value (eg 171 BPM), Key Value, Valence Value on a 0-1 scale (just the number), Duration Value, Energy Value (just the number)-
        Lower Energy: Song Name, Artist Name, BPM Value (eg 171 BPM), Key Value, Valence Value on a 0-1 scale (just the number), Duration Value, Energy Value (just the number)-

        And no other text. 
        """
        repeated_song_info = editable_prompt_function(next_song, repeated_prompt)
        song_choices = repeated_song_info.split("\n")

        pre_parsed_song = None

        
        ##JAVASCRIPT##
        song_choice = "Lower"

        ##JAVASCRIPT##
        if (song_choice == "Higher"):
            pre_parsed_song = song_choices[0]
        elif (song_choice == "Lower"):
            pre_parsed_song = song_choices[2]
        else:
            pre_parsed_song = song_choices[1]


        song_info = parse_song(pre_parsed_song)

        pass_into_frontend_card_song_info = [song_info['bpm'], song_info['key'], song_info['valence'], song_info['duration'], song_info['energy']]
        song = [song_info['title'], song_info['artist']]

        song_title = song[0]
        song_artist = song[1]

        results = song_json(song_title, song_artist)
        card_info = frontend_card(results, pass_into_frontend_card_song_info)
        image = results['tracks']['items'][0]['album']['images'][1]['url']

        bpms.append(card_info[1])
        energies.append(card_info[5])
        image_paths.append(image)
        print(song)
        already_named_songs.append(f"{song[0]} by {song[1]}")
        ##JAVASCRIPT##
        i+=1


if __name__ == "__main__": 
    app.run(debug=True)
    

    song = None
    print(bpms)
    print(energies)
    print(image_paths)
    print(songs)

