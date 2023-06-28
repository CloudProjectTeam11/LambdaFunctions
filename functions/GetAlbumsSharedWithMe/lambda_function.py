import boto3
import json
from datetime import datetime
import os

albums_table = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]
    owner = event.get('queryStringParameters', {}).get('album_owner')
    print("OWNER:" , owner)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)

    filter_expression = 'contains(shared_with, :user)'
    expression_attribute_values = {
        ':user': user
    }

    if owner != "":
        filter_expression += ' and album_owner = :owner'
        expression_attribute_values[':owner'] = owner

    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    albums = response['Items']
    output = []

    for album in albums:
        album_metadata = {
            "album_id": album["album_id"],
            "album_name": album["album_name"],
            "album_owner": album["album_owner"],
            "shared_with": list(album["shared_with"])
        }
        output.append(album_metadata)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(output)
    }
