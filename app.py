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

class feature_extraction:
    def __init__(self, sample_rate=16000, model_size='base'):
        self.sample_rate = sample_rate
        self.model = whisper.load_model(model_size)
        self.keyword_extractor = KeyBERT(model='bert-base-multilingual-cased')
        self.summarizer = pipeline("summarization")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.knowledge_base = []
        self.index = None

    def load_audio(self, audio_bytes):
        #ACCEPT RAW BYTES NOT PATH
        #converting the bytes to numpy array
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)  
        signal = librosa.resample(audio_np.astype(np.float32), orig_sr=44100, target_sr=self.sample_rate)
        return signal


    def transcribe(self, audio):
        trans_res = self.model.transcribe(audio)
        return trans_res["text"]

    def extract_keywords(self, transcript, top_n=5):
        keywords = self.keyword_extractor.extract_keywords(transcript, top_n=top_n)
        return [kw[0] for kw in keywords]

    def build_knowledge_base(self, documents):
        """Builds a vector-based knowledge base using FAISS."""
        self.knowledge_base = documents
        embeddings = [self.embedder.encode(doc, convert_to_tensor=False) for doc in documents]
        d = len(embeddings[0])
        self.index = faiss.IndexFlatL2(d)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def retrieve_relevant_context(self, transcript):
        """Retrieves relevant context from the FAISS knowledge base."""
        if not self.index:
            return ""
        transcript_embedding = self.embedder.encode(transcript, convert_to_tensor=False).reshape(1, -1)
        _, I = self.index.search(np.array(transcript_embedding, dtype=np.float32), 1)
        return self.knowledge_base[I[0][0]] if I[0][0] < len(self.knowledge_base) else ""

    def summarize(self, transcript):
        """Summarizes the transcript with RAG-based context."""
        context = self.retrieve_relevant_context(transcript)
        input_text = context + " " + transcript if context else transcript
        summary = self.summarizer(input_text, max_length=150, min_length=50, do_sample=False)
        return summary[0]["summary_text"]

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
 

        #LIVE AUDIO
        signal = feature_extraction.load_audio(audio_buffer)
        trans = feature_extraction.transcribe(signal)

        #logging to check if its working
        print(trans)

        #sending the transcript to the frontend
        emit("transcript", {"text":trans})
        
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
        #proecess accumulated live audio
        signal = feature_extraction.load_audio(audio_buffer)
        trans = feature_extraction.transcribe(signal)

        print(trans)

        emit("final", {"text":trans})

        print(f"Processing accumulated audio of size: {len(audio_buffer)} bytes")
    
    except Exception as e:
        print(f"Error processing recorded audio: {e}")
    
    finally:
        audio_buffer = bytearray()  # Reset buffer after processing
        print("Audio buffer reset.")

if __name__ == "__main__":
    print(f"Flask server started")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)



