from pydantic import BaseModel, ConfigDict, Field


class DeploymentConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    environment: str = Field(min_length=1)
    database_url: str = Field(min_length=1)
    secret_key: str = Field(min_length=1)
    object_storage_bucket: str = Field(min_length=1)
    object_storage_lifecycle_enabled: bool
    backup_enabled: bool
    migration_strategy: str = Field(min_length=1)
    health_probe_path: str = Field(min_length=1)


class DeploymentValidator:
    @staticmethod
    def validate(config: DeploymentConfig) -> list[str]:
        if config.environment != "production":
            return []
        issues: list[str] = []
        if not config.secret_key.startswith("${"):
            issues.append("Production secret must be externalized through an environment variable.")
        if not config.backup_enabled:
            issues.append("Production database backups must be enabled.")
        if not config.object_storage_lifecycle_enabled:
            issues.append("Production object storage lifecycle policy must be enabled.")
        if config.migration_strategy not in {"expand-contract", "rolling"}:
            issues.append("Production migration strategy must support rolling compatibility.")
        if config.health_probe_path != "/ready":
            issues.append("Production health probe must verify dependency readiness at /ready.")
        return issues
