from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import HCPRead
from ..services import list_hcps
router=APIRouter(prefix='/hcps',tags=['HCPs'])
@router.get('',response_model=list[HCPRead])
def all_hcps(db:Session=Depends(get_db)): return list_hcps(db)
