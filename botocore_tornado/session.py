import botocore.session
import botocore_tornado.service


class AsyncSession(botocore.session.Session):
    def get_service(self, service_name, api_version=None):
        """
        Get information about a service.

        :type service_name: str
        :param service_name: The name of the service (e.g. 'ec2')

        :returns: :class:`botocore.service.Service`
        """
        service = botocore_tornado.service.get_service(self, service_name,
                                                       self.provider,
                                                       api_version=api_version)
        event = self.create_event('service-created')
        self._events.emit(event, service=service)
        return service


def get_session(env_vars=None):
    return AsyncSession(env_vars)
