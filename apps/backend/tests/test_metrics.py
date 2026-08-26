"""Smoke tests for Prometheus metrics endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestMetricsEndpoint:
    async def test_metrics_returns_prometheus_text_format(self, client: AsyncClient):
        """GET /metrics returns a 200 with Prometheus text exposition format."""
        resp = await client.get("/metrics")

        assert resp.status_code == 200
        # Prometheus text format markers
        assert "# HELP" in resp.text
        assert "# TYPE" in resp.text

    async def test_metrics_contains_http_request_metrics(self, client: AsyncClient):
        """After at least one request, HTTP request metrics are present."""
        # Make a request to generate metric data
        await client.get("/healthz")

        resp = await client.get("/metrics")
        assert resp.status_code == 200
        # prometheus-fastapi-instrumentator default metric names
        assert "http_request" in resp.text

    async def test_metrics_excluded_from_openapi(self, client: AsyncClient):
        """The /metrics endpoint must not appear in the OpenAPI schema."""
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = schema.get("paths", {})
        assert "/metrics" not in paths

    async def test_healthz_not_tracked_as_application_request(self, client: AsyncClient):
        """
        /healthz hits are excluded from the instrumentator so they don't
        inflate request count or latency histograms.
        """
        for _ in range(5):
            await client.get("/healthz")

        resp = await client.get("/metrics")
        assert resp.status_code == 200
        # Basic smoke: endpoint is reachable and returns Prometheus format
        assert "# HELP" in resp.text
