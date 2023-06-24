import json
import functions.DefaultAuthorizer.package.jwt as jwt

def create_policy(access, context):
    if access == "Allow":
        return {
            "principalId": "yyyyyyyy",
            "policyDocument":{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": access,
                        "Resource": "arn:aws:execute-api:eu-central-1:665416417349:uy6cr0t91b/*/*"
                    }
                ]
            },
            "context": context
        }
    else:
        return {
            "principalId": "yyyyyyyy",
            "policyDocument":{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": access,
                        "Resource": "arn:aws:execute-api:eu-central-1:665416417349:uy6cr0t91b/*/*"
                    }
                ]
            }
        }        

def lambda_handler(event, context):
    secret_key = "secret"
    token = event["authorizationToken"]
    policy = None
    try:
        payload = jwt.decode(token, secret_key, algorithms="HS256")
        print("token je validan")
        access = "Allow"
        context = {
            'X-User-Id': payload["user"]
        }
        policy = create_policy(access, context)        
    except:
        print("token je nevalidan")        
        access = "Deny"
        policy = create_policy(access, None)
    
    return policy
    