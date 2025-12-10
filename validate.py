from typing import Tuple
from guardrails import Guard
import streamlit as st
import os

guardrails_api_key = st.secrets["GUARDRAILS_API_KEY"]

os.system("guardrails configure --enable-remote-inferencing --enable-metrics --token {guardrails_api_key}")
os.system("guardrails hub install hub://tryolabs/restricttotopic")
os.system("guardrails hub install hub://guardrails/detect_pii")


from guardrails.hub import RestrictToTopic
from guardrails.hub import DetectPII

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
    
