import json
import boto3
import datetime
import os

bucket_name = os.environ["USER_FILES_BUCKET"]
table_name = os.environ["USER_FILES_METADATA_TABLE"]

def lambda_handler(event, context):
    filename = event["Records"][0]["s3"]["object"]["key"]
    
    s3 = boto3.client('s3')
    response = s3.head_object(Bucket=bucket_name, Key=filename)
    metadata = response['Metadata']
    
    file_id = metadata["file-id"]
    is_changed = metadata["is-changed"]
    user_id = metadata["user-id"]
    album = metadata["album"]
    current_time = datetime.datetime.now().isoformat()
    
    dynamodb = boto3.client('dynamodb')
    
    if is_changed == "false":
        dynamodb.put_item(
                TableName=table_name,
                Item = {
                    'file_id': {'S': file_id},
                    'created_at': {'S': current_time},
                    'description': {'S': ''},
                    'file_key': {'S': filename},
                    'last_modified': {'S': current_time},
                    'user': {'S': user_id},
                    'album': {'S': album}
                }
            )
    
    else:
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'file_id': {'S':file_id}
            },
            UpdateExpression='SET last_modified = :new_datetime',
            ExpressionAttributeValues={
                ':new_datetime': {'S':current_time}
            }
        )  
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
