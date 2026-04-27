from aiogram import Router
from typing import List

from . import starts
from .user import *
from .admin import *
from .admin.menu import admin_orders, delete_worker_from_order, roles, closure_report
from .admin.menu.update_customer import travel_compensation
from .admin.menu.update_customer import promotions as admin_promotions
from .user.menu import promotions as worker_promotions
from .admin.menu.self_employed import entry, annul, unfulfilled
from .admin.menu.self_employed import archive as self_employed_archive
from .accountant.menu import debtors, add_debtor, balance_report, change_accruals
from .admin.menu import rr_sync
from .customer import *
from .manager import *
from .manager import workers_view
from .manager.menu import call_campaigns, call_archive
from .user.menu import phone_verification
from .foreman import *
from .supervisor import *
from .accountant import accountant_router
from . import director


def get_routers() -> List[Router]:
    return [
        starts.router,

        # Admin routers should be first (more specific filters)
        roles.router,
        admin_orders.router,
        delete_worker_from_order.router,
        closure_report.router,
        travel_compensation.router,
        help_group.router,

        # Admin self-employed (debtor management)
        entry.router,
        annul.router,
        self_employed_archive.router,
        unfulfilled.router,

        # Accountant (cashier) routers
        debtors.router,
        add_debtor.router,
        balance_report.router,
        change_accruals.router,

        # Admin commands
        rr_sync.router,

        # Director routers
        director.router,

        # Manager routers
        orders.router,

        # User routers
        registration.router,
        sign_act.router,
        show_contracts.router,
        accountant_router,
        create_worker_payment.router,
        confirmation_payment.router,
        about_worker.router,
        help.router,
        search_orders.router,
        user_applications.router,
        change_city.router,
        referral_system.router,
        order_for_friend.router,
        change_rules.router,
        foreman_router,
        rules_for_worker.router,
        shout.router,
        update_real_data.router,
        update_bank_card.router,
        settings.router,
        managers.router,
        customers.router,
        supervisors.router,
        collation.router,
        adm_workers.router,
        set_pics.router,
        add_worker.router,
        open_account_menu.router,
        open_delete_worker_menu.router,
        open_erase_worker_menu.router,
        open_correct_rating_menu.router,
        confirmation_change_city.router,
        by_last_name.router,
        confirmation_delete_worker.router,
        confirmation_erase_worker_tg_id.router,
        rating_adjustment.router,
        edit_accountant.router,
        self_collation.router,
        platform_email.router,
        math.router,
        phone_verification.router,
        order.router,
        open_shifts_menu.router,
        open_cities_menu.router,
        open_customer_admins_menu.router,
        open_customer_foremen_menu.router,
        add_customer_foremen.router,
        delete_customer_foremen.router,
        jobs_for_payments.router,
        add_city.router,
        update_city.router,
        show_way.router,
        add_city_way.router,
        groups_router,
        day_shift.router,
        night_shift.router,
        add_job.router,
        supervisor_orders.router,
        add_customer_admin.router,
        delete_customer_admin.router,
        open_premium_workers_menu.router,
        add_premium_worker.router,
        delete_premium_worker.router,
        create_pdf.router,
        unblock_user.router,
        block_user.router,
        create_order.router,
        customer_orders.router,
        delete_order.router,
        open_order_management.router,
        customer_shout_menu.router,
        customer_send_message.router,
        customer_stat.router,
        applications.router,
        moderation_menu.router,
        orders_in_progress.router,
        workers.router,
        workers_view.router,
        newsletter.router,
        archive.router,
        open_jobs_menu.router,
        update_job_amount.router,
        email_management.router,
        call_campaigns.router,
        call_archive.router,
        admin_promotions.router,
        worker_promotions.router,
    ]
