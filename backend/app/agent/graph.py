from sqlalchemy.orm import Session
from langgraph.graph import END, START, StateGraph
from .parser import merge_parse
from .state import AgentState
from .tools import TOOL_REGISTRY

def build_graph(db:Session):
    def understand(state:AgentState):
        parsed,used=merge_parse(state['user_message'])
        return {'intent':parsed.get('intent','help'),'arguments':parsed.get('arguments') or {},'llm_used':used}
    def execute(state:AgentState):
        intent=state.get('intent','help')
        if intent not in TOOL_REGISTRY:
            return {'reply':'I can log or edit interactions, search HCP history, schedule follow-ups, and recommend the next best action.'}
        try:
            result=TOOL_REGISTRY[intent](db,state.get('arguments') or {})
            return {'tool_used':intent,'result':result,'form_data':result if intent in {'log_interaction','edit_interaction'} and isinstance(result,dict) else {}}
        except Exception as e: return {'tool_used':intent,'error':str(e)}
    def respond(state:AgentState):
        if state.get('reply'): return {}
        if state.get('error'): return {'reply':f"I could not complete that action: {state['error']}"}
        intent=state.get('tool_used'); result=state.get('result')
        if intent=='log_interaction': reply=f"Interaction logged successfully with ID {result['id']}. The form has been populated from your summary."
        elif intent=='edit_interaction': reply=f"Interaction {result['id']} was updated successfully."
        elif intent=='search_interaction_history': reply=f"I found {len(result)} recent interaction(s)." if result else 'No interactions were found for this HCP.'
        elif intent=='schedule_follow_up': reply=f"Follow-up {result['id']} was scheduled for {result['due_date']}."
        elif intent=='recommend_next_best_action': reply=f"{result['recommendation']}\n\nReason: {result['reason']}"
        else: reply='Action completed.'
        return {'reply':reply}
    g=StateGraph(AgentState); g.add_node('understand',understand); g.add_node('execute_tool',execute); g.add_node('respond',respond)
    g.add_edge(START,'understand'); g.add_edge('understand','execute_tool'); g.add_edge('execute_tool','respond'); g.add_edge('respond',END)
    return g.compile()
