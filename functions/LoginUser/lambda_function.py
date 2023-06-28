import json
import functions.LoginUser.package.jwt as jwt
import hashlib
import boto3
import datetime
import os
from boto3.dynamodb.conditions import Key

users_table = os.environ["USERS_TABLE"]

def hash_password(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
    #return password

def validate_user(email : str, password : str):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(users_table)
    hashed_password = hash_password(password)
    response = table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    if response['Count'] != 1:
        return None
    
    user = response['Items'][0]
    if user['password'] == hashed_password:
        return user
    
    return None

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
        
    if 'email' not in body:
        return {
            'statusCode' : 400,
            'headers': {
			'Access-Control-Allow-Origin': '*',
		    },
            'body': json.dumps({'message':'Parameter (email) is required'})
        }
    if 'password' not in body:
        return {
            'statusCode' : 400,
            'headers': {
			'Access-Control-Allow-Origin': '*',
		    },
            'body': json.dumps({'message':'Parameter (password) is required'})
        }
    
    email = body['email']
    password = body["password"]
    
    user = validate_user(email, password)
    if user is not None:
        if not user.get("is_active"):
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'message':'Your account is not approved'})
            }
        userID = user['userID']
        secret_key = 'secret'
        tz = datetime.timezone(datetime.timedelta(hours=1), name='CET')
        expiration_datetime = datetime.datetime.now(tz) + datetime.timedelta(hours=24)
        payload = {'user':userID, 'email': email, 'exp':expiration_datetime}
        token = jwt.encode(payload, secret_key, algorithm='HS256')    
        return {
            'statusCode': 200,
            'headers': {
			'Access-Control-Allow-Origin': '*',
		    },
            'body': json.dumps({'user':userID, 'token':token})
        }
    return {
        'statusCode': 400,
        'headers': {
			'Access-Control-Allow-Origin': '*',
		},
        'body': json.dumps({'message':'Email or password is not correct'})
    }