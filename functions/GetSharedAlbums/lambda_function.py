import boto3
import json
from datetime import datetime
import os

albums_table = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):

    user = event["requestContext"]["authorizer"]["X-User-Id"]


    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)

    expression_attribute_values = {
        ':username': user
    }
    filter_expression = 'contains(shared_with, :username)'


    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    albums = response['Items']
    
    output = []

    for album in albums:
        table = dynamodb.Table(files_table)
        response = table.scan(
            FilterExpression='album = :album_id',
            ExpressionAttributeValues={':album_id' : album["album_id"]}
        )
        for el in response["Items"]:
            el["tags"] = list(el["tags"])
        obj = {
            "album": album["album_id"],
            "files": response["Items"]
        }
        output.append(obj)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(output)
    }
