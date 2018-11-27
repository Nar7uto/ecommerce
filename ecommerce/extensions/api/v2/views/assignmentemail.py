"""API endpoint for sending assignment email to a user."""
import logging

from ecommerce_worker.sailthru.v1.tasks import send_code_assignment_email
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.extensions.api.exceptions import BadRequestException

logger = logging.getLogger(__name__)


class AssignmentEmail(APIView):
    """Sends assignment email to a user."""
    permission_classes = (IsAuthenticated,)

    REQUIRED_PARAM_EMAIL = 'user_email'
    REQUIRED_PARAM_ENTERPRISE_NAME = 'enterprise_name'
    REQUIRED_PARAM_CODE = 'code'
    REQUIRED_PARAM_ENROLLMENT_URL = 'enrollment_url'
    REQUIRED_PARAM_CODE_USAGE_COUNT = 'code_usage_count'
    REQUIRED_PARAM_CODE_EXPIRATION_DATE = 'code_expiration_date'

    MISSING_REQUIRED_PARAMS_MSG = "Some required parameter(s) missing: {}"

    def get_request_value(self, request, key, default=None):
        """
        Get the value in the request, either through query parameters or posted data, from a key.
        """
        return request.data.get(key, request.query_params.get(key, default))

    def get_required_query_params(self, request):
        """
        Gets ``user_email``, ``enterprise_name``, ``enrollment_url``, ``code``,
        ``code_usage_count`` and ``code_expiration_date``
        which are the relevant parameters for this API endpoint.

        :param request: The request to this endpoint.
        :return: The ``user_email``, ``enterprise_name``, ``enrollment_url``, ``code``
        ``code_usage_count`` and ``code_expiration_date`` from the request.
        """
        user_email = self.get_request_value(request, self.REQUIRED_PARAM_EMAIL)
        enterprise_name = self.get_request_value(request, self.REQUIRED_PARAM_ENTERPRISE_NAME)
        code = self.get_request_value(request, self.REQUIRED_PARAM_CODE, '')
        enrollment_url = self.get_request_value(request, self.REQUIRED_PARAM_ENROLLMENT_URL)
        code_usage_count = self.get_request_value(request, self.REQUIRED_PARAM_CODE_USAGE_COUNT)
        code_expiration_date = self.get_request_value(request, self.REQUIRED_PARAM_CODE_EXPIRATION_DATE)
        if not (user_email
                and enterprise_name
                and code
                and enrollment_url
                and code_usage_count
                and code_expiration_date
                ):
            raise BadRequestException(
                self.get_missing_params_message([
                    (self.REQUIRED_PARAM_EMAIL, bool(user_email)),
                    (self.REQUIRED_PARAM_ENTERPRISE_NAME, bool(enterprise_name)),
                    (self.REQUIRED_PARAM_CODE, bool(code)),
                    (self.REQUIRED_PARAM_ENROLLMENT_URL, bool(enrollment_url)),
                    (self.REQUIRED_PARAM_CODE_USAGE_COUNT, bool(code_usage_count)),
                    (self.REQUIRED_PARAM_CODE_EXPIRATION_DATE, bool(code_expiration_date)),
                ])
            )
        return user_email, enterprise_name, code, enrollment_url, code_usage_count, code_expiration_date

    def get_missing_params_message(self, parameter_state):
        """
        Get a user-friendly message indicating a missing parameter for the API endpoint.
        """
        params = ', '.join(name for name, present in parameter_state if not present)
        return self.MISSING_REQUIRED_PARAMS_MSG.format(params)

    def post(self, request):
        """
        POST /enterprise/api/v1/request_codes

        Requires a JSON object of the following format:
        >>> {
        >>>     "user_email": "bob@alice.com",
        >>>     "enterprise_name": "IBM",
        >>>     "code": "GIL7RUEOU7VHBH7Q",
        >>>     "enrollment_url": "http://tempurl.url/enroll"
        >>>     "code_usage_count": "3"
        >>>     "code_expiration_date": "2012-04-23T18:25:43.511Z"
        >>> }

        Keys:
        *user_email*
            Email of the customer who has requested more codes.
        *enterprise_name*
            The name of the enterprise requesting more codes.
        *code*
            Code for the user.
        *enrollment_url*
            URL for the user.
        *code_usage_count*
            Number of times the code can be redeemed.
        *code_expiration_date*
            Date till code is valid.
        """
        logger.info("%s", request.data)
        try:
            user_email,\
            enterprise_name,\
            code,\
            enrollment_url,\
            code_usage_count,\
            code_expiration_date = self.get_required_query_params(request)
        except BadRequestException as invalid_request:
            return Response({'error': str(invalid_request)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_code_assignment_email.delay(user_email, enterprise_name, code, enrollment_url, code_usage_count,
                                             code_expiration_date)
            return Response({'success': str('Email scheduled')}, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception('Sending task raised: %r', exc)
            return Response(
                {'error': str('Assignment code email could not be sent')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
