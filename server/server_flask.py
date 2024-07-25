from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import random
import base64
import whisper
from datetime import datetime
import threading
import os
import torch
from gtts import gTTS
import noisereduce as nr
import soundfile as sf
from googletrans import Translator
import pandas as pd
import atexit
from speech_recog import run_s2tt_google
from faster_whisper_model import run_s2tt_faster_whisper
from whisper_model import run_s2tt_whisper

# Set the environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "int8"

translator = Translator()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

input_audio_dir = "/usr/my-audio"
output_audio_dir = "/app/outputs"
noise_reduced_audio_dir = "/app/reduced_noise"
timestamps_csv_path = '/app/timestamps.csv'

df = pd.DataFrame(columns=['chunk_id', 'received_time', 'process_start_time', 'process_end_time', 'transcription'])

atexit.register(lambda: df.to_csv(timestamps_csv_path, index=False))

lock = threading.Lock()
count=0

def saveB64audio(b64_chunk):
    global count
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{timestamp}_{count}"
    complete_filename = f"{input_audio_dir}/{filename}.wav"
    os.makedirs(os.path.dirname(complete_filename), exist_ok=True)
    with open(complete_filename, "wb") as wav_file:
        decode_string = base64.b64decode(b64_chunk)
        wav_file.write(decode_string)
    count+=1
    return complete_filename, filename

def reduce_noise(input_audio_path):
    data, rate = sf.read(input_audio_path)
    reduced_noise = nr.reduce_noise(y=data, sr=rate, prop_decrease=1)
    os.makedirs(noise_reduced_audio_dir, exist_ok=True)
    noise_reduced_path = os.path.join(noise_reduced_audio_dir, os.path.basename(input_audio_path))
    sf.write(noise_reduced_path, reduced_noise, rate)
    return noise_reduced_path

def translate_text(text, language='en'):
    start_time = datetime.now()
    translation = translator.translate(text, dest=language)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    return translation.text, start_time, end_time, duration

def run_tts(text, language='en'):
    translated_text, translate_start_time, translate_end_time, translate_duration = translate_text(text, language)
    tts_start_time = datetime.now()
    tts = gTTS(text=translated_text, lang=language)
    output_path = f"{output_audio_dir}/chunk_{random.randint(0, 100)}.wav"
    tts.save(output_path)
    tts_end_time = datetime.now()
    tts_duration = (tts_end_time - tts_start_time).total_seconds()
    return output_path, translated_text, translate_start_time, translate_end_time, translate_duration, tts_start_time, tts_end_time, tts_duration

@app.route("/")
def index():
    return "Audio Processing Server"

@socketio.on("connect")
def test_connect():
    print("Client connected")

@socketio.on("disconnect")
def test_disconnect():
    print("Client disconnected")

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(input_audio_dir, filename)


@socketio.on("audio_stream")
def handle_audio(data):
    print("\nReceived a chunk\n")

    with lock:
        received_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        audio_chunk = data["audio"]
        saved_filename, chunk_id = saveB64audio(audio_chunk)

        process_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        noise_reduction_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        noise_reduced_filename = reduce_noise(saved_filename)

        noise_reduction_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        noise_reduction_duration = (datetime.strptime(noise_reduction_end_time, "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(noise_reduction_start_time, "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        transcription_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        model = data.get("model", "speech_recognition")

        if model == "faster_whisper":
            transcription, detected_language = run_s2tt_faster_whisper(noise_reduced_filename)
        elif model == "whisper":
            transcription, detected_language = run_s2tt_whisper(noise_reduced_filename)
        else:
            transcription, detected_language = run_s2tt_google(noise_reduced_filename)

        transcription_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        transcription_duration = (datetime.strptime(transcription_end_time, "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(transcription_start_time, "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        if transcription and detected_language != 'nn':
            tts_path, translated_text, translate_start_time, translate_end_time, translate_duration, tts_start_time, tts_end_time, tts_duration = run_tts(transcription, language=data.get("language", "en"))

            process_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            process_duration = (datetime.strptime(process_end_time, "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(process_start_time, "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

            with open(tts_path, "rb") as processed_file:
                processed_data = processed_file.read()

            print("Audio processed, sending event")
            emit(
                "processed_audio",
                {
                    "audio": base64.b64encode(processed_data).decode(),
                    "transcription": transcription,
                    "chunk_id": chunk_id,
                    "received_time": received_time,
                    "process_start_time": process_start_time,
                    "noise_reduction_start_time": noise_reduction_start_time,
                    "noise_reduction_end_time": noise_reduction_end_time,
                    "noise_reduction_duration": noise_reduction_duration,
                    "transcription_start_time": transcription_start_time,
                    "transcription_end_time": transcription_end_time,
                    "transcription_duration": transcription_duration,
                    "translate_start_time": translate_start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "translate_end_time": translate_end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "translate_duration": translate_duration,
                    "tts_start_time": tts_start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "tts_end_time": tts_end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "tts_duration": tts_duration,
                    "process_duration": process_duration,
                },
                binary=False,
            )
        else:
            print("No transcription available")
            emit(
                "processed_audio",
                {
                    "audio": None,
                    "transcription": "No transcription available"
                },
                binary=False,
            )

@socketio.on("translate_text")
def handle_translation(data):
    text_to_translate = data.get("text", "")
    selected_language = data.get("language", "en")
    
    translated_text = translator.translate(text_to_translate, dest=selected_language).text

    emit("translated_text", {"translated_text": translated_text})

@socketio.on("text_to_speech")
def handle_text_to_speech(data):
    text_to_speak = data.get("text", "")
    selected_language = data.get("language", "en")
    
    tts_path, translated_text, translate_start_time, translate_end_time, translate_duration, tts_start_time, tts_end_time, tts_duration = run_tts(text_to_speak, language=selected_language)
    
    with open(tts_path, "rb") as audio_file:
        audio_data = audio_file.read()
    
    emit("synthesized_speech", {"audio": base64.b64encode(audio_data).decode()})


if __name__ == "__main__":
    socketio.run(app, debug=False, port=7860, host="0.0.0.0", log_output=True)