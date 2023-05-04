import boto3
import json

dynamodb = boto3.resource('dynamodb')
table_name = 'files_metadata'

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except:
        return {
            'statusCode' : 400,
             'headers': {
            'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'message':'Invalid request'})
        }



    file_id = body['file_id']
    description = body['description']
    tags = body['tags']

    if not file_id:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing file identificator')
        }
        
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'file_id': file_id})
    
    if not response.get('Item'):
        return {
            'statusCode': 404,
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
            'body': json.dumps('Invalid user')
        }
    update_expression = 'SET #desc = :desc, #tags = :tags'
    expression_attribute_names = {'#desc': 'description', '#tags': 'tags'}
    expression_attribute_values = {':desc': description, ':tags': tags}
    table.update_item(
        Key={'file_id': file_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('File updated successfully')
    }