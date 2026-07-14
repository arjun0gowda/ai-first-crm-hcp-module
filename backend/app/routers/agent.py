from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import ChatRequest,ChatResponse
from ..agent.graph import build_graph
from ..config import get_settings
router=APIRouter(prefix='/agent',tags=['AI Agent'])
@router.get('/status')
def status():
    settings=get_settings()
    return {'groq_configured':bool(settings.groq_api_key),'model':settings.groq_model}
@router.get('/tools')
def tools(): return [{'name':'log_interaction'},{'name':'edit_interaction'},{'name':'search_interaction_history'},{'name':'schedule_follow_up'},{'name':'recommend_next_best_action'}]
@router.post('/chat',response_model=ChatResponse)
def chat(payload:ChatRequest,db:Session=Depends(get_db)):
    s=build_graph(db).invoke({'user_message':payload.message})
    return ChatResponse(reply=s.get('reply','Done.'),tool_used=s.get('tool_used'),data=s.get('result'),form_data=s.get('form_data') or None,llm_used=bool(s.get('llm_used')))
