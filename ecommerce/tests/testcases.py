from django.core.cache import cache
from django.test import (
    TestCase as DjangoTestCase,
    LiveServerTestCase as DjangoLiveServerTestCase,
    TransactionTestCase as DjangoTransactionTestCase
)

from ecommerce.tests.mixins import SiteMixin, UserMixin, TestServerUrlMixin


class CacheMixin(object):
    def setUp(self):
        cache.clear()
        super(CacheMixin, self).setUp()

    def tearDown(self):
        cache.clear()
        super(CacheMixin, self).tearDown()


class TestCase(TestServerUrlMixin, UserMixin, SiteMixin, CacheMixin, DjangoTestCase):
    """
    Base test case for ecommerce tests.

    This class guarantees that tests have a Site and Partner available.
    """
    pass


class LiveServerTestCase(TestServerUrlMixin, UserMixin, SiteMixin, CacheMixin, DjangoLiveServerTestCase):
    """
    Base test case for ecommerce tests.

    This class guarantees that tests have a Site and Partner available.
    """
    pass


class TransactionTestCase(TestServerUrlMixin, UserMixin, SiteMixin, CacheMixin, DjangoTransactionTestCase):
    """
    Base test case for ecommerce tests.

    This class guarantees that tests have a Site and Partner available.
    """
    pass
