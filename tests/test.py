import requests
import redis
import os
import tempfile
import json
import time

BASE_URL = 'http://{}:{}/asset/'.format(os.environ['API_HOST'], os.environ['API_PORT'])

def get_upload_url():
    r = requests.post(BASE_URL)
    json_response = r.json()
    assert(r.status_code == 200)
    assert('upload_url' and 'id' in json_response)
    assert(type(json_response['id']) == str)
    assert('s3.amazonaws.com' and 'AWSAccessKeyId' in json_response['upload_url'])
    return json_response

def check_redis_key(redis_conn, asset_id, value):
    resp = redis_conn.get(asset_id)
    assert(resp.decode('utf-8') == value)

def upload_file(upload_url):
    tmpfile = tempfile.TemporaryFile()
    tmpfile.write(b'DataStax S3 asset uploader test.\n')
    tmpfile.seek(0)
    r = requests.put(upload_url, data = tmpfile.read())
    assert(r.status_code == 200)
    tmpfile.close()

def mark_file_upload(asset_id, input_data, expected_code):
    r = requests.put('{}{}'.format(
        BASE_URL,
        asset_id
    ),
        data = json.dumps(input_data
    ))
    assert(r.status_code == expected_code)

def get_download_url(asset_id, expected_code, timeout=60):
    r = requests.get('{}{}?timeout={}'.format(
        BASE_URL,
        asset_id,
        timeout
    ))
    assert(r.status_code == expected_code)
    if r.status_code == 200:
        assert('download_url' in r.json())
        return r.json()['download_url']
    else:
        return

def confirm_download(url):
    r = requests.get(url)
    assert(r.content == b'DataStax S3 asset uploader test.\n')

def check_expired_download(url):
    r = requests.get(url)
    assert(r.status_code == 403)

def main():
    print('Starting tests.')
    redis_conn = redis.Redis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']))

    # end to end
    resp = get_upload_url()
    check_redis_key(redis_conn, resp['id'], 'NOT_UPLOADED')
    upload_file(resp['upload_url'])
    mark_file_upload(resp['id'], {'Status': 'uploaded'}, 200)
    check_redis_key(redis_conn, resp['id'], 'UPLOADED')
    download_url = get_download_url(resp['id'], 200, 10)
    confirm_download(download_url)

    # pass in a bogus payload
    mark_file_upload(resp['id'], {'data': 'stax'}, 400)

    # pass in a bad UUID with PUT
    mark_file_upload('bad-put-1234567890', {'Status': 'uploaded'}, 404)

    # pass in a bad UUID with GET
    get_download_url('bad-get-1234567890', 404)

    # skip marking item as uploaded
    resp = get_upload_url()
    upload_file(resp['upload_url'])
    get_download_url(resp['id'], 404)

    # skip uploading item at all
    resp = get_upload_url()
    mark_file_upload(resp['id'], {'Status': 'uploaded'}, 200)
    check_redis_key(redis_conn, resp['id'], 'UPLOADED')
    get_download_url(resp['id'], 404)

    # confirm URL had short TTL
    time.sleep(10)
    check_expired_download(download_url)

    print('All tests passed.')

main()
