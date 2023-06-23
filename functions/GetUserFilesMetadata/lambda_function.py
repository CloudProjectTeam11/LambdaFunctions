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

    username = body['username']
    folder = body.get('folder')

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_metadata_table)

    expression_attribute_values = {
        ':user': username
    }
    filter_expression = '#usr = :user'

    if folder:
        expression_attribute_values[':folder'] = f'{username}/{folder}/'
        filter_expression += ' and begins_with(file_key, :folder)'

    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeNames={
            '#usr': 'user'
        },
        ExpressionAttributeValues=expression_attribute_values
    )

    files = response['Items']
    
    # Convert last_modified string to date and sort in descending order
    files = sorted(files, key=lambda x: datetime.fromisoformat(x['last_modified']), reverse=True)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(files)
    }
