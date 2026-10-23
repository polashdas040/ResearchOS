from packages.core.researchos_core.deployment import DeploymentConfig, DeploymentValidator


def test_production_deployment_requires_externalized_secrets_and_backups() -> None:
    config = DeploymentConfig(
        environment="production",
        database_url="postgresql://db/researchos",
        secret_key="${RESEARCHOS_SECRET_KEY}",
        object_storage_bucket="researchos",
        object_storage_lifecycle_enabled=True,
        backup_enabled=True,
        migration_strategy="expand-contract",
        health_probe_path="/ready",
    )

    assert DeploymentValidator.validate(config) == []


def test_deployment_validator_reports_production_gaps() -> None:
    config = DeploymentConfig(
        environment="production",
        database_url="postgresql://db/researchos",
        secret_key="hard-coded-secret",
        object_storage_bucket="researchos",
        object_storage_lifecycle_enabled=False,
        backup_enabled=False,
        migration_strategy="manual",
        health_probe_path="/health",
    )

    issues = DeploymentValidator.validate(config)

    assert any("secret" in issue.lower() for issue in issues)
    assert any("backup" in issue.lower() for issue in issues)
    assert any("lifecycle" in issue.lower() for issue in issues)
    assert any("migration" in issue.lower() for issue in issues)


def test_development_deployment_can_use_local_defaults() -> None:
    config = DeploymentConfig(
        environment="development",
        database_url="sqlite://",
        secret_key="local-secret",
        object_storage_bucket="local",
        object_storage_lifecycle_enabled=False,
        backup_enabled=False,
        migration_strategy="local",
        health_probe_path="/health",
    )

    assert DeploymentValidator.validate(config) == []
