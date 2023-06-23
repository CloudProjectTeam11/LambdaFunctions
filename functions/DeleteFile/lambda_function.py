import boto3
import json
import os

files_metadata_table = os.environ["USER_FILES_METADATA_TABLE"]
file_bucket = os.environ["USER_FILES_BUCKET"]

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.resource('s3')
    
    try:
        print("Hello")
    except:
        return {
            'statusCode' : 400,
             'headers': {
            'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message':'Invalid request'})
        }
        
    try:
        # Iterate through the array of file_id and file_key pairs
        for item in event:
            file_id = item['file_id']
            file_key = item['file_key']
            
            # Delete the item from DynamoDB
            table = dynamodb.Table(files_metadata_table)
            table.delete_item(Key={'file_id': file_id})
            
            # Delete the file from the S3 bucket
            s3.Object(file_bucket, file_key).delete()
            
        return {
            'statusCode': 200,
             'headers': {
            'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message':'Files deleted sucessfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
             'headers': {
            'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message':'Error deleting the files'})
        }
