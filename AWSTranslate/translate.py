import boto3
from dotenv import load_dotenv
import os

load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

def translate_en_zh(text):
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='ap-southeast-2'
    )

    translate = session.client(service_name='translate')
    result = translate.translate_text(Text=text, 
                                    SourceLanguageCode="en", 
                                    TargetLanguageCode="zh-TW")

    return result.get('TranslatedText')

def translate_zh_en(text):
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='ap-southeast-2'
    )

    translate = session.client(service_name='translate')
    result = translate.translate_text(Text=text, 
                                    SourceLanguageCode="zh-TW", 
                                    TargetLanguageCode="en")

    return result.get('TranslatedText')