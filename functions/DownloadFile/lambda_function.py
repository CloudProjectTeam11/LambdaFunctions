import boto3
import json
from datetime import datetime
import os

files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]
albums_table = os.environ["ALBUMS_TABLE"]
s3_bucket_name = os.environ["USER_FILES_BUCKET"]

def is_user_shared_with_file(file_metadata, user):
    shared_with = file_metadata.get('shared_with', [])
    return user == file_metadata['user'] or user in shared_with

def is_user_shared_with_album(album_id, user):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    response = table.get_item(Key={'album_id': album_id})
    album = response.get('Item')
    shared_with = album.get('shared_with', [])
    return user in shared_with

def lambda_handler(event, context):
    file_id = event["queryStringParameters"]["file_id"]
    user = event["requestContext"]["authorizer"]["X-User-Id"]

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_metadata_table)
    response = table.get_item(Key={'file_id': file_id})
    file_metadata = response.get('Item')

    # Check if file exists
    if not file_metadata:
        return {
            'statusCode': 404,
            'body': 'File not found'
        }

    if user != file_metadata['user'] and not is_user_shared_with_file(file_metadata, user):
        # Check if the user is in the shared_with list of the album
        album_id = file_metadata.get('album')
        if album_id and not is_user_shared_with_album(album_id, user):
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                    'Access-Control-Allow-Credentials': 'true'
                },
                'body': json.dumps({'message': 'Access forbidden'})
            }

    # Get the file's S3 key
    file_key = file_metadata['file_key']

    s3_client = boto3.client('s3')
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': s3_bucket_name,
            'Key': file_key
        }
    )

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({
            'presigned_url': presigned_url
        })
    }
