import React, { useState, useEffect, useRef } from "react";
import { useReactMediaRecorder } from "react-media-recorder";
import axios from "axios";
import io from "socket.io-client";

const socket = io("http://localhost:5000"); // Connect to Flask WebSocket

const SpeechRecorder = () => {
  const [isSystemAudio, setIsSystemAudio] = useState(false);
  const [summary, setSummary] = useState("");
  const [audioFile, setAudioFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [loading, setLoading] = useState(false); // for showing a loading spinner during file upload
  const mediaRecorderRef = useRef(null);
  const [stream, setStream] = useState(null);

  const { mediaBlobUrl, clearBlob } = useReactMediaRecorder({
    audio: isSystemAudio ? { echoCancellation: false } : true,
  });

  useEffect(() => {
    socket.on("summary_update", (data) => {
      setSummary((prev) => prev + " " + data.summary);
    });
  }, []);

  const startStreaming = async () => {
    try {
      const userStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(userStream);

      // Determine supported MIME type
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/ogg";

      const mediaRecorder = new MediaRecorder(userStream, { mimeType });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          socket.emit("audio_chunk", event.data); // Emit the audio chunk to the server
        }
      };

      mediaRecorder.start(1000); // Send audio chunks every 1 second
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      setPermissionDenied(true);
    }
  };

  const stopStreaming = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
  };

  const handleFileChange = (event) => {
    setAudioFile(event.target.files[0]);
  };

  const uploadAudio = async () => {
    if (loading) return; // Prevent multiple uploads at the same time
    setLoading(true);

    const formData = new FormData();
    
    if (audioFile) {
      formData.append("file", audioFile);
    } else if (mediaBlobUrl) {
      const audioBlob = await fetch(mediaBlobUrl).then(res => res.blob());
      formData.append("file", audioBlob, "recorded_audio.wav");
    } else {
      alert("Please record or select an audio file first!");
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/upload_audio", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setSummary(response.data.summary || "No summary available");
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>🎙 Real-Time Speech Summarizer</h2>

      {permissionDenied && <p style={{ color: "red" }}>⚠ Microphone permission denied. Enable it in browser settings.</p>}

      <label>
        <input type="checkbox" checked={isSystemAudio} onChange={() => setIsSystemAudio(!isSystemAudio)} />
        Record System Audio
      </label>

      <br /><br />

      {/* Streaming Controls */}
      <button onClick={startStreaming} disabled={isRecording}>🔴 Start Live Recording</button>
      <button onClick={stopStreaming} disabled={!isRecording}>⏹ Stop</button>

      <br /><br />

      <p style={{ color: isRecording ? "red" : "black" }}>
        {isRecording ? "🔴 Streaming..." : "Idle"}
      </p>

      {/* File Upload */}
      <input type="file" accept="audio/*" onChange={handleFileChange} />

      <br /><br />

      {/* Upload Button */}
      <button onClick={uploadAudio} disabled={!mediaBlobUrl && !audioFile || loading}>📤 Upload & Summarize</button>

      {/* Loading Spinner */}
      {loading && <div>🔄 Uploading...</div>}

      {/* Audio Player */}
      {mediaBlobUrl && <audio src={mediaBlobUrl} controls />}

      <br /><br />

      {/* Summary Output */}
      {summary && (
        <div>
          <h3>📄 Summary:</h3>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
};

export default SpeechRecorder;





