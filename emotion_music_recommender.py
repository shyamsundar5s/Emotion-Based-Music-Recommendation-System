# Importing necessary libraries
import os
import cv2
import sqlite3
import numpy as np
import librosa
from flask import Flask, render_template, request, jsonify
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Flask app initialization
app = Flask(__name__)

# Spotify API credentials
SPOTIFY_CLIENT_ID = 'your_spotify_client_id'
SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

# Load pre-trained models for facial and speech emotion recognition
facial_emotion_model = load_model('facial_emotion_model.h5')  # Replace with your model path
speech_emotion_model = load_model('speech_emotion_model.h5')  # Replace with your model path

# Emotion categories
emotion_categories = ['Happy', 'Sad', 'Angry', 'Neutral']

# Database setup
DATABASE_PATH = 'user_feedback.db'

def initialize_database():
    if not os.path.exists(DATABASE_PATH):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emotion TEXT NOT NULL,
                song_name TEXT NOT NULL,
                song_url TEXT NOT NULL,
                feedback TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

# Fetch songs from Spotify
def fetch_songs_from_spotify(emotion):
    try:
        query = f"{emotion} mood"
        results = spotify.search(q=query, type='track', limit=5)
        songs = []
        for track in results['tracks']['items']:
            songs.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'url': track['external_urls']['spotify']
            })
        return songs
    except Exception as e:
        print(f"Error in Spotify API: {e}")
        return []

# Facial Emotion Recognition
def detect_facial_emotion(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized_frame = cv2.resize(gray_frame, (48, 48))
    normalized_frame = resized_frame / 255.0
    reshaped_frame = np.reshape(normalized_frame, (1, 48, 48, 1))
    prediction = facial_emotion_model.predict(reshaped_frame)
    emotion_index = np.argmax(prediction)
    return emotion_categories[emotion_index]

# Speech Emotion Recognition
def detect_speech_emotion(audio_file_path):
    y, sr = librosa.load(audio_file_path, sr=22050)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    mfcc_scaled = StandardScaler().fit_transform(mfccs)
    reshaped_mfcc = np.reshape(mfcc_scaled, (1, mfccs.shape[0], mfccs.shape[1], 1))
    prediction = speech_emotion_model.predict(reshaped_mfcc)
    emotion_index = np.argmax(prediction)
    return emotion_categories[emotion_index]

# Hybrid Emotion Detection
def hybrid_emotion_detection(frame, audio_file_path):
    facial_emotion = detect_facial_emotion(frame)
    speech_emotion = detect_speech_emotion(audio_file_path)
    
    # Combine both emotions using a simple majority or confidence-based approach
    if facial_emotion == speech_emotion:
        return facial_emotion
    else:
        # Default to facial emotion if there is a conflict
        return facial_emotion

# Save feedback in the database
def save_feedback(emotion, song_name, song_url, feedback):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedback (emotion, song_name, song_url, feedback)
        VALUES (?, ?, ?, ?)
    ''', (emotion, song_name, song_url, feedback))
    conn.commit()
    conn.close()

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    input_type = request.form.get('input_type')
    emotion = None

    if input_type == 'facial':
        # Process facial input
        file = request.files['file']
        frame = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        emotion = detect_facial_emotion(frame)
    elif input_type == 'speech':
        # Process speech input
        file = request.files['file']
        file_path = 'temp_audio.wav'
        file.save(file_path)
        emotion = detect_speech_emotion(file_path)
    elif input_type == 'hybrid':
        # Process both facial and speech input
        frame = cv2.imdecode(np.frombuffer(request.files['facial'].read(), np.uint8), cv2.IMREAD_COLOR)
        audio_file_path = 'temp_audio.wav'
        request.files['speech'].save(audio_file_path)
        emotion = hybrid_emotion_detection(frame, audio_file_path)
    else:
        return jsonify({'error': 'Invalid input type'}), 400

    # Fetch songs from Spotify
    songs = fetch_songs_from_spotify(emotion)
    return jsonify({'emotion': emotion, 'songs': songs})

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    emotion = data.get('emotion')
    song_name = data.get('song_name')
    song_url = data.get('song_url')
    feedback = data.get('feedback')

    if not all([emotion, song_name, song_url, feedback]):
        return jsonify({'error': 'Missing required fields'}), 400

    save_feedback(emotion, song_name, song_url, feedback)
    return jsonify({'message': 'Feedback saved successfully'})

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
