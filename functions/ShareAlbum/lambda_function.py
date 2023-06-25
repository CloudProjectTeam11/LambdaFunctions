import json
import boto3
import os

albums_table = os.environ["ALBUMS_TABLE"]

def get_album(album):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    response = table.get_item(Key={'album_id': album})
    return response['Item']

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
    dynamodb = boto3.client('dynamodb')
    print(body["sharing_with"])
    dynamodb.update_item(
        TableName=albums_table,
        Key={
            'album_id': {'S':body["album"]}
        },
        UpdateExpression='ADD shared_with :users',
        ExpressionAttributeValues={
            ':users': {'SS':body["sharing_with"]}
        }
    )
    return{
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({'message': "Access added"})
    }       