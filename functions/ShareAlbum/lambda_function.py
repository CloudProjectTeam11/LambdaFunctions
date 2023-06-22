import json
import boto3
import os

bucket_name = os.environ["USER_FILES_BUCKET"]
table_name = os.environ["USER_FILES_METADATA_TABLE"]

def get_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("albumsTable")
    response = table.get_item(Key={'id': album})
    return response.get('Item')

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
    if album["owner"] != user:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': "You don't have ownership right for this album"})
        }
    dynamodb = boto3.resource('dynamodb')
    dynamodb.update_item(
        TableName="albumsTable",
        Key={
            'id': body["album"]
        },
        UpdateExpression='SET sharedWith = list_append(sharedWith, :users)',
        ExpressionAttributeValues={
            ':users': body["sharing_with"]
        }
    )
    return{
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({'message': "Access added"})
    }       