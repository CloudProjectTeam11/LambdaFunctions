import boto3
import json
from datetime import datetime
import os

files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]
albums_table = os.environ["ALBUMS_TABLE"]


def get_album_contents(album_id):
    dynamodb = boto3.resource('dynamodb')
    files_table = dynamodb.Table(files_metadata_table)

    response = files_table.scan(
        FilterExpression='album = :album_id',
        ExpressionAttributeValues={':album_id': album_id}
    )

    files = response['Items']
    for file in files:
        try:
            file["tags"] = list(file["tags"])
        except:
            print("no tags")
    return files


def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]

    album = event.get('queryStringParameters', {}).get('album')
    print("ALBUM:", album)
    dynamodb = boto3.resource('dynamodb')
    files_table = dynamodb.Table(files_metadata_table)
    albums_table = dynamodb.Table(albums_table)

    # Check if the user is the owner of the album or has access to it
    if album:
        response = albums_table.get_item(Key={'album_id': album})
        album_data = response.get('Item')

        if not album_data:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps("Album not found")
            }

        if user != album_data['album_owner'] and user not in album_data['shared_with']:
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps("Access forbidden")
            }

        album_contents = get_album_contents(album)
    else:
        # Retrieve all files for the user
        expression_attribute_values = {
            ':user': user
        }
        filter_expression = '#username = :user'

        response = files_table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames={
                '#username': 'user'
            }
        )

        album_contents = response['Items']
        for file in album_contents:
            try:
                file["tags"] = list(file["tags"])
            except:
                print("no tags")

    # Sort the album contents by last_modified in descending order
    album_contents = sorted(album_contents, key=lambda x: datetime.fromisoformat(x['last_modified']), reverse=True)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(album_contents)
    }
