import boto3
import json
from datetime import datetime
import os

files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]
s3_bucket_name = os.environ["USER_FILES_BUCKET"]

def lambda_handler(event, context):
    print("Entered the function")
    user = event["requestContext"]["authorizer"]["X-User-Id"]
    file_id = event["queryStringParameters"]["file_id"]

    print(file_id)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(files_metadata_table)

    response = table.get_item(
        Key={
            'file_id': file_id,
            'user': user
        }
    )
    file_metadata = response.get('Item')

    print(file_metadata)
    # Check if file exists
    if not file_metadata:
        return {
            'statusCode': 404,
            'body': 'File not found'
        }

    # Get the file's S3 key
    file_key = file_metadata['file_key']

    print(file_key)
    # Generate a presigned URL for the file
    s3_client = boto3.client('s3')
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': s3_bucket_name,
            'Key': file_key
        }
    )
    print(presigned_url)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({
            'presigned_url': presigned_url
        })
    }
