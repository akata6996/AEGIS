from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='AEGIS_')

    env: str = 'development'
    db_path: str = './data/aegis.db'

    mqtt_host: str = '127.0.0.1'
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic_template: str = 'aegis/nodes/+/telemetry'
    mqtt_qos: int = Field(default=1, ge=0, le=2)

    max_ingest_delay_ms: int = 5000
    max_clock_skew_ms: int = 1000
    merkle_interval_seconds: int = 600

    solana_devnet_rpc: str = 'https://api.devnet.solana.com'
    solana_commitment: str = 'confirmed'
    solana_anchor_wallet_secret: str | None = None
    solana_anchor_mock_mode: bool = True
    anchor_retry_limit: int = 5

    api_host: str = '0.0.0.0'
    api_port: int = 8000


settings = Settings()
