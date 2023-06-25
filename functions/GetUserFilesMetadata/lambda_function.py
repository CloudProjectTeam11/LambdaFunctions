import boto3
import json
from datetime import datetime
import os

files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        print(body)
    except:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Invalid request'})
        }
    user = event["requestContext"]["authorizer"]["X-User-Id"]

    album = body.get('album')

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_metadata_table)

    expression_attribute_values = {
        ':user': user
    }
    filter_expression = '#username = :user'

    if album:
        expression_attribute_values[':album'] = album
        filter_expression += ' AND album = :album'

    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ExpressionAttributeNames={
            '#username': 'user'
        }
    )

    files = response['Items']
    
    # Convert last_modified string to date and sort in descending order
    files = sorted(files, key=lambda x: datetime.fromisoformat(x['last_modified']), reverse=True)
    files = list(files)
    for file in files:
        file["tags"] = list(file["tags"])
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(files)
    }
