def chat(client,message): return client.post('/api/agent/chat',json={'message':message})
def test_all_five_tools(client):
    r=chat(client,'Log a meeting with Dr. Vikram Shah today. We discussed diabetes adherence. He was positive. I shared a brochure and need to follow up next week.')
    assert r.status_code==200; body=r.json(); assert body['tool_used']=='log_interaction'; iid=body['data']['id']; assert body['form_data']['hcp_name']=='Dr. Vikram Shah'
    r=chat(client,'Show recent interaction history for Dr. Vikram Shah.'); assert r.status_code==200; assert len(r.json()['data'])==1
    r=chat(client,f'Edit interaction {iid}. Change sentiment to neutral and add outcome: requested more clinical evidence.'); assert r.status_code==200; assert r.json()['data']['sentiment']=='Neutral'; assert r.json()['data']['outcomes']=='requested more clinical evidence'
    r=chat(client,f'Schedule a follow-up for interaction {iid} on 2026-07-21 to send clinical evidence.'); assert r.status_code==200; assert r.json()['data']['due_date']=='2026-07-21'
    r=chat(client,'Recommend the next best action for Dr. Vikram Shah.'); assert r.status_code==200; assert r.json()['tool_used']=='recommend_next_best_action'
