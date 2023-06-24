import json
import boto3
import os
import uuid

albums_table = os.environ["ALBUMS_TABLE"]

def is_duplicate_name(name: str, user: str):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    response = table.scan(
        FilterExpression='album_name = :album_name AND album_owner = :album_owner',
        ExpressionAttributeValues={
            ':album_name':name,
            ':album_owner':user
        }
    )
    if response['Items']:
        return True
    return False

def create_album(name, user):
    album_id = uuid.uuid1()
    album = {
        "album_id":str(album_id),
        "album_name":name,
        "album_owner":user,
        "sharedWith":{}
    }
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)
    table.put_item(Item=album)
    return album

def lambda_handler(event, context):
    print(event)
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

    if "name" not in body:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Parameter (name) is required'})
        }

    if is_duplicate_name(body["name"], user):
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Duplicate album name'})
        }
    album = create_album(body["name"], user)
    return{
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(album)
    }       