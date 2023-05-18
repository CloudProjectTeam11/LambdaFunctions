import json
import jwt

def lambda_handler(event, context):
    secret_key = "secret"
    token = event["authorizationToken"]
    try:
        payload = jwt.decode(token, secret_key, algorithms="HS256")
        access = "Allow"
    except:
        access = "Deny"
    context = {
        'X-User-Id': payload["user"]
    }
    
    return {
        "principalId": "yyyyyyyy",
        "policyDocument":{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": access,
                    "Resource": "arn:aws:execute-api:eu-central-1:665416417349:rf3ziq3c61/*/*"
                }
            ]
        },
        "context": context
    }
    