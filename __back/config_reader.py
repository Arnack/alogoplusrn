from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from typing import Optional


class Settings(BaseSettings):
    # Telegram Bot настройки
    bot_token: Optional[SecretStr] = None
    bot_admins: list[int] = Field(default_factory=list)

    # Max Bot настройки
    max_bot_token: Optional[SecretStr] = None

    # API токены
    main_rr_token: Optional[SecretStr] = None
    mobile_api_token: Optional[SecretStr] = None  # Bearer токен для mobile.handswork.pro

    # SMS API
    sms_api_login: Optional[SecretStr] = None
    sms_api_password: Optional[SecretStr] = None

    # PostgreSQL (обязательные - используются обоими ботами)
    postgresql_db_user: SecretStr
    postgresql_db_password: SecretStr
    postgresql_db_host: SecretStr
    postgresql_db_port: SecretStr
    postgresql_db_name: SecretStr

    # Redis
    redis_host: Optional[SecretStr] = None
    redis_port: Optional[SecretStr] = None
    redis_db: Optional[SecretStr] = None

    # SMTP
    smtp_host: Optional[SecretStr] = None
    smtp_port: Optional[SecretStr] = None
    smtp_email: Optional[SecretStr] = None
    smtp_password: Optional[SecretStr] = None

    # Zvonok API
    zvonok_api_key: Optional[SecretStr] = None
    zvonok_campaign_id_day: Optional[SecretStr] = None
    zvonok_campaign_id_night: Optional[SecretStr] = None

    # Web API + Telegram Web App (панель исполнителя)
    web_app_public_url: Optional[str] = None  # HTTPS URL фронта для WebApp и кнопки в боте
    web_jwt_secret: Optional[SecretStr] = None  # секрет подписи JWT для сессий веба
    web_jwt_expire_minutes: int = 10080  # 7 суток
    web_api_cors_origins: str = '*'  # через запятую или *
    web_auth_max_attempts_per_hour: int = 15  # логин телефон+ИНН с одного номера
    web_telegram_init_data_max_age_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


config = Settings()
