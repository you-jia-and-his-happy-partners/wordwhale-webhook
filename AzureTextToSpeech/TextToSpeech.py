import ffmpeg
import uuid
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from azure.storage.fileshare import (generate_account_sas, ShareFileClient,
                                     ShareServiceClient)


def get_speech_file_link(text):
    local_file_path = _download_speech_file(text)
    file_path = _upload_speech_file_to_azure(local_file_path)
    return file_path


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

    # Remove unused wav file.
    os.system(f"rm {wav_file_name}")

    return m4a_file_name


def _upload_speech_file_to_azure(local_file_path):
    load_dotenv()
    connection_string = os.getenv('AZURE_FILE_CONNECTION_STRING')
    share_name = 'hackathon'
    sas_token = os.getenv('SAS_TOKEN')

    # Create a ShareFileClient from a connection string
    file_client = ShareFileClient.from_connection_string(
        connection_string, share_name, local_file_path)

    with open(local_file_path, "rb") as data:
        file_client.upload_file(data)

    file_url_with_sas = file_client.url + sas_token

    # Remove unused local file.
    os.system(f"rm {local_file_path}")

    return file_url_with_sas
