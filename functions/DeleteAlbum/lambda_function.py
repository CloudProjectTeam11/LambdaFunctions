import json
import boto3
import os
import uuid

albums_table = os.environ["ALBUMS_TABLE"]
files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]
files_bucket = os.environ["USER_FILES_BUCKET"]

def get_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    response = table.get_item(Key={'album_id': album})
    return response['Items']

def delete_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    table.delete_item(Key={'album_id': album})

def get_files_in_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_metadata_table)
    response = table.scan(
        FilterExpression='album = :album_id',
        ExpressionAttributeValues={':album_id' : album}
    )
    return response["Items"]

def delete_files(files):
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.resource('s3')
    for file in files:
        file_id = file['file_id']
        file_key = file['file_key']

        table = dynamodb.Table(files_metadata_table)
        table.delete_item(Key={'file_id': file_id})
        
        s3.Object(files_bucket, file_key).delete()

def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]
    try:
        body = json.loads(event['body'])
    except:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Invalid request'})
        }

    if "album" not in body:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Parameter (album) is required'})
        }

    album = get_album(body["album"])
    if album is None:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Album not found'})
        }
    album_id = album["album_id"]
    delete_album(album_id)
    files = get_files_in_album(album_id)
    delete_files(files)

    return{
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({"message":"Album deleted"})
    }       