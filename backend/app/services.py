from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from . import models, schemas

def list_hcps(db:Session): return list(db.scalars(select(models.HCP).order_by(models.HCP.name)).all())
def get_hcp(db:Session,hcp_id:int): return db.get(models.HCP,hcp_id)
def find_hcp_by_name(db:Session,name:str):
    needle=name.lower().replace('dr.','').replace('doctor','').strip()
    for h in list_hcps(db):
        candidate=h.name.lower().replace('dr.','').replace('doctor','').strip()
        if needle in candidate or candidate in needle: return h
    return None

def get_interaction(db:Session,iid:int):
    return db.scalar(select(models.Interaction).options(joinedload(models.Interaction.hcp)).where(models.Interaction.id==iid))
def create_interaction(db:Session,payload:schemas.InteractionCreate):
    x=models.Interaction(**payload.model_dump()); db.add(x); db.commit(); return get_interaction(db,x.id)
def update_interaction(db:Session,x:models.Interaction,payload:schemas.InteractionUpdate):
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(x,k,v)
    db.add(x); db.commit(); return get_interaction(db,x.id)
def list_interactions(db:Session,hcp_id:int|None=None,limit:int=50):
    q=select(models.Interaction).options(joinedload(models.Interaction.hcp)).order_by(models.Interaction.interaction_date.desc(),models.Interaction.id.desc()).limit(limit)
    if hcp_id: q=q.where(models.Interaction.hcp_id==hcp_id)
    return list(db.scalars(q).unique().all())
def create_follow_up(db:Session,payload:schemas.FollowUpCreate):
    x=models.FollowUp(**payload.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
def list_follow_ups(db:Session,hcp_id:int|None=None):
    q=select(models.FollowUp).order_by(models.FollowUp.due_date)
    if hcp_id: q=q.where(models.FollowUp.hcp_id==hcp_id)
    return list(db.scalars(q).all())
