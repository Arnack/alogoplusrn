import logging
import secrets
from types import SimpleNamespace
from datetime import datetime
from sqlalchemy import select, update, text

from database.models import Contract, async_session


LEGAL_ENTITY_IDS = [392, 393, 480]


async def _has_wallet_payment_id_column(session) -> bool:
    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'contracts' AND column_name = 'wallet_payment_id'
        LIMIT 1
        """
    )
    result = await session.execute(query)
    return result.scalar() == 1


def _contract_from_row(row) -> SimpleNamespace:
    return SimpleNamespace(
        id=row.id,
        number=row.number,
        user_id=row.user_id,
        order_id=row.order_id,
        wallet_payment_id=getattr(row, 'wallet_payment_id', None),
        legal_entity_id=row.legal_entity_id,
        created_at=row.created_at,
        signed_at=row.signed_at,
        sign_tg_id=row.sign_tg_id,
        is_archived=row.is_archived,
        file_path=row.file_path,
    )


def _generate_contract_number() -> str:
    ts = datetime.now().strftime('%y%m%d')
    rnd = secrets.token_hex(3).upper()
    return f'AP-{ts}-{rnd}'


async def create_contracts_for_all_orgs(
    user_id: int,
    order_id: int | None = None,
    wallet_payment_id: int | None = None,
) -> list:
    """Создаёт 3 договора (по одному на каждое ИП) и возвращает их.

    order_id — заявка, к которой привязаны договоры (None для регистрационных договоров).
    """
    contracts = []
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        for org_id in LEGAL_ENTITY_IDS:
            number = _generate_contract_number()
            params = {
                'number': number,
                'user_id': user_id,
                'order_id': order_id,
                'legal_entity_id': org_id,
                'created_at': datetime.now(),
                'signed_at': None,
                'sign_tg_id': None,
                'is_archived': False,
                'file_path': None,
            }
            if has_wallet_payment_id:
                params['wallet_payment_id'] = wallet_payment_id
                insert_sql = text(
                    """
                    INSERT INTO contracts
                    (number, user_id, order_id, wallet_payment_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path)
                    VALUES
                    (:number, :user_id, :order_id, :wallet_payment_id, :legal_entity_id, :created_at, :signed_at, :sign_tg_id, :is_archived, :file_path)
                    RETURNING id, number, user_id, order_id, wallet_payment_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path
                    """
                )
            else:
                insert_sql = text(
                    """
                    INSERT INTO contracts
                    (number, user_id, order_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path)
                    VALUES
                    (:number, :user_id, :order_id, :legal_entity_id, :created_at, :signed_at, :sign_tg_id, :is_archived, :file_path)
                    RETURNING id, number, user_id, order_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path
                    """
                )
            result = await session.execute(insert_sql, params)
            row = result.mappings().first()
            if row:
                contracts.append(_contract_from_row(row))
        await session.commit()
    return contracts


async def get_user_contracts(user_id: int) -> list:
    """Возвращает все договоры пользователя."""
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        columns = "id, number, user_id, order_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        if has_wallet_payment_id:
            columns = "id, number, user_id, order_id, wallet_payment_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        result = await session.execute(
            text(f"SELECT {columns} FROM contracts WHERE user_id = :user_id ORDER BY id"),
            {'user_id': user_id},
        )
        return [_contract_from_row(row) for row in result.mappings().all()]


async def sign_contracts_for_user(user_id: int, tg_id: int) -> bool:
    """Помечает все договоры пользователя как подписанные."""
    async with async_session() as session:
        try:
            await session.execute(
                text(
                    """
                    UPDATE contracts
                    SET signed_at = :signed_at, sign_tg_id = :sign_tg_id
                    WHERE user_id = :user_id
                    """
                ),
                {
                    'signed_at': datetime.now(),
                    'sign_tg_id': tg_id,
                    'user_id': user_id,
                },
            )
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logging.exception(e)
            return False


async def set_contract_file_path(contract_id: int, file_path: str) -> None:
    """Сохраняет путь к файлу PDF договора (п.11 ТЗ)."""
    async with async_session() as session:
        await session.execute(
            text("UPDATE contracts SET file_path = :file_path WHERE id = :contract_id"),
            {'file_path': file_path, 'contract_id': contract_id},
        )
        await session.commit()


async def get_contract(contract_id: int) -> Contract | None:
    """Возвращает договор по ID."""
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        columns = "id, number, user_id, order_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        if has_wallet_payment_id:
            columns = "id, number, user_id, order_id, wallet_payment_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        result = await session.execute(
            text(f"SELECT {columns} FROM contracts WHERE id = :contract_id LIMIT 1"),
            {'contract_id': contract_id},
        )
        row = result.mappings().first()
        return _contract_from_row(row) if row else None


async def archive_contracts_except_legal_entity(
    user_id: int,
    legal_entity_id: int,
    order_id: int | None = None,
    wallet_payment_id: int | None = None,
) -> list[int]:
    """
    Архивирует 2 договора из 3, оставляя только договор с выбранным legal_entity_id (п.7 ТЗ).

    Args:
        user_id: ID пользователя
        legal_entity_id: ID юридического лица, договор которого нужно оставить
        order_id: ID заявки (если нужно архивировать договоры конкретной заявки)

    Returns:
        Список ID архивированных договоров
    """
    archived_ids = []
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        where_parts = [
            "user_id = :user_id",
            "legal_entity_id != :legal_entity_id",
            "is_archived = false",
        ]
        params = {'user_id': user_id, 'legal_entity_id': legal_entity_id}
        if order_id is not None:
            where_parts.append("order_id = :order_id")
            params['order_id'] = order_id
        if wallet_payment_id is not None and has_wallet_payment_id:
            where_parts.append("wallet_payment_id = :wallet_payment_id")
            params['wallet_payment_id'] = wallet_payment_id
        result = await session.execute(
            text(f"SELECT id FROM contracts WHERE {' AND '.join(where_parts)}"),
            params,
        )
        archived_ids = [row.id for row in result.mappings().all()]
        if archived_ids:
            await session.execute(
                text("UPDATE contracts SET is_archived = true WHERE id = ANY(:contract_ids)"),
                {'contract_ids': archived_ids},
            )
        await session.commit()

    return archived_ids


async def get_active_contract(
    user_id: int,
    legal_entity_id: int,
    order_id: int | None = None,
    wallet_payment_id: int | None = None,
) -> Contract | None:
    """
    Возвращает активный договор пользователя для выбранного ИП.

    Args:
        user_id: ID пользователя
        legal_entity_id: ID юридического лица
        order_id: ID заявки (опционально)
    """
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        where_parts = [
            "user_id = :user_id",
            "legal_entity_id = :legal_entity_id",
            "is_archived = false",
        ]
        params = {
            'user_id': user_id,
            'legal_entity_id': legal_entity_id,
        }
        if order_id is not None:
            where_parts.append("order_id = :order_id")
            params['order_id'] = order_id
        if wallet_payment_id is not None and has_wallet_payment_id:
            where_parts.append("wallet_payment_id = :wallet_payment_id")
            params['wallet_payment_id'] = wallet_payment_id
        columns = "id, number, user_id, order_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        if has_wallet_payment_id:
            columns = "id, number, user_id, order_id, wallet_payment_id, legal_entity_id, created_at, signed_at, sign_tg_id, is_archived, file_path"
        result = await session.execute(
            text(
                f"""
                SELECT {columns}
                FROM contracts
                WHERE {' AND '.join(where_parts)}
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            params,
        )
        row = result.mappings().first()
        return _contract_from_row(row) if row else None
