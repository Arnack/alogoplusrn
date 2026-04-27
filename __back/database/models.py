from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from datetime import datetime
from typing import List, Optional

from config_reader import config


engine = create_async_engine(
    url=f"postgresql+asyncpg://"
        f"{config.postgresql_db_user.get_secret_value()}:"
        f"{config.postgresql_db_password.get_secret_value()}@"
        f"{config.postgresql_db_host.get_secret_value()}:"
        f"{config.postgresql_db_port.get_secret_value()}/"
        f"{config.postgresql_db_name.get_secret_value()}"
)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    max_id: Mapped[int] = mapped_column(BigInteger, default=0)  # ID в мессенджере Max
    max_chat_id: Mapped[int] = mapped_column(BigInteger, default=0)  # ID личного диалога Max
    username: Mapped[str] = mapped_column(String(25), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(25))
    city: Mapped[str] = mapped_column(String(25))
    rejections: Mapped[int] = mapped_column(Integer, default=0)
    block: Mapped[bool] = mapped_column(Boolean, default=False)
    call_block: Mapped[bool] = mapped_column(Boolean, default=False)
    call_block_reason: Mapped[str] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(20))
    middle_name: Mapped[str] = mapped_column(String(20))
    last_name: Mapped[str] = mapped_column(String(20))
    inn: Mapped[str] = mapped_column(String(12))
    api_id: Mapped[int] = mapped_column(Integer)
    card: Mapped[str] = mapped_column(String(16))
    last_job: Mapped[int] = mapped_column(Integer, nullable=True)
    balance: Mapped[str] = mapped_column(String(20), default='0')
    passport_data_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    smz_status: Mapped[str] = mapped_column(String(20), nullable=True)  # 'confirmed' / 'pending' / None
    gender: Mapped[str] = mapped_column(String(1), nullable=True)  # 'M' / 'F'
    last_web_ip: Mapped[str] = mapped_column(String(45), nullable=True)  # последний IP web-входа

    security: Mapped["DataForSecurity"] = relationship("DataForSecurity", back_populates="user")
    user_applications: Mapped[List["OrderApplication"]] = relationship("OrderApplication", back_populates="user")
    rating: Mapped["UserRating"] = relationship("UserRating", back_populates="user")
    order_workers: Mapped["OrderWorker"] = relationship("OrderWorker", back_populates="user")
    archive_order_workers: Mapped[List["OrderWorkerArchive"]] = relationship(
        "OrderWorkerArchive", back_populates="user"
    )
    reg: Mapped["UserRegisteredAt"] = relationship("UserRegisteredAt", back_populates="user")
    change_city: Mapped["ChangeCity"] = relationship("ChangeCity", back_populates="user")
    payments: Mapped["Payment"] = relationship("Payment", back_populates="user")
    premium_entries: Mapped[List["PremiumWorker"]] = relationship("PremiumWorker", back_populates="worker")
    debtor_cycles: Mapped[List["DebtorCycle"]] = relationship("DebtorCycle", back_populates="worker")
    help_last_use: Mapped["HelpLastUse"] = relationship("HelpLastUse", back_populates="worker")


class UserRegisteredAt(Base):
    __tablename__ = 'user_registered_at'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    date: Mapped[str] = mapped_column(String(10))

    user: Mapped["User"] = relationship("User", back_populates="reg")


class UserRating(Base):
    __tablename__ = 'user_rating'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    successful_orders: Mapped[int] = mapped_column(Integer, default=0)
    plus: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="rating")


class Verification(Base):
    __tablename__ = 'verifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(Integer)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    max_id: Mapped[int] = mapped_column(BigInteger, default=0)  # Max ID для отправки кода
    code_hash: Mapped[str] = mapped_column(String)
    salt: Mapped[str] = mapped_column(String)


class RegCode(Base):
    __tablename__ = 'reg_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    code_hash: Mapped[str] = mapped_column(String)
    salt: Mapped[str] = mapped_column(String)


class CodeForOrder(Base):
    __tablename__ = 'codes_for_orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    code_hash: Mapped[str] = mapped_column(String)
    salt: Mapped[str] = mapped_column(String)


class CodeDailyAttempts(Base):
    __tablename__ = 'code_daily_attempts'

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(25))
    last_usage = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer)


class OrderForFriendLogging(Base):
    __tablename__ = 'order_for_friend_logging'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    who_signed: Mapped[int] = mapped_column(Integer)
    who_signed_tg_id: Mapped[int] = mapped_column(BigInteger)
    when_signed: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    friend_id: Mapped[int] = mapped_column(Integer)
    friend_tg_id: Mapped[int] = mapped_column(BigInteger)
    order_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    when_deleted: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class DataForSecurity(Base):
    __tablename__ = 'dataForSecurity'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    phone_number: Mapped[str] = mapped_column(String(25))
    first_name: Mapped[str] = mapped_column(String(20))
    last_name: Mapped[str] = mapped_column(String(20))
    middle_name: Mapped[str] = mapped_column(String(20))
    passport_series: Mapped[str] = mapped_column(String(4), nullable=True)
    passport_number: Mapped[str] = mapped_column(String(6), nullable=True)
    passport_issue_date: Mapped[str] = mapped_column(String(10), nullable=True)    # DD.MM.YYYY
    passport_department_code: Mapped[str] = mapped_column(String(7), nullable=True)  # 000-000
    passport_issued_by: Mapped[str] = mapped_column(String(200), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="security")
    wallet_payments: Mapped["WalletPayment"] = relationship("WalletPayment", back_populates="worker")


class City(Base):
    __tablename__ = 'cities'

    id: Mapped[int] = mapped_column(primary_key=True)
    city_name: Mapped[str] = mapped_column(String(25))


class Settings(Base):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    shifts: Mapped[int] = mapped_column(Integer)
    bonus: Mapped[int] = mapped_column(Integer)
    registration_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rr_manual_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    smz_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rr_partner_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    help_group_chat_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


class HelpLastUse(Base):
    __tablename__ = 'help_last_uses'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    last_use: Mapped[datetime] = mapped_column(DateTime)

    worker: Mapped["User"] = relationship("User", back_populates="help_last_use")


class Referral(Base):
    __tablename__ = 'referral'

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(BigInteger)
    referral: Mapped[int] = mapped_column(BigInteger)
    shifts_referral: Mapped[int] = mapped_column(Integer, default=0)
    bonus: Mapped[bool] = mapped_column(Boolean, default=False)


class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(50))
    day_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    night_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    email_addresses: Mapped[str] = mapped_column(Text, nullable=True)
    email_sending_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    travel_compensation: Mapped[int] = mapped_column(Integer, nullable=True, default=None)

    admins: Mapped[List["CustomerAdmin"]] = relationship("CustomerAdmin", back_populates="customer")
    groups: Mapped["CustomerGroup"] = relationship("CustomerGroup", back_populates="customer")
    foremen: Mapped[List["CustomerForeman"]] = relationship("CustomerForeman", back_populates="customer")
    cities: Mapped[List["CustomerCity"]] = relationship("CustomerCity", back_populates="customer")
    jobs: Mapped[List["CustomerJob"]] = relationship("CustomerJob", back_populates="customer")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")
    premium_workers: Mapped[List["PremiumWorker"]] = relationship("PremiumWorker", back_populates="customer")


class PremiumWorker(Base):
    __tablename__ = 'premium_workers'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete='CASCADE'))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    bonus_type: Mapped[str] = mapped_column(String(20))  # 'unconditional' / 'conditional'

    customer: Mapped["Customer"] = relationship("Customer", back_populates="premium_workers")
    worker: Mapped["User"] = relationship("User", back_populates="premium_entries")
    conditions: Mapped[List["PremiumCondition"]] = relationship(
        "PremiumCondition",
        back_populates="premium_worker",
        cascade="all, delete-orphan"
    )


class PremiumCondition(Base):
    __tablename__ = 'premium_conditions'

    id: Mapped[int] = mapped_column(primary_key=True)
    premium_worker_id: Mapped[int] = mapped_column(ForeignKey('premium_workers.id', ondelete='CASCADE'))
    threshold_percent: Mapped[str] = mapped_column(String(10))  # "95,50"
    bonus_amount: Mapped[str] = mapped_column(String(10))       # "500"

    premium_worker: Mapped["PremiumWorker"] = relationship("PremiumWorker", back_populates="conditions")


class CustomerAdmin(Base):
    __tablename__ = 'customer_admins'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    admin_full_name: Mapped[str] = mapped_column(String(50))
    admin: Mapped[int] = mapped_column(BigInteger)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="admins")


class CustomerGroup(Base):
    __tablename__ = 'customer_groups'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    group_name: Mapped[str] = mapped_column(String(50))
    chat_id: Mapped[str] = mapped_column(String(20))

    customer: Mapped["Customer"] = relationship("Customer", back_populates="groups")


class CustomerForeman(Base):
    __tablename__ = 'customer_foremen'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String(60))
    tg_id: Mapped[int] = mapped_column(BigInteger)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="foremen")


class CustomerCity(Base):
    __tablename__ = 'customer_cities'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    city: Mapped[str] = mapped_column(String(25))

    customer: Mapped["Customer"] = relationship("Customer", back_populates="cities")
    city_way: Mapped["CustomerCityWay"] = relationship("CustomerCityWay", back_populates="city")


class CustomerCityWay(Base):
    __tablename__ = 'customer_city_way'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_city_id: Mapped[int] = mapped_column(ForeignKey('customer_cities.id', ondelete="CASCADE"))
    way_to_job: Mapped[str] = mapped_column(Text)

    city: Mapped["CustomerCity"] = relationship("CustomerCity", back_populates="city_way")
    city_photos: Mapped[List["CityWayPhoto"]] = relationship("CityWayPhoto", back_populates="city_way")


class CityWayPhoto(Base):
    __tablename__ = 'city_way_photos'

    id: Mapped[int] = mapped_column(primary_key=True)
    city_way_id: Mapped[int] = mapped_column(ForeignKey('customer_city_way.id', ondelete="CASCADE"))
    photo: Mapped[str] = mapped_column(String)

    city_way: Mapped["CustomerCityWay"] = relationship("CustomerCityWay", back_populates="city_photos")


class CustomerJob(Base):
    __tablename__ = 'customer_jobs'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    job: Mapped[str] = mapped_column(String(25))

    customer: Mapped["Customer"] = relationship("Customer", back_populates="jobs")
    amount: Mapped["CustomerJobAmount"] = relationship("CustomerJobAmount", back_populates="job")


class CustomerJobAmount(Base):
    __tablename__ = 'customer_jobs_amount'

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('customer_jobs.id', ondelete="CASCADE"))
    amount: Mapped[int] = mapped_column(String(25))

    job: Mapped["CustomerJob"] = relationship("CustomerJob", back_populates="amount")


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete="CASCADE"))
    job_name: Mapped[str] = mapped_column(String(20))
    date: Mapped[str] = mapped_column(String(15))
    day_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    night_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    workers: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String(25))
    moderation: Mapped[bool] = mapped_column(Boolean, default=True)
    in_progress: Mapped[bool] = mapped_column(Boolean, default=False)
    manager: Mapped[int] = mapped_column(BigInteger, nullable=True)
    amount: Mapped[str] = mapped_column(String(10), nullable=True)
    work_cycle: Mapped[int] = mapped_column(Integer, default=1)
    rr_order_id: Mapped[int] = mapped_column(Integer, nullable=True)      # ID заявки в CRM РР
    rr_shift_id: Mapped[str] = mapped_column(String(50), nullable=True)   # UUID смены в CRM
    legal_entity_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Какое ИП опубликовало

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    order_workers: Mapped[List["OrderWorker"]] = relationship("OrderWorker", back_populates="order")
    user_applications: Mapped[List["OrderApplication"]] = relationship("OrderApplication", back_populates="order")
    shout_stats: Mapped[List["ShoutStat"]] = relationship("ShoutStat", back_populates="order")


class OrderArchive(Base):
    __tablename__ = 'orders_archive'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete='CASCADE'))
    job_name: Mapped[str] = mapped_column(String(20))
    date: Mapped[str] = mapped_column(String(15))
    day_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    night_shift: Mapped[str] = mapped_column(String(20), nullable=True)
    workers_count: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String(25))
    manager_tg_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[str] = mapped_column(String(10))

    archive_order_workers: Mapped[List["OrderWorkerArchive"]] = relationship(
        "OrderWorkerArchive", back_populates="archive_order"
    )


class OrderWorkerArchive(Base):
    __tablename__ = 'order_workers_archive'

    id: Mapped[int] = mapped_column(primary_key=True)
    archive_order_id: Mapped[int] = mapped_column(ForeignKey('orders_archive.id', ondelete="CASCADE"))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    worker_hours: Mapped[str] = mapped_column(String(5))
    date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), nullable=True, default='WORKED')  # WORKED, NOT_OUT, EXTRA
    compensation_amount: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    is_rr_worker: Mapped[bool] = mapped_column(Boolean, default=False)
    penalty_amount: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    bonus_amount: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    rating_deduction: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    archive_order: Mapped["OrderArchive"] = relationship("OrderArchive", back_populates="archive_order_workers")
    user: Mapped["User"] = relationship("User", back_populates="archive_order_workers")


class OrderApplication(Base):
    __tablename__ = 'order_applications'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete="CASCADE"))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    order_from_friend: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="user_applications")
    order: Mapped["Order"] = relationship("Order", back_populates="user_applications")


class OrderWorker(Base):
    __tablename__ = 'order_workers'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete="CASCADE"))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    added_by_manager: Mapped[bool] = mapped_column(Boolean, default=False)
    order_from_friend: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rr_worker: Mapped[bool] = mapped_column(Boolean, default=False)     # Исполнитель пришёл из РР
    rr_worker_inn: Mapped[str] = mapped_column(String(12), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="order_workers")
    order: Mapped["Order"] = relationship("Order", back_populates="order_workers")


class Manager(Base):
    __tablename__ = 'managers'

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_full_name: Mapped[str] = mapped_column(String(50))
    manager_id: Mapped[int] = mapped_column(BigInteger)


class Accountant(Base):
    __tablename__ = 'accountants'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(50))
    tg_id: Mapped[int] = mapped_column(BigInteger)


class DebtorCycle(Base):
    __tablename__ = 'debtor_cycles'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    status: Mapped[str] = mapped_column(String(10), default='active')
    # 'active' | 'deducted' | 'annulled'
    deducted_amount: Mapped[int] = mapped_column(Integer, nullable=True)
    deduction_date: Mapped[str] = mapped_column(String(10), nullable=True)  # DD.MM.YYYY
    annulled_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    annulled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    worker: Mapped["User"] = relationship("User", back_populates="debtor_cycles")
    no_show_events: Mapped[List["NoShowEvent"]] = relationship(
        "NoShowEvent", back_populates="cycle", cascade="all, delete-orphan"
    )


class NoShowEvent(Base):
    __tablename__ = 'no_show_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey('debtor_cycles.id', ondelete='CASCADE'))
    order_archive_id: Mapped[int] = mapped_column(Integer, nullable=True)
    no_show_date: Mapped[str] = mapped_column(String(10))
    assigned_amount: Mapped[int] = mapped_column(Integer, default=3000)
    cashier_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    cashier_reviewed_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    cashier_reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    buttons_expire_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    cycle: Mapped["DebtorCycle"] = relationship("DebtorCycle", back_populates="no_show_events")
    cashier_messages: Mapped[List["NoShowCashierMessage"]] = relationship(
        "NoShowCashierMessage", back_populates="event", cascade="all, delete-orphan"
    )


class NoShowCashierMessage(Base):
    __tablename__ = 'no_show_cashier_messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('no_show_events.id', ondelete='CASCADE'))
    cashier_tg_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(Integer)

    event: Mapped["NoShowEvent"] = relationship("NoShowEvent", back_populates="cashier_messages")


class Supervisor(Base):
    __tablename__ = 'supervisors'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(50))
    tg_id: Mapped[int] = mapped_column(BigInteger)


class Director(Base):
    __tablename__ = 'directors'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(50))
    tg_id: Mapped[int] = mapped_column(BigInteger)


class ShoutStat(Base):
    __tablename__ = 'shout_stats'

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_tg_id: Mapped[int] = mapped_column(BigInteger)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'))
    workers: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)

    order: Mapped["Order"] = relationship("Order", back_populates="shout_stats")


class Saving(Base):
    __tablename__ = 'savings'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[str] = mapped_column(String(10))
    saving_amount: Mapped[str] = mapped_column(String(10))
    date: Mapped[str] = mapped_column(String(10))


class Rule(Base):
    __tablename__ = 'rules'

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(10))
    rules: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(10))


class ChangeCity(Base):
    __tablename__ = 'change_city'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    changed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="change_city")


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    order_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[str] = mapped_column(String(10))
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    in_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(15), default="MODERATION")

    user: Mapped["User"] = relationship("User", back_populates="payments")


class WalletPayment(Base):
    __tablename__ = 'wallet_payments'

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('dataForSecurity.id'))
    amount: Mapped[str] = mapped_column(String(10))
    date: Mapped[str] = mapped_column(String(10))
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    api_registry_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="MODERATION")
    refund: Mapped[bool] = mapped_column(Boolean, default=False)

    worker: Mapped["DataForSecurity"] = relationship("DataForSecurity", back_populates="wallet_payments")


class JobForPayment(Base):
    __tablename__ = 'jobs_for_payment'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)


class Registry(Base):
    __tablename__ = 'registries'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    registry_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default='MODERATION')


class PlatformEmail(Base):
    __tablename__ = 'platform_emails'

    id: Mapped[int] = mapped_column(primary_key=True)
    email_addresses: Mapped[str] = mapped_column(Text)


class EmailLog(Base):
    __tablename__ = 'email_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    order_date: Mapped[str] = mapped_column(String(15))
    shift: Mapped[str] = mapped_column(String(5))
    work_cycle: Mapped[int] = mapped_column(Integer)
    email_type: Mapped[str] = mapped_column(String(10))
    recipients: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10))
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CallCampaign(Base):
    __tablename__ = 'call_campaigns'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'))
    shift: Mapped[str] = mapped_column(String(5))        # 'day' / 'night'
    order_date: Mapped[str] = mapped_column(String(15))  # "01.02.2026"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    results: Mapped[List["CallResult"]] = relationship(
        "CallResult", back_populates="campaign", cascade="all, delete-orphan"
    )


class CallResult(Base):
    __tablename__ = 'call_results'

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey('call_campaigns.id', ondelete='CASCADE'))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(25))
    zvonok_call_id: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default='pending')  # pending/green/yellow/red/blue
    attempt_no: Mapped[int] = mapped_column(Integer, default=0)
    raw_response: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    campaign: Mapped["CallCampaign"] = relationship("CallCampaign", back_populates="results")
    worker: Mapped["User"] = relationship("User")


class WebPanelNotification(Base):
    """Личные сообщения исполнителю от администрации (рассылка из бота → дубль в веб-панели)."""
    __tablename__ = 'web_panel_notifications'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(120), default='Сообщение от администрации')
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserDeviceToken(Base):
    """Expo push tokens for mobile push notifications."""
    __tablename__ = 'user_device_tokens'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PhoneVerification(Base):
    __tablename__ = 'phone_verifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    salt: Mapped[str] = mapped_column(String(64), nullable=True)
    pending_phone: Mapped[str] = mapped_column(String(25), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User")


class Promotion(Base):
    """Акция, привязанная к Получателю услуг."""
    __tablename__ = 'promotions'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete='CASCADE'), index=True)
    type: Mapped[str] = mapped_column(String(10))            # 'streak' / 'period'
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    n_orders: Mapped[int] = mapped_column(Integer)           # N (streak) / K (period)
    period_days: Mapped[int] = mapped_column(Integer, nullable=True)  # D (только для period)
    bonus_amount: Mapped[int] = mapped_column(Integer)       # сумма за 1 заявку (₽)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    city: Mapped[str] = mapped_column(String(25))

    customer: Mapped["Customer"] = relationship("Customer")
    participations: Mapped[List["PromotionParticipation"]] = relationship(
        "PromotionParticipation", back_populates="promotion", cascade="all, delete-orphan"
    )


class PromotionParticipation(Base):
    """Участие исполнителя в акции."""
    __tablename__ = 'promotion_participations'

    id: Mapped[int] = mapped_column(primary_key=True)
    promotion_id: Mapped[int] = mapped_column(ForeignKey('promotions.id', ondelete='CASCADE'), index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)   # текущая серия (streak-тип)
    period_start_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # начало периода (period-тип)
    period_completed: Mapped[int] = mapped_column(Integer, default=0)  # выполнено за текущий период
    status: Mapped[str] = mapped_column(String(15), default='active')  # active / cancelled
    cycles_completed: Mapped[int] = mapped_column(Integer, default=0)  # сколько циклов завершено

    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="participations")
    worker: Mapped["User"] = relationship("User")


class PromotionBonus(Base):
    """Начисленный бонус по акции (запись в «начисления»)."""
    __tablename__ = 'promotion_bonuses'

    id: Mapped[int] = mapped_column(primary_key=True)
    participation_id: Mapped[int] = mapped_column(ForeignKey('promotion_participations.id', ondelete='CASCADE'))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    promotion_name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)
    accrued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    worker: Mapped["User"] = relationship("User")


class Contract(Base):
    __tablename__ = 'contracts'

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    wallet_payment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('wallet_payments.id', ondelete='SET NULL'),
        nullable=True,
    )
    legal_entity_id: Mapped[int] = mapped_column(Integer)  # 392 / 393 / 480
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sign_tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # путь к PDF договору

    user: Mapped["User"] = relationship("User")
    order: Mapped[Optional["Order"]] = relationship("Order")


class WorkerAct(Base):
    """Акт выполненных работ, привязанный к заявке и работнику."""
    __tablename__ = 'worker_acts'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    wallet_payment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('wallet_payments.id', ondelete='SET NULL'),
        nullable=True,
    )
    legal_entity_id: Mapped[int] = mapped_column(Integer)  # 392 / 393 / 480
    amount: Mapped[str] = mapped_column(String(20))          # Сумма выплаты
    date: Mapped[str] = mapped_column(String(15))            # Дата акта DD.MM.YYYY
    status: Mapped[str] = mapped_column(String(30), default='pending')
    # pending → sent → signed / auto_signed / refused
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # путь к PDF
    card_snapshot: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # Карта на момент подписания акта

    order: Mapped["Order"] = relationship("Order")
    worker: Mapped["User"] = relationship("User")


class Receipt(Base):
    """Чек самозанятого из «Мой налог», привязанный к акту."""
    __tablename__ = 'receipts'

    id: Mapped[int] = mapped_column(primary_key=True)
    act_id: Mapped[int] = mapped_column(ForeignKey('worker_acts.id', ondelete='CASCADE'))
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    url: Mapped[str] = mapped_column(Text)                   # Ссылка на чек из «Мой налог»
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # путь к скачанному PDF

    act: Mapped["WorkerAct"] = relationship("WorkerAct")
    worker: Mapped["User"] = relationship("User")


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_session():
    async with async_session() as session:
        await session.close()
