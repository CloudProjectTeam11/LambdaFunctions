const multipart = require("functions/UploadFileToS3Bucket/node_modules/parse-multipart");
const AWS = require("functions/UploadFileToS3Bucket/node_modules/aws-sdk");
const uuid = require("functions/UploadFileToS3Bucket/node_modules/uuid");

var s3 = new AWS.S3();
var dynamodb = new AWS.DynamoDB();
const userFilesBucketName = process.env.USER_FILES_BUCKET;
const albumsTable = process.env.ALBUMS_TABLE

async function getS3Object(objectKey) {
    const params = {
      Bucket: userFilesBucketName,
      Key: objectKey
    };
  
    try {
      const data = await s3.headObject(params).promise();
      return data
    } catch (error) {
        return undefined;
    }
}

exports.handler = async (event, context, callback) => {
    let bodyBuffer = Buffer.from(event['body'], 'base64');
    let boundary = multipart.getBoundary(event.headers["content-type"]);
    let user = event.requestContext.authorizer["X-User-Id"];
    let parts = multipart.Parse(bodyBuffer, boundary);
    let album = event.queryStringParameters["album"];
    let filename = parts[0].filename;

    let dynamoParams = {
        TableName: albumsTable,
        Key: {
            album_id: { S: album },
        }
    };
    const albumResult = await dynamodb.getItem(dynamoParams).promise();
    if(albumResult.Item){
        const albumObj = albumResult.Item;
        console.log(albumObj);
        console.log(user);
        if(albumObj["album_owner"]["S"] != user){
            return {
                statusCode: 403,
                headers: {
                    "Access-Control-Allow-Origin" : "*",
                    "Access-Control-Allow-Credentials" : "true",
                    "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
                    "Access-Control-Allow-Headers" : "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
                },
                body: JSON.stringify({"message": "You have no access rights to this album"})
            };
        }
    }
    else{
        return {
            statusCode: 404,
            headers: {
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Credentials" : "true",
                "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
                "Access-Control-Allow-Headers" : "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
            },
            body: JSON.stringify({"message": "Album with given id not found"})
        };
    }
    filename = user + "/" + filename;

    let decodedImage = Buffer.from(parts[0].data, 'base64');
    
    const data = await getS3Object(filename);
    console.log(data);
    let params = {
        "Body" : decodedImage,
        "Bucket": userFilesBucketName,
        "Key" : filename
    }
    let fileId = "";
    if(data == undefined){
        fileId = uuid.v1();
        params["Metadata"] = {
            "file-id" : fileId,
            "user-id" : user,
            "is-changed" : "false",
            "album" : album
        };
    }else{        
        fileId = data.Metadata["file-id"];
        params["Metadata"] = {
            "file-id" : fileId,
            "user-id" : user,
            "is-changed":"true",
            "album" : album
        }
    }
    console.log(params);
    const result = await s3.upload(params).promise();

    const response = {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Origin" : "*",
            "Access-Control-Allow-Credentials" : "true",
            "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
            "Access-Control-Allow-Headers" : "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
        },
        body: JSON.stringify({"fileID": fileId})
    };
    return response;
};