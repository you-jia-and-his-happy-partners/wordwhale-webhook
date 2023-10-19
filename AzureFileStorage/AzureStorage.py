import os
from dotenv import load_dotenv
from azure.storage.fileshare import (ShareFileClient)


def upload_file_to_azure(local_file_path):
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
