import json
import boto3
import hashlib
import re
import os
import uuid
from boto3.dynamodb.conditions import Key

users_table = os.environ["USERS_TABLE"]
albums_table = os.environ["ALBUMS_TABLE"]

def hash_password(password: str):
	return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_user_exist(username: str):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(users_table)
	response = table.get_item(Key={'username': username})
	return response.get('Item') is None


def check_email_exist(email: str):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(users_table)
	response = table.query(
		IndexName='EmailIndex',
		KeyConditionExpression=Key('email').eq(email)
	)
	return response['Count'] == 0


def check_password_format(password: str):
	pattern = r"^(?=.*[A-Z])(?=.*\d.*\d.*\d).+$"
	return re.search(pattern, password)


def check_email(email: str):
	pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
	return re.match(pattern, email)


def put_user(user: dict):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(users_table)
	table.put_item(Item=user)


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
	
	if 'email' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (email) is required'})
		}
	if 'password' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (password) is required'})
		}
	
	if 'name' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (name) is required'})
		}
	if 'last_name' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (last_name) is required'})
		}
	
	if 'birth_date' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (birth_date) is required'})
		}
	if 'username' not in body:
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Parameter (username) is required'})
		}
	
	if not check_user_exist(body["username"]):
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Username already exists'})
		}
	
	if not check_email_exist(body["email"]):
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Email already exists'})
		}
	
	if not check_password_format(body["password"]):
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Password does not match the required format'})
		}
	if not check_email(body["email"]):
		return {
			'statusCode': 400,
			'headers': {
				'Access-Control-Allow-Origin': '*',
			},
			'body': json.dumps({'message': 'Invalid email address '})
		}
	
	user = {
		'email': body['email'],
		'password': hash_password(body["password"]),
		'last_name': body["last_name"],
		'birth_date': body["birth_date"],
		'name': body["name"],
		'username': body["username"],
		'userID': body["username"],
		"is_active":True
		
	}
	album_id = uuid.uuid1()
	album = {
        "album_id":str(album_id),
        "album_name":"Default Album",
        "album_owner":user['username'],
        "shared_with":set([''])
    }
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(albums_table)
	table.put_item(Item=album)

	put_user(user)
	
	return {
		'statusCode': 200,
		'headers': {
			'Access-Control-Allow-Origin': '*',
		},
		'body': json.dumps({'user': user["username"]})
	}
