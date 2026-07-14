from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import FollowUpCreate,FollowUpRead
from .. import services
router=APIRouter(prefix='/follow-ups',tags=['Follow-ups'])
@router.post('',response_model=FollowUpRead,status_code=201)
def create(payload:FollowUpCreate,db:Session=Depends(get_db)):
    if not services.get_hcp(db,payload.hcp_id): raise HTTPException(404,'HCP not found')
    if payload.interaction_id and not services.get_interaction(db,payload.interaction_id): raise HTTPException(404,'Interaction not found')
    return services.create_follow_up(db,payload)
@router.get('',response_model=list[FollowUpRead])
def all_items(hcp_id:int|None=None,db:Session=Depends(get_db)): return services.list_follow_ups(db,hcp_id)
