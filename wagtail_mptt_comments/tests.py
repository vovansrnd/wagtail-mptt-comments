from django.test import RequestFactory, SimpleTestCase, override_settings

from .views import _client_ip


class ClientIPResolutionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(COMMENTS_TRUST_PROXY_HEADERS=True, COMMENTS_TRUSTED_PROXY_IPS=())
    def test_ignores_forwarded_header_without_proxy_allowlist(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="203.0.113.10",
            HTTP_X_FORWARDED_FOR="198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "203.0.113.10")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_walks_forwarded_chain_from_right_and_skips_trusted_proxies(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.8",
            HTTP_X_FORWARDED_FOR="198.51.100.44, 10.0.0.7",
        )
        self.assertEqual(_client_ip(request), "198.51.100.44")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_ignores_header_from_untrusted_remote_peer(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="203.0.113.10",
            HTTP_X_FORWARDED_FOR="198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "203.0.113.10")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_malformed_forwarded_chain_falls_back_to_remote_addr(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.8",
            HTTP_X_FORWARDED_FOR="not-an-ip, 198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "10.0.0.8")
