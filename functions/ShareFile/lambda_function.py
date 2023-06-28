import boto3
import json
from datetime import datetime
import os

albums_table1 = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]

    # Retrieve file_id and share_with_user from the request body
    body = json.loads(event['body'])
    file_id = body.get('file_id')
    share_with_user = body.get('username')

    dynamodb = boto3.resource('dynamodb')

    # Retrieve file metadata from the metadata table
    metadata_table = dynamodb.Table(files_table)
    response = metadata_table.get_item(Key={'file_id': file_id})
    file_metadata = response.get('Item')

    # Check if the file exists
    if not file_metadata:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("File not found")
        }

    print(file_metadata)
    # Check if the user is the owner of the file
    if file_metadata['user'] != user:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("Access forbidden")
        }

    # Check if the file is already shared with the user
    if share_with_user in file_metadata['shared_with']:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("File already shared with the user")
        }

    # Find the album in the albums table
    albums_table = dynamodb.Table(albums_table1)
    response = albums_table.get_item(Key={'album_id': file_metadata['album']})
    album = response.get('Item')

    # Check if the album is already shared with the user
    if share_with_user in album['shared_with']:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("Album already shared with the user")
        }

    # Update the shared_with list in the file metadata
    file_metadata['shared_with'].append(share_with_user)

    # Convert shared_with to a list of strings
    file_metadata['shared_with'] = [str(user) for user in file_metadata['shared_with']]

    metadata_table.put_item(Item=file_metadata)

    output = {
        "album": album["album_id"],
        "files": [file_metadata]
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(output)
    }
