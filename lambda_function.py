import boto3
import json
import logging
import os
import json

from base64 import b64decode
from urlparse import parse_qs

from boto3 import resource
from boto3.dynamodb.conditions import Key


ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']

kms = boto3.client('kms', region_name='us-east-1')

DECRYPTED = boto3.client('kms')
expected_token = DECRYPTED.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN),EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def ddb(key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ProductCatalog')
    response = table.get_item(
        Key={
            'Id': key,
        }
        )

    return response['Item']
    
def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def lambda_handler(event, context):
    print(json.dumps(event))
    print(event['body'])
    params = parse_qs(event['body'])
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        return respond(Exception('Invalid request token'))

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    if 'text' in params:
            command_text = params['text'][0]
            command_value = ddb(int(command_text))
    else:
        command_text = ''
        command_value = 'val'

    response = respond(None, "%s invoked %s in %s searching for the following key %s and returned the following item %s" % (user, command, channel, command_text, command_value))
    logger.info(response)
    return response
