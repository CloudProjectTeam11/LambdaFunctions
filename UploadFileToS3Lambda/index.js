const multipart = require("parse-multipart");
const AWS = require("aws-sdk");
const uuid = require("uuid");

var s3 = new AWS.S3();

async function getS3Object(objectKey) {
    const params = {
      Bucket: "demo-app-content",
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
    let folder = event.queryStringParameters["folder"];
    let filename = parts[0].filename;
    if (folder != undefined){
        filename = folder + "/" + filename;
    }
    filename = user + "/" + filename;

    let decodedImage = Buffer.from(parts[0].data, 'base64');
    
    const data = await getS3Object(filename);
    console.log(data);
    let params = {
        "Body" : decodedImage,
        "Bucket": "demo-app-content",
        "Key" : filename,
    }
    let fileId = "";
    if(data == undefined){
        fileId = uuid.v1();
        params["Metadata"] = {
            "file-id" : fileId,
            "user-id" : user,
            "is-changed" : "false"
        };
    }else{        
        fileId = data.Metadata["file-id"];
        params["Metadata"] = {
            "file-id" : fileId,
            "user-id" : user,
            "is-changed":"true"
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