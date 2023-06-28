import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
table_name = os.environ["USER_FILES_METADATA_TABLE"]
users_table = os.environ["USERS_TABLE"]
sqs = boto3.client('sqs')
queue_url = 'https://sqs.eu-central-1.amazonaws.com/665416417349/FileChangeQueue'

def lambda_handler(event, context):
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

    file_id = body['file_id']
    description = body['description']
    tags = set(body['tags'])
    album = body['album']

    if not file_id:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Missing file identifier'})
        }

    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'file_id': file_id})

    if not response.get('Item'):
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps('File not found')
        }

    user = event["requestContext"]["authorizer"]["X-User-Id"]
    userTable = table.get_item(
        Key={'file_id': file_id},
        ProjectionExpression='#u',
        ExpressionAttributeNames={'#u': 'user'}
    )

    if user != userTable["Item"]["user"]:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message': 'Invalid user'})
        }

    update_expression = 'SET #desc = :desc, #tags = :tags, #alb = :album'
    expression_attribute_names = {'#desc': 'description', '#tags': 'tags', '#alb': 'album'}
    expression_attribute_values = {':desc': description, ':tags': tags, ':album': album}
    table.update_item(
        Key={'file_id': file_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )

    # Fetch user data from users_table
    user_table = dynamodb.Table(users_table)
    user_response = user_table.get_item(Key={'username': user})

    if not user_response.get('Item'):
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps('User not found')
        }

    user_data = user_response['Item']
    user_email = user_data['email']
    username = user_data['username']

    # Send email notification
    message_payload = {
        'user': {
            'email': user_email,
            'username': username
        },
        'album': {
            'album_name': album
        },
        'file': {
            'file_name': response['Item']['file_key']
        },
        'command': 'edited'
    }

    print(message_payload)

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_payload)
    )

    print(response)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({'message': 'File updated successfully'})
    }
