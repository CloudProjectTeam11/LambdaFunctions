import boto3
import json
from datetime import datetime
import os

albums_table1 = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]

    # Retrieve file_id and share_with_user from the request body
    try:
        body = json.loads(event['body'])
        file_id = body.get('file_id')
        share_with_users = body.get('users')
    except:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("Invalid request")
        }
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

    # Find the album in the albums table
    albums_table = dynamodb.Table(albums_table1)
    response = albums_table.get_item(Key={'album_id': file_metadata['album']})
    album = response.get('Item')

    shared_with = album.get('shared_with', [])
    shared_users = False
    # Check if any user in share_with_users is already in shared_with
    for share_user in share_with_users:
        if share_user in shared_with:
            shared_users = True
            share_with_users.remove(share_user)


    print(share_with_users)

    file_metadata['shared_with'] = share_with_users

    file_metadata['shared_with'] = [str(user) for user in file_metadata['shared_with']]
    metadata_table.put_item(Item=file_metadata)

    if(shared_users):
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps("Some users have album access, file access change declined.")
        }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps("Access granted")
    }
