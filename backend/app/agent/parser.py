import json, re
from datetime import date, timedelta
from typing import Any
from groq import Groq
from ..config import get_settings

EDIT_FIELDS={'interaction_type','interaction_date','interaction_time','attendees','topics_discussed','materials_shared','samples_distributed','sentiment','outcomes','follow_up_actions','ai_summary'}

def _iso_date(message:str)->str|None:
    m=re.search(r'\b(20\d{2}-\d{2}-\d{2})\b',message)
    return m.group(1) if m else None

def _hcp_name(message:str)->str|None:
    m=re.search(r'\bDr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}',message)
    return m.group(0).rstrip('.,') if m else None

def _interaction_id(message:str)->int|None:
    m=re.search(r'\binteraction\s*#?\s*(\d+)\b',message,re.I)
    return int(m.group(1)) if m else None

def _relative_due(message:str)->str|None:
    low=message.lower()
    today=date.today()
    if 'tomorrow' in low: return (today+timedelta(days=1)).isoformat()
    if 'next week' in low: return (today+timedelta(days=7)).isoformat()
    return None

def deterministic_parse(message:str)->dict[str,Any]:
    low=message.lower().strip(); args={}
    iid=_interaction_id(message); hcp=_hcp_name(message); iso=_iso_date(message)
    if iid: args['interaction_id']=iid
    if hcp: args['hcp_name']=hcp

    if re.match(r'^(edit|update|modify|change)\b',low) or 'edit interaction' in low:
        intent='edit_interaction'; changes={}
        sm=re.search(r'(?:change|set|update)\s+(?:the\s+)?sentiment\s+to\s+(positive|neutral|negative)',message,re.I)
        if sm: changes['sentiment']=sm.group(1).title()
        om=re.search(r'(?:add|change|set|update)\s+(?:the\s+)?outcomes?\s*(?:to|:)\s*(.+?)(?:\.|$)',message,re.I)
        if om: changes['outcomes']=om.group(1).strip()
        fm=re.search(r'(?:add|change|set|update)\s+(?:the\s+)?follow[ -]?up(?:\s+actions?)?\s*(?:to|:)\s*(.+?)(?:\.|$)',message,re.I)
        if fm: changes['follow_up_actions']=fm.group(1).strip()
        args['changes']=changes
    elif 'history' in low or low.startswith('show recent interaction'):
        intent='search_interaction_history'
    elif 'next best action' in low or low.startswith('recommend'):
        intent='recommend_next_best_action'
    elif low.startswith('schedule') or low.startswith('create a follow'):
        intent='schedule_follow_up'
        due=iso or _relative_due(message)
        if due: args['due_date']=due
        tm=re.search(r'\bto\s+(.+?)(?:\.|$)',message,re.I)
        args['task']=tm.group(1).strip() if tm else message
    elif re.match(r'^(log|record|add)\b',low) or any(x in low for x in ['we discussed','met with','meeting with','call with']):
        intent='log_interaction'
        args['interaction_date']=iso or date.today().isoformat()
        args['topics_discussed']=message
        if 'positive' in low: args['sentiment']='Positive'
        elif 'negative' in low: args['sentiment']='Negative'
        elif 'neutral' in low: args['sentiment']='Neutral'
        if 'brochure' in low: args['materials_shared']='Brochure'
        follow=re.search(r'(?:need to|should|will)\s+follow[ -]?up\s+(.+?)(?:\.|$)',message,re.I)
        if follow: args['follow_up_actions']='Follow up '+follow.group(1).strip()
    else: intent='help'
    return {'intent':intent,'arguments':args}

SYSTEM=("You extract CRM actions from field-representative text. Return one valid JSON object only, with keys intent and arguments.\\n"
        "Allowed intents: log_interaction, edit_interaction, search_interaction_history, schedule_follow_up, recommend_next_best_action, help.\\n"
        "For edit_interaction put edits under arguments.changes. Use outcomes (plural), not outcome.\\n"
        "For schedule_follow_up return due_date in YYYY-MM-DD and task.\\n"
        "For a sentence beginning Log/Record/Add, always choose log_interaction even when it mentions a later follow-up.\\n"
        "Never invent an interaction ID. Today is {today}.")

def llm_parse(message:str)->tuple[dict[str,Any],bool]:
    settings=get_settings()
    if not settings.groq_api_key: return {},False
    client=Groq(api_key=settings.groq_api_key)
    response=client.chat.completions.create(
        model=settings.groq_model, temperature=0,
        response_format={'type':'json_object'},
        messages=[{'role':'system','content':SYSTEM.format(today=date.today().isoformat())},{'role':'user','content':message}],
    )
    content=response.choices[0].message.content or '{}'
    try: return json.loads(content),True
    except json.JSONDecodeError:
        m=re.search(r'\{.*\}',content,re.S)
        return (json.loads(m.group(0)) if m else {}),True

def merge_parse(message:str)->tuple[dict[str,Any],bool]:
    base=deterministic_parse(message)
    try: enriched,used=llm_parse(message)
    except Exception: enriched,used={},False
    eargs=enriched.get('arguments') if isinstance(enriched,dict) else {}
    eargs=eargs if isinstance(eargs,dict) else {}
    # LLM enriches first; deterministic values override essential fields.
    args={**eargs,**base['arguments']}
    if base['intent']=='edit_interaction':
        echanges=eargs.get('changes') if isinstance(eargs.get('changes'),dict) else {}
        bchanges=base['arguments'].get('changes',{})
        # Move accidentally top-level editable fields into changes.
        for f in EDIT_FIELDS:
            if f in eargs and eargs[f] is not None: echanges[f]=eargs[f]
        args['changes']={**echanges,**bchanges}
    intent=base['intent'] if base['intent']!='help' else enriched.get('intent','help')
    return {'intent':intent,'arguments':args},used

def summarize(data:dict[str,Any])->str:
    settings=get_settings()
    fallback=f"{data.get('interaction_type','Interaction')} with {data.get('hcp_name','HCP')}: {data.get('topics_discussed','No topics supplied')}. Sentiment: {data.get('sentiment','Neutral')}."
    if not settings.groq_api_key: return fallback
    try:
        client=Groq(api_key=settings.groq_api_key)
        r=client.chat.completions.create(model=settings.groq_model,temperature=.2,messages=[{'role':'system','content':'Write a concise two-sentence CRM summary using only supplied facts.'},{'role':'user','content':json.dumps(data,default=str)}])
        return (r.choices[0].message.content or fallback).strip()
    except Exception: return fallback
