"""
Configuration management for Centre AI MCP Server
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import secrets


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration"""
    host: str = "postgres"
    port: int = 5432
    database: str = "centre_ai"
    user: str = "centre_ai"
    password: str = "centre_ai_password"

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration"""
    host: str = "qdrant"
    port: int = 6333
    api_key: Optional[str] = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class RedisConfig:
    """Redis configuration for sessions and caching"""
    host: str = "redis"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_hex(32)))
    mcp_auth_token: str = field(default_factory=lambda: os.getenv("MCP_AUTH_TOKEN", secrets.token_hex(32)))
    admin_username: str = "admin"
    admin_password: str = "changeme"
    jwt_expiry_hours: int = 24
    claude_oauth_client_id: str = field(default_factory=lambda: os.getenv("CLAUDE_OAUTH_CLIENT_ID", "claude_centre_ai"))
    claude_oauth_client_secret: str = field(default_factory=lambda: os.getenv("CLAUDE_OAUTH_CLIENT_SECRET", secrets.token_hex(32)))
    allowed_origins: list = field(default_factory=lambda: [
        "https://claude.ai",
        "https://*.claude.ai",
        "https://claude.com",
        "https://*.claude.com",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "*"
    ])


@dataclass
class ServerConfig:
    """Server configuration"""
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 2068
    admin_host: str = "0.0.0.0"
    admin_port: int = 2069
    debug: bool = False
    log_level: str = "INFO"
    api_domain: str = "localhost"
    mcp_domain: str = "localhost"
    admin_domain: str = "localhost"
    https_domains: list = field(default_factory=list)


@dataclass
class Config:
    """Main configuration class"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    data_dir: Path = Path("/app/data")
    git_repos_dir: Path = Path("/app/git_repos")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config = cls()

        # Database
        config.database.host = os.getenv("POSTGRES_HOST", config.database.host)
        config.database.port = int(os.getenv("POSTGRES_PORT", config.database.port))
        config.database.database = os.getenv("POSTGRES_DB", config.database.database)
        config.database.user = os.getenv("POSTGRES_USER", config.database.user)
        config.database.password = os.getenv("POSTGRES_PASSWORD", config.database.password)

        # Qdrant
        config.qdrant.host = os.getenv("QDRANT_HOST", config.qdrant.host)
        config.qdrant.port = int(os.getenv("QDRANT_PORT", config.qdrant.port))
        config.qdrant.api_key = os.getenv("QDRANT_API_KEY")

        # Redis
        config.redis.host = os.getenv("REDIS_HOST", config.redis.host)
        config.redis.port = int(os.getenv("REDIS_PORT", config.redis.port))
        config.redis.password = os.getenv("REDIS_PASSWORD")

        # Security
        config.security.secret_key = os.getenv("SECRET_KEY", config.security.secret_key)
        config.security.mcp_auth_token = os.getenv("MCP_AUTH_TOKEN", config.security.mcp_auth_token)
        config.security.admin_username = os.getenv("ADMIN_USERNAME", config.security.admin_username)
        config.security.admin_password = os.getenv("ADMIN_PASSWORD", config.security.admin_password)

        # Server
        config.server.mcp_port = int(os.getenv("MCP_PORT", config.server.mcp_port))
        config.server.admin_port = int(os.getenv("ADMIN_PORT", config.server.admin_port))
        config.server.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.server.log_level = os.getenv("LOG_LEVEL", config.server.log_level)

        # Domain configuration
        config.server.api_domain = os.getenv("API_DOMAIN", config.server.api_domain)
        config.server.mcp_domain = os.getenv("MCP_DOMAIN", config.server.mcp_domain)
        config.server.admin_domain = os.getenv("ADMIN_DOMAIN", config.server.admin_domain)
        https_domains = os.getenv("HTTPS_DOMAINS", "")
        config.server.https_domains = [d.strip() for d in https_domains.split(",") if d.strip()]

        # Paths
        config.data_dir = Path(os.getenv("DATA_DIR", config.data_dir))
        config.git_repos_dir = Path(os.getenv("GIT_REPOS_DIR", config.git_repos_dir))

        return config

    def get_api_base_url(self) -> str:
        """Get the API base URL for OAuth endpoints"""
        use_https = any(self.server.api_domain.endswith(https_domain) for https_domain in self.server.https_domains)
        protocol = "https" if use_https else "http"
        # Include port for non-standard ports
        if self.server.mcp_port not in [80, 443]:
            return f"{protocol}://{self.server.api_domain}:{self.server.mcp_port}"
        return f"{protocol}://{self.server.api_domain}"

    def get_mcp_base_url(self) -> str:
        """Get the MCP base URL for SSE/WebSocket endpoints"""
        use_https = any(self.server.mcp_domain.endswith(https_domain) for https_domain in self.server.https_domains)
        protocol = "https" if use_https else "http"
        return f"{protocol}://{self.server.mcp_domain}"

    def get_admin_base_url(self) -> str:
        """Get the Admin base URL for management interface"""
        use_https = any(self.server.admin_domain.endswith(https_domain) for https_domain in self.server.https_domains)
        protocol = "https" if use_https else "http"
        return f"{protocol}://{self.server.admin_domain}"


# Global configuration instance
config = Config.from_env()
