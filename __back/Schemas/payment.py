from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class WorkerPaymentSchema(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    inn: str = Field(max_length=12)
    amount: str = Field(max_length=4)
    type_of_work: str
    card_number: str = Field(max_length=16)
    phone: str = Field(max_length=10)

    model_config = ConfigDict(extra='forbid')


class WorkerChangeAmountSchema(BaseModel):
    payment_id: int
    full_name: str
    old_amount: str
    new_amount: Optional[str] = None
