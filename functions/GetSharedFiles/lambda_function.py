import boto3
import json
from datetime import datetime
import os

albums_table = os.environ["ALBUMS_TABLE"]
files_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    user = event["requestContext"]["authorizer"]["X-User-Id"]
    owner = event['queryStringParameters'].get('owner', '')

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_table)

    filter_expression = 'contains(shared_with, :username) and #owner = :owner'
    expression_attribute_values = {':username': user, ':owner': owner}
    expression_attribute_names = {'#owner': 'user'}

    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ExpressionAttributeNames=expression_attribute_names
    )

    files = response['Items']
    for file in files:
        file['tags'] = list(file.get('tags', []))

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(files)
    }
