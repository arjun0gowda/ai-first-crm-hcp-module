from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import InteractionCreate,InteractionRead,InteractionUpdate
from .. import services
router=APIRouter(prefix='/interactions',tags=['Interactions'])
@router.post('',response_model=InteractionRead,status_code=201)
def create(payload:InteractionCreate,db:Session=Depends(get_db)):
    if not services.get_hcp(db,payload.hcp_id): raise HTTPException(404,'HCP not found')
    return services.create_interaction(db,payload)
@router.get('',response_model=list[InteractionRead])
def all_items(hcp_id:int|None=None,limit:int=Query(50,ge=1,le=200),db:Session=Depends(get_db)): return services.list_interactions(db,hcp_id,limit)
@router.patch('/{interaction_id}',response_model=InteractionRead)
def edit(interaction_id:int,payload:InteractionUpdate,db:Session=Depends(get_db)):
    x=services.get_interaction(db,interaction_id)
    if not x: raise HTTPException(404,'Interaction not found')
    return services.update_interaction(db,x,payload)
