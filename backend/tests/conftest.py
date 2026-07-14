import os
os.environ['DATABASE_URL']='sqlite:///./test_hcp_crm.db'
os.environ['GROQ_API_KEY']=''
import pytest
from fastapi.testclient import TestClient
from app.database import Base,engine
from app.main import app

@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
