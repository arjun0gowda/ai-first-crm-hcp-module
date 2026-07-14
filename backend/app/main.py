from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .config import get_settings
from .database import Base,SessionLocal,engine
from .models import HCP
from .routers import agent,followups,hcps,interactions
settings=get_settings()
def seed():
    db=SessionLocal()
    try:
        if db.scalar(select(HCP.id).limit(1)): return
        db.add_all([HCP(name='Dr. Ananya Rao',specialty='Cardiology',institution='City Heart Institute'),HCP(name='Dr. Vikram Shah',specialty='Endocrinology',institution='Metro Diabetes Centre'),HCP(name='Dr. Meera Iyer',specialty='General Medicine',institution='Green Valley Hospital')]); db.commit()
    finally: db.close()
@asynccontextmanager
async def lifespan(_:FastAPI): Base.metadata.create_all(bind=engine); seed(); yield
app=FastAPI(title=settings.app_name,version='2.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(hcps.router,prefix='/api'); app.include_router(interactions.router,prefix='/api'); app.include_router(followups.router,prefix='/api'); app.include_router(agent.router,prefix='/api')
@app.get('/health')
def health(): return {'status':'ok','service':settings.app_name}
