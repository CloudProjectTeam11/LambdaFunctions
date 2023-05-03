const multipart = require("parse-multipart")
const AWS = require("aws-sdk")

var s3 = new AWS.S3();

exports.handler = async (event, context, callback) => {
    let bodyBuffer = new Buffer(event['body'].toString(), 'base64');
    let boundary = multipart.getBoundary(event.headers["content-type"]);
        
    let parts = multipart.Parse(bodyBuffer, boundary);
    let folder = event.queryStringParameters["folder"];
    let filename = parts[0].filename;
    if (folder != undefined){
        filename = folder + "/" + filename;
    }

    let decodedImage = Buffer.from(parts[0].data, 'base64');
    
    let params = {
        "Body" : decodedImage,
        "Bucket": "demo-app-content",
        "Key" : filename
    }

    const result = await s3.upload(params).promise();
    const response = {
        statusCode: 200,
        body: JSON.stringify('Hello from Lambda!'),
    };
    return response;
};