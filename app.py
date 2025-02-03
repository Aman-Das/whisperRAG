import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import numpy as np
import librosa
from vosk import Model, KaldiRecognizer
from werkzeug.utils import secure_filename
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textblob import TextBlob  # Sentiment analysis library

# Initialize nltk resources
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

LIVE_AUDIO_FOLDER = "live_audio_file"
os.makedirs(LIVE_AUDIO_FOLDER, exist_ok=True)

VOSK_MODEL_PATH = os.path.abspath("./src/models/vosk")

# Ensure model exists
if not os.path.exists(VOSK_MODEL_PATH):
    raise FileNotFoundError(f"VOSK Model not found at {VOSK_MODEL_PATH}. Download from https://alphacephei.com/vosk/models.")

audio_buffer = bytearray()  # Buffer to store live audio chunks

class Transcriber:
    def __init__(self, sample_rate=16000):  # Default sample rate set to 16000 for Vosk
        self.sample_rate = sample_rate
        self.model = Model(VOSK_MODEL_PATH)
    
    def load_audio(self, audio_bytes, orig_sr=48000):  # Original sample rate of the microphone input
        """Convert raw bytes to a resampled numpy array with the proper format."""
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Resample only if needed (from orig_sr to self.sample_rate)
        if orig_sr != self.sample_rate:
            audio_np = librosa.resample(audio_np.astype(np.float32), orig_sr=orig_sr, target_sr=self.sample_rate)
        
        # Normalize and convert to int16 PCM
        audio_np = np.int16(audio_np / np.max(np.abs(audio_np)) * 32767)

        # Ensure buffer size is a multiple of 2 bytes (16-bit PCM)
        if len(audio_np) % 2 != 0:
            audio_np = np.append(audio_np, 0)  # Add a zero-padding sample

        return audio_np

    def transcribe(self, audio):
        """Transcribe the audio signal using Vosk."""
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.AcceptWaveform(audio.tobytes())
        return recognizer.Result()

    def extract_keywords(self, text):
        """Extract keywords from the transcribed text using basic NLTK methods."""
        # Tokenize the text and remove stop words
        words = word_tokenize(text)
        stop_words = set(stopwords.words("english"))
        filtered_words = [word for word in words if word.isalnum() and word.lower() not in stop_words]
        
        # Optionally, we can add more sophisticated keyword extraction here
        return filtered_words

    def analyze_sentiment(self, text):
        """Analyze sentiment of the transcribed text using TextBlob."""
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity  # Sentiment score between -1 (negative) and 1 (positive)
        return sentiment

    def extract_timestamped_words(self, audio):
        """Simulate timestamped words based on the audio signal."""
        # A simple approximation: this could be improved based on actual timing data
        words = audio.split()  # Split transcription into words
        timestamps = []
        for i, word in enumerate(words):
            timestamps.append({"word": word, "timestamp": i * 0.5})  # Rough estimate (every word 0.5 seconds apart)
        return timestamps


transcriber = Transcriber()

@socketio.on("audio_chunk")
def handle_audio_chunk(audio_data):
    """Receives and processes live audio chunks."""
    global audio_buffer

    try:
        if isinstance(audio_data, bytes):
            audio_buffer.extend(audio_data)
            print(f"Received chunk: {len(audio_data)} bytes, Total buffer: {len(audio_buffer)} bytes")

            # Ensure buffer length is a multiple of 2 (int16 PCM requirement)
            if len(audio_buffer) % 2 != 0:
                audio_buffer = audio_buffer[:-1]  # Remove last byte if necessary

            MIN_PROCESS_SIZE = 3200  # 0.2s of 16kHz 16-bit PCM audio
            if len(audio_buffer) >= MIN_PROCESS_SIZE:
                # Convert to correct format by resampling to 16kHz
                signal = transcriber.load_audio(bytes(audio_buffer), orig_sr=48000)

                recognizer = KaldiRecognizer(transcriber.model, transcriber.sample_rate)

                if recognizer.AcceptWaveform(signal.tobytes()):
                    transcription = recognizer.Result()  # Finalized words
                else:
                    transcription = recognizer.PartialResult()  # Intermediate words

                print(transcription)  # Log transcription
                # Extract keywords
                keywords = transcriber.extract_keywords(transcription)
                sentiment = transcriber.analyze_sentiment(transcription)
                timestamps = transcriber.extract_timestamped_words(transcription)

                emit("transcript", {
                    "text": transcription,
                    "keywords": keywords,
                    "sentiment": sentiment,
                    "timestamps": timestamps
                })

                audio_buffer = bytearray()  # Reset buffer after processing

    except Exception as e:
        print(f"Error processing live audio: {e}")

@socketio.on("stop_recording")
def stop_recording():
    """Stops recording and processes accumulated live audio."""
    global audio_buffer

    if not audio_buffer:
        print("No audio recorded.")
        return

    try:
        # Ensure buffer size is always a multiple of 2 bytes
        if len(audio_buffer) % 2 != 0:
            audio_buffer.append(0)

        signal = transcriber.load_audio(audio_buffer)
        transcription = transcriber.transcribe(signal)

        print(transcription)
        # Extract keywords
        keywords = transcriber.extract_keywords(transcription)
        sentiment = transcriber.analyze_sentiment(transcription)
        timestamps = transcriber.extract_timestamped_words(transcription)

        emit("final", {
            "text": transcription,
            "keywords": keywords,
            "sentiment": sentiment,
            "timestamps": timestamps
        })

    except Exception as e:
        print(f"Error processing recorded audio: {e}")

    finally:
        audio_buffer = bytearray()  # Reset buffer after processing
        print("Audio buffer reset.")

# Route for handling file uploads for audio files
@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    """Handle file upload and transcribe audio file."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(LIVE_AUDIO_FOLDER, filename)
        file.save(file_path)

        # Load the file for transcription
        try:
            audio_data, sr = librosa.load(file_path, sr=transcriber.sample_rate)
            audio_data = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)  # Convert to 16-bit PCM

            transcription = transcriber.transcribe(audio_data)

            # Extract keywords from transcription
            keywords = transcriber.extract_keywords(transcription)
            sentiment = transcriber.analyze_sentiment(transcription)
            timestamps = transcriber.extract_timestamped_words(transcription)

            return jsonify({
                "summary": transcription,
                "keywords": keywords,
                "sentiment": sentiment,
                "timestamps": timestamps
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400


def allowed_file(filename):
    """Check if the file extension is valid."""
    allowed_extensions = {"wav", "mp3", "flac", "ogg", "m4a"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


if __name__ == "__main__":
    print("Flask server started")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
