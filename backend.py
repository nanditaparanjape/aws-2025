from flask import Flask, render_template, request, jsonify, send_from_directory
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials
import boto3
import botocore
import matplotlib.pyplot as plt
import io
import base64
import time

app = Flask(__name__, static_folder='.')

# Global variables
already_named_songs = []
bpms = []
energies = []
image_paths = []
songs = []
current_song = None

# AWS Bedrock setup
region = "us-west-2"
bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)

# Spotify API setup
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="4c0a7a2e5a1e4c18996837995251779e",
    client_secret="a6b0858c688147d2b57fd001b55b2739", 
))

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

# Define constants
BASE_ADDRESS = "https://api.spotify.com."
ENERGY_RANGE = 5
KEY_RANGE = 2
TEMPO_RANGE = 5

# Helper Functions
def song_json(song_name, artist_name):
    """Search for a song on Spotify and return JSON data"""
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)
    return results

def frontend_card(results, song_info):
    """Parse song data to create a card for frontend display"""
    try:
        album_cover_url = results['tracks']['items'][0]['album']['images'][1]['url']
        
        if (type(song_info) != list):
            split_data = song_info.split(", ")
        else:
            split_data = song_info
            
        bpm = split_data[0]
        key = split_data[1]
        valence = split_data[2] 
        duration = split_data[3]
        energy = split_data[4]
        
        card_info = [album_cover_url, bpm, key, valence, duration, energy]
        return card_info
    except Exception as e:
        print(f"Error processing song data: {e}")
        return None

def editable_prompt_function(initial_data, prompt):
    """Query Claude via AWS Bedrock API"""
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

def parse_song(pre_parsed_string):
    """Parse song data from Claude's response"""
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

# Routes
@app.route("/")
def index():
    """Serve the index.html file"""
    return send_from_directory('.', 'index.html')

@app.route("/initial_card.html")
def initial_card():
    """Serve the initial_card.html file"""
    return send_from_directory('.', 'initial_card.html')

@app.route("/in_set.html")
def in_set():
    """Serve the in_set.html file"""
    return send_from_directory('.', 'in_set.html')

@app.route("/script.js")
def serve_js():
    """Serve the script.js file"""
    return send_from_directory('.', 'script.js')

@app.route("/style.css")
def serve_css():
    """Serve the style.css file"""
    return send_from_directory('.', 'style.css')

@app.route("/dj_bg2.png")
def serve_image():
    """Serve the background image"""
    return send_from_directory('.', 'dj_bg2.png')

@app.route("/vibe", methods=["POST"])
def initial_vibe():
    """Handle initial song submission"""
    global already_named_songs, bpms, energies, image_paths, songs, current_song
    
    try:
        data = request.json
        song_title = data.get("title")
        song_artist = data.get("artist")
        
        if not song_title or not song_artist:
            return jsonify({"error": "Missing song title or artist"}), 400
            
        # Get initial song data
        song = [song_title, song_artist]
        initial_song = f"{song_title}, {song_artist}"
        
        # Query Spotify
        initial_results = song_json(song_title, song_artist)
        if not initial_results['tracks']['items']:
            return jsonify({"error": "Song not found on Spotify"}), 404
            
        # Get song data from Claude
        initial_prompt = """Based on the song provided, please give me the BPM, Key, Valence, Duration, and Energy of the song.
        Give it to me in this format:
        BPM Value (Just the number), Key Value, Valence Value on a 0-1 scale, Duration Value, Energy Value.
        And no other text. 
        """
        initial_song_info = editable_prompt_function(initial_song, initial_prompt)
        
        # Process song data
        image = initial_results['tracks']['items'][0]['album']['images'][1]['url']
        card_info = frontend_card(initial_results, initial_song_info)
        
        # Store data
        image_paths.append(image)
        bpms.append(card_info[1])
        energies.append(card_info[5])
        already_named_songs.append(f"{song_title} by {song_artist}")
        songs.append(song)
        current_song = song
        
        # Return data to frontend
        return jsonify({
            "success": True,
            "song": {
                "title": song_title,
                "artist": song_artist,
                "image": image,
                "bpm": card_info[1],
                "key": card_info[2],
                "valence": card_info[3],
                "duration": card_info[4],
                "energy": card_info[5]
            }
        }), 200
        
    except Exception as e:
        print(f"Error in initial_vibe: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/next_song", methods=["POST"])
def get_next_song():
    """Get recommendations for the next song"""
    global already_named_songs, bpms, energies, image_paths, songs, current_song
    
    try:
        data = request.json
        energy_preference = data.get("energy_preference", "Same")  # Higher, Same, or Lower
        
        if not songs:
            return jsonify({"error": "No songs in playlist yet"}), 400
            
        current_song = songs[-1]
        song_title, song_artist = current_song
        
        # Get recommendations from Claude
        next_song = f"{song_title}, {song_artist}"
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
        
        # Select based on energy preference
        if energy_preference == "Higher":
            pre_parsed_song = song_choices[0]
        elif energy_preference == "Lower":
            pre_parsed_song = song_choices[2]
        else:  # Same
            pre_parsed_song = song_choices[1]
            
        # Parse song data
        song_info = parse_song(pre_parsed_song)
        pass_into_frontend_card_song_info = [
            song_info['bpm'], 
            song_info['key'], 
            song_info['valence'], 
            song_info['duration'], 
            song_info['energy']
        ]
        
        # Get Spotify data
        new_song = [song_info['title'], song_info['artist']]
        results = song_json(new_song[0], new_song[1])
        
        if not results['tracks']['items']:
            return jsonify({"error": "Recommended song not found on Spotify"}), 404
            
        # Process song data
        card_info = frontend_card(results, pass_into_frontend_card_song_info)
        image = results['tracks']['items'][0]['album']['images'][1]['url']
        
        # Store data
        bpms.append(card_info[1])
        energies.append(card_info[5])
        image_paths.append(image)
        songs.append(new_song)
        already_named_songs.append(f"{new_song[0]} by {new_song[1]}")
        current_song = new_song
        
        # Return data to frontend
        return jsonify({
            "success": True,
            "song": {
                "title": new_song[0],
                "artist": new_song[1],
                "image": image,
                "bpm": card_info[1],
                "key": card_info[2],
                "valence": card_info[3],
                "duration": card_info[4],
                "energy": card_info[5]
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_next_song: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/start_set", methods=["POST"])
def start_set():
    """Initialize a new DJ set"""
    global already_named_songs, bpms, energies, image_paths, songs
    
    try:
        # Clear any existing data
        already_named_songs = []
        bpms = []
        energies = []
        image_paths = []
        songs = []
        
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error in start_set: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_recommendations", methods=["POST"])
def get_recommendations():
    """Get three song recommendations based on energy levels"""
    global current_song, already_named_songs
    
    try:
        if not current_song:
            return jsonify({"error": "No current song"}), 400
            
        # Get current song's BPM using Claude
        current_song_info = f"{current_song[0]}, {current_song[1]}"
        bpm_prompt = """Based on the song provided, please give me the BPM of the song.
        Give it to me in this format:
        BPM Value (Just the number)
        And no other text."""
        
        # Add retry logic for BPM request with longer delays
        max_retries = 5  # Increased retries
        current_bpm = None
        for attempt in range(max_retries):
            try:
                current_bpm_response = editable_prompt_function(current_song_info, bpm_prompt)
                current_bpm = float(current_bpm_response.strip())
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to get BPM after {max_retries} attempts: {e}")
                    return jsonify({"error": "Could not get song BPM"}), 500
                time.sleep(5)  # Increased delay to 5 seconds
        
        bpm_range = 5  # Allow ±5 BPM variation
            
        prompt = f"""Based on the song "{current_song[0]}" by {current_song[1]} (BPM: {current_bpm}), recommend three songs:

        1. First song: A lower energy song (dial it down)
        2. Second song: A similar energy song (keep it steady)
        3. Third song: A higher energy song (hype it up)
        
        Requirements:
        - All songs must have BPM within ±{bpm_range} of {current_bpm} BPM
        - Each song should have a different energy level
        - Do not recommend any of these songs: {', '.join(already_named_songs)}
        
        For each song, provide:
        - Title
        - Artist
        - BPM
        - Key
        - Duration
        - Energy (just the number between 0 and 1)
        
        Format each song as: Title, Artist, BPM, Key, Duration, Energy
        
        Please provide exactly three songs, one for each energy level.
        """
        
        # Add retry logic for recommendations with longer delays
        recommendations = []
        for attempt in range(max_retries):
            try:
                # Add delay before each attempt (except the first one)
                if attempt > 0:
                    time.sleep(5)  # Increased delay to 5 seconds
                    
                response = editable_prompt_function(current_song[0], prompt)
                recommendations = []
                
                # Parse the response line by line
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                
                for line in lines:
                    try:
                        parts = line.split(', ')
                        if len(parts) >= 6:
                            # Clean up energy value by removing any prefix
                            energy_str = parts[5].replace('Energy:', '').replace('Energy', '').strip()
                            try:
                                energy = float(energy_str)
                                if 0 <= energy <= 1:  # Validate energy is between 0 and 1
                                    song_data = {
                                        'title': parts[0],
                                        'artist': parts[1],
                                        'bpm': parts[2],
                                        'key': parts[3],
                                        'duration': parts[4],
                                        'energy': energy
                                    }
                                    
                                    # Get Spotify data for the song
                                    spotify_data = song_json(song_data['title'], song_data['artist'])
                                    if spotify_data['tracks']['items']:
                                        image = spotify_data['tracks']['items'][0]['album']['images'][1]['url']
                                        recommendations.append({
                                            **song_data,
                                            'image': image
                                        })
                            except ValueError:
                                print(f"Invalid energy value: {energy_str}")
                                continue
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing song data: {e}")
                        continue
                
                # If we have at least one recommendation, try to use it
                if recommendations:
                    # Sort by energy to ensure order (lower, same, higher)
                    recommendations.sort(key=lambda x: x['energy'])
                    
                    # If we have exactly 3, we're good
                    if len(recommendations) == 3:
                        break
                    
                    # If we have 1 or 2, try to get more
                    if attempt < max_retries - 1:
                        print(f"Got {len(recommendations)} recommendations, retrying for more...")
                        continue
                    
            except Exception as e:
                print(f"Error getting recommendations (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 5 seconds...")
                continue
        
        # If we have any recommendations, return them
        if recommendations:
            # Ensure we have exactly 3 by duplicating if necessary
            while len(recommendations) < 3:
                recommendations.append(recommendations[-1])
            
            return jsonify({
                "success": True,
                "recommendations": recommendations[:3]
            }), 200
        
        return jsonify({"error": "Could not get any valid recommendations"}), 500
        
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/end_set", methods=["POST"])
def end_set():
    """End the set and clear data"""
    global already_named_songs, bpms, energies, image_paths, songs, current_song
    
    try:
        # Clear all the data
        already_named_songs = []
        bpms = []
        energies = []
        image_paths = []
        songs = []
        current_song = None
        
        return jsonify({
            "success": True
        }), 200
        
    except Exception as e:
        print(f"Error in end_set: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__": 
    app.run(debug=True)