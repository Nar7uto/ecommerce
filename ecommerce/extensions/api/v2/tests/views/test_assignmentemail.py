from __future__ import unicode_literals

import ddt
import json
import mock
from django.urls import reverse

from ecommerce.tests.testcases import TestCase


@ddt.ddt
class AssignmentEmailTests(TestCase):
    """ Tests for AssignmentEmail API view. """
    path = reverse('api:v2:assignmentemail')

    def setUp(self):
        super(AssignmentEmailTests, self).setUp()
        self.user = self.create_user()
        self.client.login(username=self.user.username, password=self.password)

        self.data = {
            'user_email': 'GIL7RUEOU7VHBH7Q',
            'enterprise_name': 'DummyEnterprise',
            'code': 'GIL7RUEOU7VHBH7Q',
            'enrollment_url': 'http://tempurl.url/enroll',
            'code_usage_count': '3',
            'code_expiration_date': '2012-04-23T18:25:43.511Z'
        }

    def test_authentication_required(self):
        """ Verify the endpoint requires authentication. """
        self.client.logout()
        response = self.client.post(self.path, data=self.data)
        self.assertEqual(response.status_code, 401)

    @mock.patch('ecommerce_worker.sailthru.v1.tasks.send_code_assignment_email.delay')
    @ddt.data(
        (
            # A valid request.
            {
                'user_email': 'johndoe@unknown.com',
                'enterprise_name': 'fakeOrg',
                'code': 'GIL7RUEOU7VHBH7Q',
                'enrollment_url': 'http://tempurl.url/enroll',
                'code_usage_count': '3',
                'code_expiration_date': '2012-04-23T18:25:43.511Z'
            },
            {u'success': u'Email scheduled'},
            200,
            None,
            True,
            (u'johndoe@unknown.com', u'fakeOrg', u'GIL7RUEOU7VHBH7Q', u'http://tempurl.url/enroll', u'3',
             u'2012-04-23T18:25:43.511Z')
        ),
        (
            # A bad request due to a missing field
            {
                'user_email': 'johndoe@unknown.com',
                'enterprise_name': 'fakeOrg',
                'enrollment_url': 'http://tempurl.url/enroll',
                'code_usage_count': '3',
                'code_expiration_date': '2012-04-23T18:25:43.511Z'
            },
            {u'error': u'Some required parameter(s) missing: code'},
            400,
            None,
            False,
            (u'johndoe@unknown.com', u'fakeOrg', u'GIL7RUEOU7VHBH7P', u'http://tempurl.url/enroll', u'3',
             u'2012-04-23T18:25:43.511Z')
        ),
        (
            # Email task issue
            {
                'user_email': 'johndoe@unknown.com',
                'enterprise_name': 'fakeOrg',
                'code': 'GIL7RUEOU7VHBH7P',
                'enrollment_url': 'http://tempurl.url/enroll',
                'code_usage_count': '3',
                'code_expiration_date': '2012-04-23T18:25:43.511Z'
            },
            {u'error': u'Assignment code email could not be sent'},
            500,
            Exception(),
            True,
            (u'johndoe@unknown.com', u'fakeOrg', u'GIL7RUEOU7VHBH7P', u'http://tempurl.url/enroll', u'3',
             u'2012-04-23T18:25:43.511Z')
        )
    )
    @ddt.unpack
    def test_email_task_success(
            self,
            post_data,
            response_data,
            status_code,
            mock_side_effect,
            mail_attempted,
            args,
            mock_send_code_assignment_email,
    ):
        """ Verify the endpoint schedules async task to send email """
        mock_send_code_assignment_email.side_effect = mock_side_effect
        response = self.client.post(self.path, data=post_data)
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response_data, json.loads(response.content))
        if mail_attempted:
            mock_send_code_assignment_email.assert_called_once_with(*args)
        else:
            mock_send_code_assignment_email.assert_not_called()
