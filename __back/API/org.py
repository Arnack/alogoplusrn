from API.fin.contracts import fin_change_organization, fin_get_organization_balance


async def get_organization_balance(org_id: int) -> str | None:
    return await fin_get_organization_balance(org_id)


async def change_current_organization(org_id: int) -> bool:
    return await fin_change_organization(org_id)
