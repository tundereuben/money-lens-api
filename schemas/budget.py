from pydantic import BaseModel
from datetime import date
from typing import Optional

from schemas.category import CategoryResponse

class BudgetCreate(BaseModel):
    name: str
    amount: float
    category_id: int 

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float]
    
class BudgetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    amount: float
    category_id: int
    category: CategoryResponse