from faster_whisper import WhisperModel
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "int8"

model_size = "tiny"
faster_model = WhisperModel(model_size, device=device, compute_type=compute_type)

def run_s2tt_faster_whisper(input_audio):
    segments, detected_language = faster_model.transcribe(input_audio, vad_filter=True)
    transcription = " ".join([segment.text for segment in segments])
    return transcription, detected_language.language


# if __name__ == "__main__":
#     transcription, detected_language = run_s2tt_faster_whisper("/home/ervin/commentcasecrit.mp3")
#     print (transcription, detected_languaged)