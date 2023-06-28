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
    
    dynamodb = boto3.resource('dynamodb')
    
    if is_changed == "false":
        new_file = {
            "file_id": str(file_id),
            "created_at": str(current_time),
            "description": "",
            "file_key": str(filename),
            "last_modified": str(current_time),
            "user": str(user_id),
            "album": str(album),
            "shared_with": set([''])
        }
        table = dynamodb.Table(table_name)
        table.put_item(Item=new_file)
    
    else:
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'file_id': file_id
            },
            UpdateExpression='SET last_modified = :new_datetime',
            ExpressionAttributeValues={
                ':new_datetime': current_time
            }
        )  
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
