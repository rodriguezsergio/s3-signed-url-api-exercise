from sanic import Sanic, response
import boto3.session
import botocore
import asyncio
import aioredis
import os
import logging
import uuid
app = Sanic()

async def is_asset_in_cache(asset_id):
    if asset_id not in app.cache:
        logging.info('Asset ID, {}, not present in app.cache.'.format(asset_id))
        redis_response = await app.redis.execute('get', asset_id)

        if redis_response is None:
            logging.info('Asset ID, {}, not present in Redis.'.format(asset_id))
            return False

        app.cache[asset_id] = redis_response.decode('utf-8')
        logging.info('Cache state: {}.'.format(app.cache))
    return True

@app.listener('before_server_start')
async def start_up(app, loop):
    app.cache = {}
    session = boto3.session.Session(region_name=os.environ['AWS_REGION'])
    app.client = session.client('s3')
    app.redis = await aioredis.create_pool(
        address=(os.environ['REDIS_HOST'], os.environ['REDIS_PORT']),
        minsize=5,
        maxsize=10,
        loop=loop
    )

@app.listener('after_server_stop')
async def shut_down(app, loop):
    app.redis.close()
    await app.redis.wait_closed()

@app.route('/asset', methods=['POST'])
async def generate_upload_url(request):
    uuid_str = str(uuid.uuid4())

    try:
        s3_response = app.client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'ACL': os.environ['FILE_ACL'],
                'Bucket': os.environ['S3_BUCKET'],
                'Key': uuid_str
            },
            ExpiresIn=int(os.environ['UPLOAD_URL_TTL'])
        )
    except botocore.exceptions.ClientError as e:
        logging.error('An error occurred while calling "generate_presigned_url" in generate_upload_url().')
        logging.error('Error Status Code: {}.'.format(e.response['Error']['Code']))
        logging.error('Error Message: {}.'.format(e.response['Error']['Message']))
        return response.json(
                {'message': 'An error occurred when attempting to generate the upload URL.'},
                status=500
            )
    else:
        app.cache[uuid_str] = 'NOT_UPLOADED'
        await app.redis.execute('set', uuid_str, 'NOT_UPLOADED')
        logging.info('Cache state: {}.'.format(app.cache))

        return response.json({
            'upload_url': s3_response,
            'id': uuid_str
        })

@app.route('/asset/<asset_id>', methods=['PUT'])
async def mark_as_uploaded(request, asset_id):
    if (request.json != {'Status': 'uploaded'}):
        return response.json(
            {'message': 'Expected JSON with the contents: {"Status": "uploaded"}.'},
            status=400
        )

    in_cache = await is_asset_in_cache(asset_id)
    if not in_cache:
        return response.json(
                {'message': 'Asset ID not found.'},
                status=404
            )

    app.cache[asset_id] = 'UPLOADED'
    await app.redis.execute('set', asset_id, 'UPLOADED')
    logging.info('Cache state: {}.'.format(app.cache))

    return response.HTTPResponse(status=200)

@app.route('/asset/<asset_id>', methods=['GET'])
async def generate_download_url(request, asset_id):
    in_cache = await is_asset_in_cache(asset_id)
    if not in_cache:
        return response.json(
                {'message': 'Asset ID not found.'},
                status=404
            )

    if app.cache[asset_id] != 'UPLOADED':
        return response.json(
                {'message': 'Asset ID has not been set to "uploaded".'},
                status=404
            )

    logging.info('Checking if asset, {}, is present on S3.'.format(asset_id))
    try:
        app.client.head_object(
            Bucket=os.environ['S3_BUCKET'],
            Key=asset_id
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logging.info('Asset ID not found on S3.')
            return response.json(
                    {'message': 'Asset ID not found on S3.'},
                    status=404
                )
        else:
            logging.error('An error occurred when calling "head_object" on the asset: {}.'.format(asset_id))
            logging.error('Error Status Code: {}.'.format(e.response['Error']['Code']))
            logging.error('Error Message: {}.'.format(e.response['Error']['Message']))
            return response.json(
                    {'message': 'An error occurred while attempting to check for the requested file.'},
                    status=500
                )

    download_url_ttl = int(os.environ['DOWNLOAD_URL_TTL'])
    if 'timeout' in request.args:
        download_url_ttl = int(request.args['timeout'][0])

    logging.info('Attempting to generate download URL for asset, {}.'.format(asset_id))
    try:
        s3_response = app.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.environ['S3_BUCKET'],
                'Key': asset_id
            },
            ExpiresIn=download_url_ttl
        )
    except botocore.exceptions.ClientError as e:
        logging.error('An error occurred while calling "generate_presigned_url" in generate_download_url().')
        logging.error('Error Status Code: {}.'.format(e.response['Error']['Code']))
        logging.error('Error Message: {}.'.format(e.response['Error']['Message']))
        return response.json(
                {'message': 'An error occurred when attempting to generate the download URL.'},
                status=500
            )
    else:
        return response.json({
            'download_url': s3_response
        })

if __name__ == "__main__":
    # write logs to disk
    logFormat='%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=logFormat, filename='logs/datastax.log', level=logging.INFO)
    logging.basicConfig(format=logFormat, level=logging.INFO)
    logger = logging.getLogger()

    # configure console logging to match
    consoleLogger = logging.StreamHandler()
    consoleLogger.setLevel(logging.INFO)
    formatter = logging.Formatter(logFormat)
    consoleLogger.setFormatter(formatter)

    logger.addHandler(consoleLogger)

    app.run(host='0.0.0.0',
            port=os.environ['API_PORT'],
            workers=int(os.environ['WORKERS'])
            )
