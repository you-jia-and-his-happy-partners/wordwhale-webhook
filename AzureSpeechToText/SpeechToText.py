import requests
import ffmpeg
import uuid
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk


def get_text_with_content(content):
    local_file_path = _convert(content)
    text = _from_local_to_azure(local_file_path)
    return text


# Speech to Text
def get_text_with_url(url):
    local_file_path = _download_and_convert(url)
    text = _from_local_to_azure(local_file_path)
    return text


# Download to local and Convert the file
def _download_and_convert(url):
    # Use uuid to generate filename
    serial_number = str(uuid.uuid4())
    m4a_file_name = f"{serial_number}.m4a"
    wav_file_name = f"{serial_number}.wav"

    # Use requests to download file with URL
    response = requests.get(url)
    with open(m4a_file_name, "wb") as f:
        f.write(response.content)

    # Use ffmpeg to covert audio file
    ffmpeg.input(m4a_file_name).output(wav_file_name, acodec='pcm_s16le', ar=44100).run()

    # Remove m4a file in local
    os.system(f"rm {m4a_file_name}")

    return wav_file_name


def _convert(content):
    # Use uuid to generate filename
    serial_number = str(uuid.uuid4())
    m4a_file_name = f"{serial_number}.m4a"
    wav_file_name = f"{serial_number}.wav"

    with open(m4a_file_name, "wb") as f:
        f.write(content)

    # Use ffmpeg to covert audio file
    ffmpeg.input(m4a_file_name).output(wav_file_name, acodec='pcm_s16le', ar=44100).run()

    # Remove m4a file in local
    os.system(f"rm {m4a_file_name}")

    return wav_file_name

# Azure Speech SDK
def _from_local_to_azure(wav_file_name):
    # Load Key and Region
    load_dotenv()
    subscription = os.getenv('SPEECH_KEY')
    region = os.getenv('SPEECH_REGION')
    
    # Get text from Azure Speech SDK
    speech_config = speechsdk.SpeechConfig(subscription=subscription, region=region)
    audio_config = speechsdk.AudioConfig(filename=wav_file_name)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once_async().get()
    
    # Remove wav file in local
    os.system(f"rm {wav_file_name}")
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    
    return result.text
