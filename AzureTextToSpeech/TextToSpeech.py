import ffmpeg
import uuid
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import AzureFileStorage


def get_speech_file_link(text):
    local_file_path, duration = _download_speech_file(text)
    file_path = AzureFileStorage.upload_file_to_azure(local_file_path)
    return file_path, duration


def _download_speech_file(text):
    load_dotenv()
    subscription = os.getenv('SPEECH_KEY')
    region = os.getenv('SPEECH_REGION')
    speech_config = speechsdk.SpeechConfig(subscription=subscription,
                                           region=region)

    # Use uuid to generate filename
    serial_number = str(uuid.uuid4())
    wav_file_name = f"{serial_number}.wav"
    m4a_file_name = f"{serial_number}.m4a"

    # Get wav file from Azure speech SDK.
    file_config = speechsdk.audio.AudioOutputConfig(filename=wav_file_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=file_config)
    speech_synthesizer.speak_text_async(text).get()

    # Use ffmpeg to covert audio file.
    input_stream = ffmpeg.input(wav_file_name)
    output_stream = ffmpeg.output(input_stream, m4a_file_name, acodec='aac')
    ffmpeg.run(output_stream)

    probe = ffmpeg.probe(m4a_file_name,
                         v='error', select_streams='a:0',
                         show_entries='format=duration', of='json')
    duration = float(probe['format']['duration'])

    # Remove unused wav file.
    os.system(f"rm {wav_file_name}")

    # Remove unused m4a file.
    os.system(f"rm {m4a_file_name}")

    return m4a_file_name, duration
