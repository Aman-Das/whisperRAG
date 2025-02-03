import React, { useState, useEffect, useRef } from "react";
import { useReactMediaRecorder } from "react-media-recorder";
import axios from "axios";
import io from "socket.io-client";

const socket = io("http://localhost:5000");

const SpeechRecorder = () => {
  const [isSystemAudio, setIsSystemAudio] = useState(false);
  const [summary, setSummary] = useState("");
  const [keywords, setKeywords] = useState([]);
  const [sentiment, setSentiment] = useState("");  // New state for sentiment
  const [timestamps, setTimestamps] = useState([]);  // New state for timestamps
  const [audioFile, setAudioFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const [stream, setStream] = useState(null);

  const { mediaBlobUrl, clearBlob } = useReactMediaRecorder({
    audio: isSystemAudio ? { echoCancellation: false } : true,
  });

  useEffect(() => {
    socket.on("summary_update", (data) => {
      setSummary((prev) => prev + " " + data.summary);
      setKeywords(data.keywords);
      setSentiment(data.sentiment);  // Update sentiment
      setTimestamps(data.timestamps);  // Update timestamps
    });
  }, []);

  const startStreaming = async () => {
    try {
      const userStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(userStream);

      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/ogg";
      const mediaRecorder = new MediaRecorder(userStream, { mimeType });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          socket.emit("audio_chunk", event.data);
        }
      };

      mediaRecorder.start(1000);
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
    if (loading) return;
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
      setKeywords(response.data.keywords || []);
      setSentiment(response.data.sentiment || "No sentiment analysis available");
      setTimestamps(response.data.timestamps || []);
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2 className="header">🎙 Speech Summarizer</h2>

      {permissionDenied && <p className="alert">⚠ Microphone permission denied. Enable it in browser settings.</p>}

      <label className="checkbox-label">
        <input type="checkbox" checked={isSystemAudio} onChange={() => setIsSystemAudio(!isSystemAudio)} />
        Record System Audio
      </label>

      <div className="button-container">
        <button onClick={startStreaming} disabled={isRecording} className="btn primary">
          🔴 Start Live Recording
        </button>
        <button onClick={stopStreaming} disabled={!isRecording} className="btn secondary">
          ⏹ Stop
        </button>
      </div>

      <p className={`status ${isRecording ? "recording" : "idle"}`}>
        {isRecording ? "🔴 Streaming..." : "Idle"}
      </p>

      <input type="file" accept="audio/*" onChange={handleFileChange} className="file-input" />

      <button onClick={uploadAudio} disabled={!mediaBlobUrl && !audioFile || loading} className="btn upload">
        📤 Upload & Summarize
      </button>

      {loading && <div className="loading">🔄 Uploading...</div>}

      {mediaBlobUrl && <audio src={mediaBlobUrl} controls className="audio-player" />}

      <div className="content-container">
        {summary && (
          <div className="summary-container">
            <h3>📄 Summary:</h3>
            <p>{summary}</p>
          </div>
        )}

        {keywords.length > 0 && (
          <div className="keywords-container">
            <h3>🔑 Keywords:</h3>
            <ul>
              {keywords.map((keyword, index) => (
                <li key={index}>{keyword}</li>
              ))}
            </ul>
          </div>
        )}

        {sentiment && (
          <div className="sentiment-container">
            <h3>💬 Sentiment Analysis:</h3>
            <p>{sentiment}</p>
          </div>
        )}

{timestamps.length > 0 && (
  <div className="timestamps-container">
    <h3>⏱ Timestamps:</h3>
    <ul>
      {timestamps.map((timestamp, index) => (
        <li key={index}>
          {timestamp.word} - {timestamp.timestamp}
        </li>
      ))}
    </ul>
  </div>
)}

      </div>
    </div>
  );
};

export default SpeechRecorder;

