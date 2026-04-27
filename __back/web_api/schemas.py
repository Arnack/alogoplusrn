from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int


class TelegramWebAppAuthBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    init_data: str = Field(
        ...,
        alias='initData',
        description='Сырая строка initData из Telegram.WebApp',
    )


class AuthBootstrapResponse(BaseModel):
    authenticated: bool
    requires_phone_auth: bool
    access_token: str | None = None
    token_type: str = 'bearer'
    expires_in: int | None = None
    reason: str | None = None


class CheckUserBody(BaseModel):
    city: str = Field(..., min_length=1, max_length=64)
    phone: str = Field(..., min_length=10, max_length=32)


class CheckUserResponse(BaseModel):
    exists: bool


class LoginPhoneBody(BaseModel):
    city: str = Field(..., min_length=1, max_length=64)
    phone: str = Field(..., min_length=10, max_length=32)
    inn_last4: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class MenuItem(BaseModel):
    id: str
    title: str


class PanelMenuResponse(BaseModel):
    role: Literal['worker', 'foreman', 'supervisor']
    items: list[MenuItem]


class CityOut(BaseModel):
    id: int
    name: str


class UserPublic(BaseModel):
    id: int
    tg_id: int
    city: str
    phone_number: str
    first_name: str
    last_name: str
    middle_name: str
    inn_masked: str
    block: bool
    in_rr: bool


class AboutPanelOut(BaseModel):
    """Поля как в txt.about_worker + флаги для кнопок (как keyboards/inline/user/about_worker)."""

    phone_registry: str
    fio_registry: str
    phone_actual: str
    fio_actual: str
    card: str | None
    balance: str
    city: str
    rating: str
    total_orders: int
    successful_orders: int
    in_rr: bool
    api_worker_id: int | None = None


class WorkerRulesOut(BaseModel):
    text: str
    date: str
    formatted_html: str


class ReferralPackOut(BaseModel):
    link: str
    bonus: str
    shifts: int
    friends: int
    completed: int
    message_html: str


class ErasePersonalDataBody(BaseModel):
    confirm: bool = True


class CreateWalletPaymentBody(BaseModel):
    amount: str = Field(..., min_length=1, max_length=20)


class SecurityDataUpdateBody(BaseModel):
    """Данные для охраны (тот же сценарий, что и в мессенджере)."""

    phone: str = Field(..., min_length=10, max_length=32)
    last_name: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=20)
    middle_name: str = Field(..., min_length=1, max_length=20)


class ChangeCityBody(BaseModel):
    city_id: int = Field(..., ge=1)


class BankCardUpdateBody(BaseModel):
    """Смена карты: номер и подтверждение последними 4 цифрами ИНН."""

    card: str = Field(..., min_length=12, max_length=24)
    inn_last4: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class EnsureContractsBody(BaseModel):
    """Подписание договоров: подтверждение PIN-кодом (случайный тип)."""

    pin_type: str = Field(..., pattern=r'^(inn|bday|byear|pass)$')
    pin_value: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class OrderSearchItem(BaseModel):
    id: int
    job_name: str
    date: str
    city: str
    customer_id: int
    day_shift: Optional[str] = None
    night_shift: Optional[str] = None
    amount_base: str
    amount_with_rating: str
    job_fp: Optional[str] = Field(
        None,
        description='Текст ТЗ для исполнителя (как в Telegram: get_job_fp_for_txt).',
    )
    travel_compensation_rub: Optional[int] = Field(
        None,
        description='Компенсация Платформы за проезд для получателя услуг (🚌), если задана.',
    )


class CustomerSearchItem(BaseModel):
    customer_id: int
    organization: str
    orders_available: int


class ApplyPreviewOut(BaseModel):
    """HTML текста подтверждения отклика на заявку (веб-панель)."""

    message_html: str
    order_summary_html: str = Field(
        default='',
        description='Карточка заявки перед условиями (как в Telegram); для отклика за друга пусто — сводка внутри message_html.',
    )


class ApplicationItem(BaseModel):
    order_id: int
    kind: Literal['application', 'assigned']
    application_id: Optional[int] = None
    order_worker_id: Optional[int] = None
    job_name: str
    date: str
    city: str
    customer_id: int
    organization: Optional[str] = None
    day_shift: Optional[str] = None
    night_shift: Optional[str] = None
    amount_adjusted: Optional[str] = None
    day_of_week: Optional[str] = None
    added_by_manager: Optional[bool] = None


class NotificationItem(BaseModel):
    id: str
    title: str
    body: str
    created_at: str
    read: bool


class NotificationsResponse(BaseModel):
    items: list[NotificationItem]
    unread_count: int


class HelpInfoResponse(BaseModel):
    text: str
    note: str | None = None
    help_configured: bool = False
    can_send_signal: bool = True
    cooldown_seconds: int | None = None


class OrderForFriendInfoResponse(BaseModel):
    available: bool = True
    message: str = ''
    cities: list[str] = Field(default_factory=list)


class FriendLookupBody(BaseModel):
    phone: str | None = Field(None, min_length=10, max_length=32)
    inn: str | None = Field(None, min_length=10, max_length=12)


class FriendSetCityBody(BaseModel):
    city: str = Field(..., min_length=1, max_length=64)


class FriendVerifyCodeBody(BaseModel):
    code: str = Field(..., min_length=4, max_length=8)


class FriendProgressResponse(BaseModel):
    step: Literal['idle', 'need_city', 'need_code', 'verified']
    message: str = ''
    cities: list[str] = Field(default_factory=list)
    friend_label: str | None = None


class ShoutStatusResponse(BaseModel):
    can_send: bool
    message: str
    order_id: int | None = None
    job_name: str | None = None
    order_date: str | None = None
    city: str | None = None
    workers_on_site: int = 0


class ShoutSendBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=3500)


class ShoutItemOut(BaseModel):
    id: int
    order_id: int
    workers_reached: int
    views: int
    job_name: str
    order_date: str
    city: str


class CoordinatorCityOut(BaseModel):
    name: str


class CoordinatorCustomerOut(BaseModel):
    customer_id: int
    organization: str


class CoordinatorOrderOut(BaseModel):
    id: int
    job_name: str
    date: str
    city: str
    in_progress: bool
    moderation: bool


class NotificationMarkReadBody(BaseModel):
    ids: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    message: str


class ApplyOrderBody(BaseModel):
    order_from_friend: bool = False


# ── Registration ────────────────────────────────────────────


class RegValidateBody(BaseModel):
    inn: str | None = Field(None, min_length=12, max_length=12, pattern=r'^\d{12}$')
    phone: str | None = Field(None, min_length=10, max_length=32)
    card: str | None = Field(None, min_length=12, max_length=24)


class RegValidateResponse(BaseModel):
    inn_ok: bool = True
    phone_ok: bool = True
    card_ok: bool = True
    inn_error: str | None = None
    phone_error: str | None = None
    card_error: str | None = None


class RegSendSmsBody(BaseModel):
    phone: str = Field(..., min_length=10, max_length=32)


class RegSendSmsResponse(BaseModel):
    code_id: str


class RegVerifySmsBody(BaseModel):
    code_id: str
    code: str = Field(..., min_length=4, max_length=8)


class RegVerifySmsResponse(BaseModel):
    ok: bool
    phone: str


class RegSubmitBody(BaseModel):
    city: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: str = Field('', max_length=50)
    birth_date: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{4}$')
    inn: str = Field(..., min_length=12, max_length=12, pattern=r'^\d{12}$')
    card: str = Field(..., min_length=12, max_length=24)
    passport_series: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')
    passport_number: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    passport_date: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{4}$')
    phone: str = Field(..., min_length=10, max_length=32)


class RegSubmitResponse(BaseModel):
    status: str  # 'done' | 'pending'
    api_worker_id: int | None = None
    access_token: str | None = None
    token_type: str = 'bearer'
    expires_in: int | None = None


class RegStatusBody(BaseModel):
    api_worker_id: int
    phone: str = Field(..., min_length=10, max_length=32)
    city: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: str = Field('', max_length=50)
    birth_date: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{4}$')
    inn: str = Field(..., min_length=12, max_length=12, pattern=r'^\d{12}$')
    card: str = Field(..., min_length=12, max_length=24)
    passport_series: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')
    passport_number: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    passport_date: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{4}$')
