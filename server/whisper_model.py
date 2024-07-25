import whisper
import soundfile as sf
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "int8"

model_size = "tiny"
whisper_model = whisper.load_model(model_size).to(device)

def run_s2tt_whisper(input_audio):
    audio, sample_rate = sf.read(input_audio)
    
    # Convert the audio to a tensor and move it to the appropriate device
    audio_tensor = torch.tensor(audio).to(device)
    
    # Transcribe the audio and detect the language
    result = whisper_model.transcribe(input_audio)
    detected_language = result["language"]
    transcription = result["text"]
    
    return transcription, detected_language


# if __name__ == "__main__":
#     transcription, detected_language = run_s2tt_whisper("/home/ervin/commentcasecrit.mp3")
#     print (transcription, detected_language)
