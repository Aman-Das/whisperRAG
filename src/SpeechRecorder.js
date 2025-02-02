import React, { useState, useEffect, useRef } from "react";
import { useReactMediaRecorder } from "react-media-recorder";
import axios from "axios";
import io from "socket.io-client";

const socket = io("http://13.49.44.30:5000");

const SpeechRecorder = () => {
  const [isSystemAudio, setIsSystemAudio] = useState(false);
  const [summary, setSummary] = useState("");
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
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px", fontFamily: "Arial, sans-serif" }}>
      <h2>🎙 Real-Time Speech Summarizer</h2>

      {permissionDenied && <p style={{ color: "red" }}>⚠ Microphone permission denied. Enable it in browser settings.</p>}

      <label>
        <input type="checkbox" checked={isSystemAudio} onChange={() => setIsSystemAudio(!isSystemAudio)} />
        Record System Audio
      </label>

      <br /><br />

      <div>
        <button onClick={startStreaming} disabled={isRecording} style={buttonStyle}>
          🔴 Start Live Recording
        </button>
        <button onClick={stopStreaming} disabled={!isRecording} style={buttonStyle}>
          ⏹ Stop
        </button>
      </div>

      <br /><br />

      <p style={{ color: isRecording ? "red" : "black" }}>
        {isRecording ? "🔴 Streaming..." : "Idle"}
      </p>

      <br />

      <input type="file" accept="audio/*" onChange={handleFileChange} style={fileInputStyle} />

      <br /><br />

      <button onClick={uploadAudio} disabled={!mediaBlobUrl && !audioFile || loading} style={buttonStyle}>
        📤 Upload & Summarize
      </button>

      {loading && <div>🔄 Uploading...</div>}

      {mediaBlobUrl && <audio src={mediaBlobUrl} controls />}

      <br /><br />

      {summary && (
        <div>
          <h3>📄 Summary:</h3>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
};

const buttonStyle = {
  padding: "10px 20px",
  margin: "5px",
  fontSize: "16px",
  cursor: "pointer",
};

const fileInputStyle = {
  margin: "10px 0",
};

export default SpeechRecorder;






