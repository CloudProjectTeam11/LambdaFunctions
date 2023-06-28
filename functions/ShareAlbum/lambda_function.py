import json
import boto3
import os

albums_table = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def get_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    response = table.get_item(Key={'album_id': album})
    return response.get('Item')

def get_files_in_album(album_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_table)
    response = table.scan(
        FilterExpression='album = :album_id',
        ExpressionAttributeValues={':album_id' : album_id}
    )
    print(response["Items"])
    for el in response["Items"]:
        try:
            el["tags"] = list(el["tags"])
        except:
            print("no tags")
    return response["Items"]
    
def remove_user_from_file(file_id, user):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_table)
    response = table.get_item(Key={'file_id': file_id})
    file_metadata = response.get('Item')
    if user in file_metadata['shared_with']:
        file_metadata['shared_with'].remove(user)
        table.put_item(Item=file_metadata)

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
    if album["album_owner"] != user:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': "You don't have ownership rights for this album"})
        }

    files = get_files_in_album(body["album"])
    for file in files:
        for sharing_id in body["sharing_with"]:
            remove_user_from_file(file['file_id'], sharing_id)

    dynamodb = boto3.client('dynamodb')
    dynamodb.update_item(
        TableName=albums_table,
        Key={
            'album_id': {'S': body["album"]}
        },
        UpdateExpression='ADD shared_with :users',
        ExpressionAttributeValues={
            ':users': {'SS': body["sharing_with"]}
        }
    )
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({'message': "Access added"})
    }
