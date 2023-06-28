const multipart = require("functions/UploadFileToS3Bucket/node_modules/parse-multipart");
const AWS = require("functions/UploadFileToS3Bucket/node_modules/aws-sdk");
const uuid = require("functions/UploadFileToS3Bucket/node_modules/uuid");

const userFilesBucketName = process.env.USER_FILES_BUCKET;
const table_name = process.env.USER_FILES_METADATA_TABLE;

const s3 = new AWS.S3();
const dynamodb = new AWS.DynamoDB.DocumentClient();

async function uploadFileToS3(params) {
  return new Promise((resolve, reject) => {
    s3.upload(params, (err, data) => {
      if (err) {
        reject(err);
      } else {
        resolve(data);
      }
    });
  });
}

async function putFileMetadataToDynamoDB(fileId, user, album, filename) {
  const current_time = new Date().toISOString();

  const fileMetadata = {
    file_id: fileId,
    created_at: current_time,
    description: "",
    file_key: filename,
    last_modified: current_time,
    user: user,
    album: album,
    shared_with: []
  };

  console.log(fileMetadata);

  const params = {
    TableName: table_name,
    Item: fileMetadata
  };

  return dynamodb.put(params).promise();
}

async function deleteFileMetadataFromDynamoDB(fileId) {
  const params = {
    TableName: table_name,
    Key: {
      file_id: fileId
    }
  };

  return dynamodb.delete(params).promise();
}

exports.handler = async (event, context, callback) => {
  const bodyBuffer = Buffer.from(event.body, 'base64');
  const boundary = multipart.getBoundary(event.headers["content-type"]);

  const user = event.requestContext.authorizer["X-User-Id"];
  const parts = multipart.Parse(bodyBuffer, boundary);
  const album = event.queryStringParameters["album"];
  let filename = parts[0].filename;
  const decodedImage = Buffer.from(parts[0].data, 'base64');

  filename = `${user}/${filename}`;

  let fileId;
  try {
    // Upload metadata to DynamoDB
    fileId = uuid.v1();
    await putFileMetadataToDynamoDB(fileId, user, album, filename);
  } catch (error) {
    console.log(error.message);
    return {
      statusCode: 500,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
        "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
      },
      body: JSON.stringify({ message: "Failed to upload file metadata to DynamoDB." })
    };
  }

  const params = {
    Body: decodedImage,
    Bucket: userFilesBucketName,
    Key: filename
  };

  try {
    // Upload file to S3
    const s3UploadResult = await uploadFileToS3(params);

    const response = {
      statusCode: 200,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
        "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
      },
      body: JSON.stringify({ fileID: fileId })
    };

    return response;
  } catch (error) {
    // Delete file metadata from DynamoDB if S3 upload fails
    await deleteFileMetadataFromDynamoDB(fileId);

    return {
      statusCode: 500,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
        "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, authenticationToken, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
      },
      body: JSON.stringify({ message: "Failed to upload file to S3." })
    };
  }
};