import logging

import botocore.operation
from botocore.signers import RequestSigner
from tornado import gen

logger = logging.getLogger(__name__)


class AsyncOperation(botocore.operation.Operation):

    @gen.coroutine
    def call(self, endpoint, **kwargs):
        from .endpoint import AsyncEndpoint
        assert isinstance(endpoint, AsyncEndpoint)
        # from here on is copied from botocore.operation.Operation.call, with
        # the yield added on endpoint.make_request, and the response returned
        # through raising a gen.Return
        logger.debug("%s called with kwargs: %s", self, kwargs)
        # It probably seems a little weird to be firing two different
        # events here.  The reason is that the first event is fired
        # with the parameters exactly as supplied.  The second event
        # is fired with the built parameters.  Generally, it's easier
        # to manipulate the former but at times, like with ReST operations
        # that build an XML or JSON payload, you have to wait for
        # build_parameters to do it's job and the latter is necessary.
        event = self.session.create_event('before-parameter-build',
                                          self.service.endpoint_prefix,
                                          self.name)
        self.session.emit(event, endpoint=endpoint,
                          model=self.model,
                          params=kwargs)
        request_dict = self.build_parameters(**kwargs)

        service_name = self.service.service_name
        service_model = self.session.get_service_model(service_name)

        signature_version, region_name = \
            self._get_signature_version_and_region(
                endpoint, service_model)

        credentials = self.session.get_credentials()
        event_emitter = self.session.get_component('event_emitter')
        signer = RequestSigner(service_model.service_name,
                               region_name, service_model.signing_name,
                               signature_version, credentials,
                               event_emitter)

        event = self.session.create_event('before-call',
                                          self.service.endpoint_prefix,
                                          self.name)
        # The operation kwargs is being passed in kwargs to support
        # handlers that still depend on this value.  Eventually
        # everything should move over to the model/endpoint args.
        self.session.emit(event, endpoint=endpoint,
                          model=self.model,
                          params=request_dict,
                          operation=self,
                          request_signer=signer)

        # Here we register to the specific request-created event
        # for this operation. Since it's possible to run the same
        # operation in multiple threads, we used a lock to prevent
        # issues. It's possible a request will be signed more than
        # once. Once the request has been made, we unregister the
        # handler.
        def request_created(request, **kwargs):
            # This first check lets us quickly determine when
            # a request has already been signed without needing
            # to acquire the lock.
            if not getattr(request, '_is_signed', False):
                with self._lock:
                    if not getattr(request, '_is_signed', False):
                        signer.sign(self.name, request)
                        request._is_signed = True

        event_emitter.register('request-created.{0}.{1}'.format(
            self.service.endpoint_prefix, self.name), request_created)

        try:
            response = yield endpoint.make_request(self.model, request_dict)
        finally:
            event_emitter.unregister('request-created.{0}.{1}'.format(
                self.service.endpoint_prefix, self.name), request_created)

        event = self.session.create_event('after-call',
                                          self.service.endpoint_prefix,
                                          self.name)
        self.session.emit(event,
                          http_response=response[0],
                          model=self.model,
                          operation=self,
                          parsed=response[1])
        raise gen.Return(response)
