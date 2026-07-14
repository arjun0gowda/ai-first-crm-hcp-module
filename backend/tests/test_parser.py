from app.agent.parser import deterministic_parse

def test_schedule_extracts_date_and_task():
    p=deterministic_parse('Schedule a follow-up for interaction 1 on 2026-07-21 to send clinical evidence.')
    assert p['intent']=='schedule_follow_up'; assert p['arguments']['interaction_id']==1; assert p['arguments']['due_date']=='2026-07-21'; assert p['arguments']['task']=='send clinical evidence'
def test_edit_extracts_changes():
    p=deterministic_parse('Edit interaction 1. Change sentiment to neutral and add outcome: requested more clinical evidence.')
    assert p['arguments']['changes']=={'sentiment':'Neutral','outcomes':'requested more clinical evidence'}
def test_log_is_not_misrouted_by_follow_up_phrase():
    p=deterministic_parse('Log a meeting with Dr. Vikram Shah today. We discussed adherence and need to follow up next week.')
    assert p['intent']=='log_interaction'; assert p['arguments']['follow_up_actions']=='Follow up next week'


def test_llm_list_values_are_normalized():
    from app.agent.tools import _as_text, _normalize_interaction_fields

    assert _as_text(["one", "two"]) == "one; two"
    normalized = _normalize_interaction_fields(
        {
            "outcomes": ["Dr. Vikram Shah was positive about the product"],
            "materials_shared": ["Brochure", "Clinical paper"],
            "sentiment": ["Positive"],
        }
    )
    assert normalized["outcomes"] == "Dr. Vikram Shah was positive about the product"
    assert normalized["materials_shared"] == "Brochure; Clinical paper"
    assert normalized["sentiment"] == "Positive"
