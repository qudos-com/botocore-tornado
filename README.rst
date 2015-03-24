botocore-tornado
================

This module provides subclasses of `botocore <https://github.com/boto/botocore>`__
classes that use the tornado AsyncHTTPClient to make requests. As far as 
possible, the api is kept the same as the botocore api, the only difference is 
that Operation.call returns a Future that is resolved when the http request is 
complete.


Installation
------------

.. code-block:: bash

    pip install botocore-tornado


Example
-------

Uploading a file to S3:

.. code-block:: python

    import botocore.session

    session = botocore.session.get_session()
    s3 = session.get_service('s3')
    endpoint = s3.get_endpoint(region)

    fp = open('./testfile.txt', 'rb')
    operation = s3.get_operation('PutObject')
    http_response, response_data = operation.call(endpoint,
                                                  bucket=bucket,
                                                  key=key + '/' + filename,
                                                  body=fp)


Using botocore-tornado:

.. code-block:: python

    from tornado.ioloop import IOLoop
    from tornado import gen
    import botocore_tornado.session

    @gen.coroutine
    def main_async():
        session = botocore_tornado.session.get_session()
        s3 = session.get_service('s3')
        endpoint = s3.get_endpoint(region)

        fp = open('./testfile.txt', 'rb')
        operation = s3.get_operation('PutObject')
        http_response, response_data = yield operation.call(endpoint,
                                                            bucket=bucket,
                                                            key=key + '/' + filename,
                                                            body=fp)
        print response_data

    IOLoop.instance().run_sync(main_async)
