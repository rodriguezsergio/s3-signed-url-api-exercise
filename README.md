DataStax Exercise
===========================

This is a simple API that allows a user to generate presigned URLs for use with S3. A Makefile is provided to get started quickly. It is assumed that the end user has at least Docker installed and, optionally, `make`.

## Requirements
AWS credentials will be required to run the API and tests successfully. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` should be set to their appropriate values in your environment. The Makefile can also be used to create the pre-defined S3 bucket assuming the AWS CLI is installed.

- `make run`: Run the API and redis only
- `make test`: Run the API, redis, and the tests
- `make bootstrap`: Create the pre-defined S3 bucket
- `make all-test`: Creates the S3 bucket and runs `make test`
- `make all`: Creates the S3 bucket and runs `make run`
- `make teardown`: Stops the Docker containers, deletes all files from the S3 bucket, and deletes the bucket itself

## Configuration Variables

| Variable              | Default                  |
|------------           |--------------------------|
| AWS_REGION            | us-east-1                |
| AWS_ACCESS_KEY_ID     |                          |
| AWS_SECRET_ACCESS_KEY |                          |
| REDIS_HOST            | redis                    |
| REDIS_PORT            | 6379                     |
| FILE_ACL              | private*                 |
| S3_BUCKET             | dmc-srodriguez-20181130  |
| UPLOAD_URL_TTL        | 3600 (seconds)           |
| DOWNLOAD_URL_TTL      | 60 (seconds)             |
| API_PORT              | 8080                     |
| WORKERS               | 1 (for the sanic server) |

* https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl

