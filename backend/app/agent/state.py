from typing import Any, TypedDict
class AgentState(TypedDict,total=False):
    user_message:str
    intent:str
    arguments:dict[str,Any]
    tool_used:str
    result:Any
    form_data:dict[str,Any]
    reply:str
    error:str
    llm_used:bool
