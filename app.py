from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import wave
import io

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

LIVE_AUDIO_FOLDER = "live_audio_file"
os.makedirs(LIVE_AUDIO_FOLDER, exist_ok=True)

live_audio_file = os.path.join(LIVE_AUDIO_FOLDER, "live_audio.wav")
audio_buffer = bytearray()  # Buffer to store live audio chunks

@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    """Handles uploaded audio files and processes them."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    
    try:
        # Process the uploaded file here if needed
        audio_data = file.read()
        print(f"Received file of size: {len(audio_data)} bytes")

        # Here you can pass `audio_data` directly to your model instead of saving
        # Example: model_output = model.predict(audio_data)
        # If necessary, process the audio data and pass it to your model
        
        return jsonify({"message": "File uploaded successfully, processed data sent to model"})
    except Exception as e:
        print(f"Error processing uploaded audio: {e}")
        return jsonify({"error": "Failed to process the audio file"}), 500

@socketio.on("audio_chunk")
def handle_audio_chunk(audio_data):
    """Receives and processes live audio chunks."""
    global audio_buffer

    try:
        # Append the audio data chunk to the buffer
        audio_buffer.extend(audio_data)
        print(f"Received chunk: {len(audio_data)} bytes, Total buffer: {len(audio_buffer)} bytes")
        
        # Pass the buffer data directly to your model
        # Example: model_output = model.predict(audio_buffer)
        
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
        # Process the accumulated audio directly into your model
        # Example: model_output = model.predict(audio_buffer)
        # You can also choose to reset or store the buffer temporarily for model evaluation

        print(f"Processing accumulated audio of size: {len(audio_buffer)} bytes")
    
    except Exception as e:
        print(f"Error processing recorded audio: {e}")
    
    finally:
        audio_buffer = bytearray()  # Reset buffer after processing
        print("Audio buffer reset.")

if __name__ == "__main__":
    print(f"Running Flask server")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)



