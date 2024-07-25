import speech_recognition as sr

def run_s2tt_google(input_audio):
    recognizer = sr.Recognizer()
    with sr.AudioFile(input_audio) as source:
        audio = recognizer.record(source)
    try:
        transcription = recognizer.recognize_google(audio)
        detected_language = "en"
    except sr.UnknownValueError:
        transcription = None
        detected_language = "nn"
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        transcription = None
        detected_language = "nn"
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return transcription, detected_language


# if __name__ == "__main__":
#     transcription, detected_language = run_s2tt_google("/home/ervin/examples_french.aiff")
#     print(transcription, detected_language)
