"""Fail-closed E2E test-build profile for App Factory.

Does not change the app-build-manifest schema. Extra dart-defines and CLI
flags are enough: channels remain dev | pilot | production.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app_factory.application.demo_api_origins import DEMO_API_HOST, PRODUCTION_API_HOST
from app_factory.domain.errors import ManifestValidationError

ALLOWED_E2E_ENVIRONMENTS = frozenset({"demo"})
ALLOWED_E2E_API_HOSTS = frozenset({DEMO_API_HOST})


class E2eTestBuildError(ManifestValidationError):
    """Raised when an E2E test build would target an unsafe origin or env."""


def hostname_of(url: str) -> str:
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").lower()
    if host:
        return host
    candidate = (url or "").strip().lower().split("/")[0]
    if ":" in candidate and not candidate.startswith("["):
        return candidate.split(":", 1)[0]
    return candidate


def is_production_api_host(host: str) -> bool:
    normalized = (host or "").lower().strip()
    if not normalized or normalized == DEMO_API_HOST:
        return False
    if normalized == PRODUCTION_API_HOST:
        return True
    return normalized.endswith("." + PRODUCTION_API_HOST)


def e2e_dart_defines(
    *,
    environment: str,
    run_id: str = "",
    log_path: str = "",
    actor_id: str = "",
) -> dict[str, str]:
    defines = {
        "E2E_TEST_BUILD": "true",
        "BF_E2E_ENVIRONMENT": environment.strip().lower(),
    }
    if run_id.strip():
        defines["BF_E2E_RUN_ID"] = run_id.strip()
    if log_path.strip():
        defines["BF_E2E_LOG_PATH"] = log_path.strip()
    if actor_id.strip():
        defines["BF_E2E_ACTOR_ID"] = actor_id.strip()
    return defines


def assert_e2e_test_build_safe(
    *,
    api_base_url: str,
    environment: str,
    public_app_id: str,
) -> None:
    env = (environment or "").strip().lower()
    if not env:
        raise E2eTestBuildError("E2E_TEST_BUILD requires --e2e-environment=demo.")
    if env not in ALLOWED_E2E_ENVIRONMENTS:
        raise E2eTestBuildError(f"unknown E2E environment {env!r} — abort.")
    if not (public_app_id or "").strip():
        raise E2eTestBuildError("E2E_TEST_BUILD requires tenant.public_app_id.")
    host = hostname_of(api_base_url)
    if is_production_api_host(host):
        raise E2eTestBuildError(
            f"E2E_TEST_BUILD must not target production API host {host!r}."
        )
    if host not in ALLOWED_E2E_API_HOSTS:
        raise E2eTestBuildError(
            f"E2E_TEST_BUILD API host {host!r} is not allowlisted as demo "
            f"({sorted(ALLOWED_E2E_API_HOSTS)})."
        )
