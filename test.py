import botocore_tornado.session
import botocore.session
from tornado import gen
from tornado.ioloop import IOLoop

bucket = 'botocore-tornado-test'  # change this to your bucket name
key = 'xyzzy'  # a subfolder under the bucket
filename = 'testfile.txt'  # the file we will put into S3
region = 'us-east-1'  # change this to your region
acl = 'public-read'  # we are going to set the ACL to public-read so we can access the file via a url


@gen.coroutine
def main_async():
    session = botocore_tornado.session.get_session()
    session.set_debug_logger()
    session.set_debug_logger('botocore_tornado')
    s3 = session.get_service('s3')
    endpoint = s3.get_endpoint(region)

    print "========================="
    print "====== ASYNC TEST ======="
    print "========================="

    print
    print "uploading the file to s3"
    fp = open('./' + filename, 'rb')
    operation = s3.get_operation('PutObject')
    http_response, response_data = yield operation.call(endpoint,
                                                        bucket=bucket,
                                                        key=key + '/' + filename,
                                                        body=fp)

    print http_response
    print response_data
    print
    print "getting s3 object properties of file we just uploaded"
    operation = s3.get_operation('GetObjectAcl')
    http_response, response_data = yield operation.call(endpoint,
                                                        bucket=bucket,
                                                        key=key + '/' + filename)
    print http_response
    print response_data
    print
    print "setting the acl to public-read"
    operation = s3.get_operation('PutObjectAcl')
    http_response, response_data = yield operation.call(endpoint,
                                                        bucket=bucket,
                                                        key=key + '/' + filename,
                                                        acl=acl)
    print http_response
    print response_data
    print
    print "The url of the object is:"
    print
    print 'http://'+bucket+'.s3.amazonaws.com/' + key + '/' + filename


def main_sync():
    session = botocore.session.get_session()
    session.set_debug_logger()
    s3 = session.get_service('s3')
    endpoint = s3.get_endpoint(region)

    print "========================="
    print "====== SYNC TEST ========"
    print "========================="

    print
    print "uploading the file to s3"

    fp = open('./' + filename, 'rb')
    operation = s3.get_operation('PutObject')
    http_response, response_data = operation.call(endpoint,
                                                  bucket=bucket,
                                                  key=key + '/' + filename,
                                                  body=fp)
    print http_response
    print response_data
    print
    print "getting s3 object properties of file we just uploaded"
    operation = s3.get_operation('GetObjectAcl')
    http_response, response_data = operation.call(endpoint,
                                                  bucket=bucket,
                                                  key=key + '/' + filename)
    print http_response
    print response_data
    print
    print "setting the acl to public-read"
    operation = s3.get_operation('PutObjectAcl')
    http_response, response_data = operation.call(endpoint,
                                                  bucket=bucket,
                                                  key=key + '/' + filename,
                                                  acl=acl)
    print http_response
    print response_data
    print
    print "The url of the object is:"
    print
    print 'http://'+bucket+'.s3.amazonaws.com/' + key + '/' + filename


if __name__ == '__main__':
    with open(filename, 'w') as f:
        f.write("botocore tornado upload test file")
    IOLoop.instance().run_sync(main_async)
    main_sync()
