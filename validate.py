from typing import Tuple
from guardrails import Guard
from guardrails.hub import DetectPII, RestrictToTopic
import streamlit as st

@st.cache_resource
def get_guards():
    return Guard().use_many(
        DetectPII(
            pii_entities=['IBAN_CODE', 'IP_ADDRESS', 'LOCATION', 'CREDIT_CARD'],
            on_fail='exception'
        ),
        RestrictToTopic(
            valid_topics=['scope of mock interview'],
            on_fail='reask'
        )
    )

def validate_input(user_input: str) -> Tuple[bool, str]:
    try:
        get_guards().validate(user_input)
        return True, ""
    except Exception as e:
        return False, str(e)
    
