import boto3
import json
from datetime import datetime
import os

albums_table = os.environ["ALBUMS_TABLE"]

def lambda_handler(event, context):

    user = event["requestContext"]["authorizer"]["X-User-Id"]


    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(albums_table)

    expression_attribute_values = {
        ':album_owner': user
    }
    filter_expression = 'album_owner = :album_owner'


    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    albums = response['Items']
    
    for album in albums:
        shared_with = [el for el in album["shared_with"] if el!=""]
        album["shared_with"] = shared_with
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(albums)
    }
