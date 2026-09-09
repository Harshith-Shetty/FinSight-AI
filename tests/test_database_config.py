"""Focused tests for database configuration and enum persistence."""

from app.core.config import Settings
from app.models.database import ChatMode, SafeUserRole, TaskStatus, UserRole


def make_settings(**overrides) -> Settings:
    values = {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/finsight",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "SECRET_KEY": "test-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_database_ssl_defaults_to_disabled() -> None:
    config = make_settings()

    assert config.DATABASE_SSL is False
    assert config.DATABASE_URL.startswith("postgresql+asyncpg://")


def test_database_ssl_can_be_enabled_from_environment_style_value() -> None:
    config = make_settings(DATABASE_SSL="true")

    assert config.DATABASE_SSL is True


def test_database_enum_values_match_postgresql_labels() -> None:
    assert [mode.name for mode in ChatMode] == ["HYBRID", "PRIVATE"]
    assert [status.name for status in TaskStatus] == [
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
    ]


def test_safe_user_role_serialization_is_case_insensitive() -> None:
    role_type = SafeUserRole()

    assert role_type.process_bind_param(UserRole.PREMIUM, None) == "PREMIUM"
    assert role_type.process_bind_param("admin", None) == "ADMIN"
    assert role_type.process_result_value("guest", None) is UserRole.GUEST
    assert role_type.process_result_value("UNKNOWN", None) is UserRole.NORMAL
