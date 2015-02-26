import botocore.endpoint
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


class AsyncEndpoint(botocore.endpoint.Endpoint):
    """Subclass of Endpoint that uses AsyncHTTPClient to make requests.
    The make_request method is wrapped in a coroutine"""

    def __init__(self, *args, **kwargs):
        super(AsyncEndpoint, self).__init__(*args, **kwargs)
        self.http_client = AsyncHTTPClient()

    @gen.coroutine
    def _send_request(self, request_dict, operation_model):
        request = self.create_request(request_dict, operation_model)
        body = request.body
        # handle the case when body is a file-like object. HTTPRequest expects
        # it to be a string, so we just read all of it here.
        if body is not None and hasattr(body, 'read'):
            body = body.read()
        # for some reason, the default transport (httplib) defaults to sending
        # an empty string as the body, instead of nothing, so here we check
        # if this is a PUT method and default the body to the empty string
        elif body is None and request.method == 'PUT':
            body = ''
        http_request = HTTPRequest(
            url=request.url, headers=request.headers,
            method=request.method, body=body)
        http_response = yield self.http_client.fetch(http_request)
        protocol = operation_model.metadata['protocol']
        response_dict = {
            'headers': http_response.headers,
            'status_code': http_response.code,
        }
        if response_dict['status_code'] >= 300:
            response_dict['body'] = http_response.body
        elif operation_model.has_streaming_output:
            response_dict['body'] = botocore.response.StreamingBody(
                http_response.body, response_dict['headers'].get('content-length'))
        else:
            response_dict['body'] = http_response.body
        parser = botocore.parsers.create_parser(protocol)
        parsed = parser.parse(
            response_dict, operation_model.output_shape)
        raise gen.Return((http_response, parsed))


class EndpointCreator(botocore.endpoint.EndpointCreator):
    def _get_endpoint(self, service_model, region_name, endpoint_url,
                      verify, response_parser_factory):
        """Copied from botocore.endpoint.EndpointCreator._get_endpoint
        so that the custom get_endpoint_complex can be used"""
        service_name = service_model.signing_name
        endpoint_prefix = service_model.endpoint_prefix
        user_agent = self._user_agent
        event_emitter = self._event_emitter
        user_agent = self._user_agent
        return get_endpoint_complex(service_name, endpoint_prefix,
                                    region_name, endpoint_url,
                                    verify, user_agent, event_emitter,
                                    response_parser_factory)


def get_endpoint(service, region_name, endpoint_url, verify=None):
    """Copied from botocore.endpoint.get_endpoint so that the custom
    get_endpoint_complex can be used"""
    service_name = getattr(service, 'signing_name', service.endpoint_prefix)
    endpoint_prefix = service.endpoint_prefix
    session = service.session
    event_emitter = session.get_component('event_emitter')
    user_agent = session.user_agent()
    return get_endpoint_complex(service_name, endpoint_prefix,
                                region_name, endpoint_url, verify, user_agent,
                                event_emitter)



def get_endpoint_complex(service_name, endpoint_prefix,
                         region_name, endpoint_url, verify,
                         user_agent, event_emitter,
                         response_parser_factory=None):
    """Copied from botocore.endpoint.get_endpoint_complex so that the
    AsyncEndpoint can be returned"""
    proxies = botocore.endpoint._get_proxies(endpoint_url)
    verify = botocore.endpoint._get_verify_value(verify)
    return AsyncEndpoint(
        region_name, endpoint_url,
        user_agent=user_agent,
        endpoint_prefix=endpoint_prefix,
        event_emitter=event_emitter,
        proxies=proxies,
        verify=verify,
        response_parser_factory=response_parser_factory)
