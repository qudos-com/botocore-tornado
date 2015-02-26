import logging

import botocore.service

from .endpoint import EndpointCreator
from .operation import AsyncOperation

logger = logging.getLogger(__name__)


class AsyncService(botocore.service.Service):

    def _create_operation_objects(self):
        logger.debug("Creating operation objects for: %s", self)
        operations = []
        for operation_name in self._operations_data:
            data = self._operations_data[operation_name]
            data['name'] = operation_name
            model = self._model.operation_model(operation_name)
            op = AsyncOperation(self, data, model)
            operations.append(op)
        return operations

    def get_endpoint(self, region_name=None, is_secure=True,
                     endpoint_url=None, verify=None):
        """
        Return the Endpoint object for this service in a particular
        region.

        :type region_name: str
        :param region_name: The name of the region.

        :type is_secure: bool
        :param is_secure: True if you want the secure (HTTPS) endpoint.

        :type endpoint_url: str
        :param endpoint_url: You can explicitly override the default
            computed endpoint name with this parameter.  If this arg is
            provided then neither ``region_name`` nor ``is_secure``
            is used in building the final ``endpoint_url``.
            ``region_name`` can still be useful for services that require
            a region name independent of the endpoint_url (for example services
            that use Signature Version 4, which require a region name for
            use in the signature calculation).

        """
        resolver = self.session.get_component('endpoint_resolver')
        region = self.session.get_config_variable('region')
        event_emitter = self.session.get_component('event_emitter')
        response_parser_factory = self.session.get_component(
            'response_parser_factory')
        user_agent= self.session.user_agent()
        endpoint_creator = EndpointCreator(resolver, region, event_emitter,
                                           user_agent)
        kwargs = {'service_model': self._model, 'region_name': region_name,
                  'is_secure': is_secure, 'endpoint_url': endpoint_url,
                  'verify': verify,
                  'response_parser_factory': response_parser_factory}
        if self._has_custom_signature_version:
            kwargs['signature_version'] = self.signature_version

        return endpoint_creator.create_endpoint(**kwargs)


def get_service(session, service_name, provider, api_version=None):
    """
    Return a Service object for a given provider name and service name.

    :type service_name: str
    :param service_name: The name of the service.

    :type provider: Provider
    :param provider: The Provider object associated with the session.
    """
    logger.debug("Creating service object for: %s", service_name)
    return AsyncService(session, provider, service_name)
