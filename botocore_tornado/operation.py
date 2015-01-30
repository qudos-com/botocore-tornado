import logging

import botocore.operation
from tornado import gen

logger = logging.getLogger(__name__)


class AsyncOperation(botocore.operation.Operation):

    @gen.coroutine
    def call(self, endpoint, **kwargs):
        from .endpoint import AsyncEndpoint
        assert isinstance(endpoint, AsyncEndpoint)
        # copied from botocore.operation.Operation.call
        logger.debug("%s called with kwargs: %s", self, kwargs)
        event = self.session.create_event('before-parameter-build',
                                          self.service.endpoint_prefix,
                                          self.name)
        self.session.emit(event, endpoint=endpoint,
                          model=self.model,
                          params=kwargs)
        request_dict = self.build_parameters(**kwargs)
        event = self.session.create_event('before-call',
                                          self.service.endpoint_prefix,
                                          self.name)
        # The operation kwargs is being passed in kwargs to support
        # handlers that still depend on this value.  Eventually
        # everything should move over to the model/endpoint args.
        self.session.emit(event, endpoint=endpoint,
                          model=self.model,
                          params=request_dict,
                          operation=self)

        response = yield endpoint.make_request(self.model, request_dict)

        event = self.session.create_event('after-call',
                                          self.service.endpoint_prefix,
                                          self.name)
        self.session.emit(event,
                          http_response=response[0],
                          model=self.model,
                          operation=self,
                          parsed=response[1])
        raise gen.Return(response)
