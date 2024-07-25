import React, { useState, useEffect } from "react";
import io from "socket.io-client";
import RecordRTC, { StereoAudioRecorder } from "recordrtc";
import "./App.css";
import AudioPlayerButton from "./components/AudioPlayer";

const socket = io.connect("http://localhost:7860");

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptionText, setTranscriptionText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [feedback, setFeedback] = useState("");
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [processDetails, setProcessDetails] = useState([]);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    socket.on("processed_audio", (data) => {
      if (data.audio) {
        const audio = new Audio("data:audio/mp3;base64," + data.audio);
        audio.play();
      }
      if (data.transcription && data.transcription !== "No transcription available") {
        updateTranscription(data.transcription);
      }
      updateProcessDetails(data);
    });

    socket.on("translated_text", (data) => {
      setTranslatedText(data.translated_text);
    });

    socket.on("synthesized_speech", (data) => {
      const audio = new Audio("data:audio/mp3;base64," + data.audio);
      audio.play();
    });

    return () => {
      socket.off("processed_audio");
      socket.off("translated_text");
      socket.off("synthesized_speech");
    };
  }, []);

  const updateTranscription = (newLine) => {
    setTranscriptionText((prevText) => prevText + (prevText ? "\n" : "") + newLine); // Update editable transcription text
  };

  const startRecording = () => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const recorder = RecordRTC(stream, {
        type: "audio",
        recorderType: StereoAudioRecorder,
        mimeType: "audio/wav",
        timeSlice: 3500,
        desiredSampRate: 16000,
        numberOfAudioChannels: 1,
        ondataavailable: (event) => {
          blobToBase64(event).then((b64) => {
            const language = document.getElementById("targetLanguage").value;
            const model = document.getElementById("transcriptionModel").value;
            socket.emit("audio_stream", { audio: b64, language: language, model: model });
          });
        },
      });
      recorder.startRecording();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setFeedback("Recording started.");
    }).catch((err) => {
      console.error("Error accessing microphone:", err);
    });
  };

  const stopRecording = () => {
    if (isRecording && mediaRecorder) {
      mediaRecorder.stopRecording();
      setIsRecording(false);
      setFeedback("Recording stopped.");
    }
  };

  const translateText = () => {
    const text = transcriptionText; // Use editable transcription text
    const language = document.getElementById("targetLanguage").value;
    socket.emit("translate_text", { text: text, language: language });
  };

  const synthesizeText = () => {
    const text = transcriptionText; // Use editable transcription text
    const language = document.getElementById("targetLanguage").value;
    socket.emit("text_to_speech", { text: text, language: language });
  };

  const updateProcessDetails = (data) => {
    if (data.transcription && data.transcription !== "No transcription available") {
      setProcessDetails((prevDetails) => [...prevDetails, data]);
    }
  };

  const blobToBase64 = (blob) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    return new Promise((resolve) => {
      reader.onloadend = () => {
        const base64data = reader.result.split(",")[1];
        resolve(base64data);
      };
    });
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle("dark-mode");
  };

  const [currentAudio, setCurrentAudio] = useState(null);

  const handlePlayAudio = (audioUrl) => {
      if (currentAudio) {
          currentAudio.pause(); // Pause current audio if any
      }
      const audio = new Audio(audioUrl);
      setCurrentAudio(audio);
      audio.play();
  };

  return (
    <div className={`container mt-5 ${darkMode ? "dark-mode" : ""}`}>
      <h1 className="text-center mb-4">Real-Time Speech Translation</h1>
      <button className="btn btn-dark toggle-theme" onClick={toggleDarkMode}>
        {darkMode ? "Light Mode" : "Dark Mode"}
      </button>
      <div className="content">
        {/* Left side: Transcription and translation */}
        <div className="left-panel">
          <div className="mb-3">
            <label htmlFor="targetLanguage">Target Language:</label>
            <select id="targetLanguage" className="form-control">
              <option value="en">English</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
              {/* Add more language options as needed */}
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="transcriptionModel">Transcription Model:</label>
            <select id="transcriptionModel" className="form-control">
              <option value="speech_recognition">Speech Recognition</option>
              <option value="faster_whisper">Faster Whisper</option>
              <option value="whisper">Whisper</option>
            </select>
          </div>
          <div className="mb-3 text-center">
            <button className="btn btn-primary mr-2" onClick={startRecording} disabled={isRecording}>Start Recording</button>
            <button className="btn btn-danger" onClick={stopRecording} disabled={!isRecording}>Stop Recording</button>
          </div>
          <div className="mb-3">
            <label htmlFor="transcription">Transcription:</label>
            <textarea
              id="transcription"
              className="form-control"
              value={transcriptionText}
              onChange={(e) => setTranscriptionText(e.target.value)} // Allow user to edit transcription
            ></textarea>
          </div>
          <div className="mb-3 text-center">
            <button className="btn btn-secondary mr-2" onClick={translateText}>Translate</button>
            <button className="btn btn-info" onClick={synthesizeText}>Text to Speech</button>
          </div>
          <div className="mb-3">
            <label htmlFor="translatedText">Translation:</label>
            <textarea id="translatedText" className="form-control" value={translatedText} readOnly></textarea>
          </div>
          <p className="text-center">{feedback}</p>
        </div>

        <div className="right-panel">
          <h3 className="mb-3">Process Details</h3>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                <th>Action</th>
                  <th>Chunk ID</th>
                  <th>Received Time</th>
                  <th>Process Start Time</th>
                  <th>Noise Reduction Start Time</th>
                  <th>Noise Reduction End Time</th>
                  <th>Noise Reduction Duration (s)</th>
                  <th>Transcription Start Time</th>
                  <th>Transcription End Time</th>
                  <th>Transcription Duration (s)</th>
                  <th>TTS Start Time</th>
                  <th>TTS End Time</th>
                  <th>TTS Duration (s)</th>
                  <th>Process Duration(s)</th>
                  <th>Translate Duration</th>
                </tr>
              </thead>
              <tbody>
                {processDetails.map((item, index) => (
                  <tr key={index}>
                    <td><AudioPlayerButton chunkId={item.chunk_id} /></td>
                    <td>{item.chunk_id}</td>
                    <td>{item.received_time}</td>
                    <td>{item.process_start_time}</td>
                    <td>{item.noise_reduction_start_time}</td>
                    <td>{item.noise_reduction_end_time}</td>
                    <td>{item.noise_reduction_duration}</td>
                    <td>{item.transcription_start_time}</td>
                    <td>{item.transcription_end_time}</td>
                    <td>{item.transcription_duration}</td>
                    <td>{item.tts_start_time}</td>
                    <td>{item.tts_end_time}</td>
                    <td>{item.tts_duration}</td>
                    <td>{item.process_duration}</td>
                    <td>{item.translate_duration}</td>
                    
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;