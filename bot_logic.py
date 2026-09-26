import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY or "dummy_key_to_allow_startup",
)

SYSTEM_PROMPT = """You are Vera, magicpin's merchant-AI assistant. You engage with local merchants in India over WhatsApp.
You MUST reply with a JSON object containing the exact fields: 'body' (string), 'cta' (string: binary YES/STOP, open_ended, or none), 'send_as' (string: vera or merchant_on_behalf), 'suppression_key' (string), and 'rationale' (string).

Rules:
1. Specificity: Use concrete numbers/stats.
2. Category Fit: Match the voice.
3. Merchant Fit: Personalize to their numbers and language preference.
4. Trigger Relevance: State WHY you are messaging.
5. Engagement: Use a hook. End with ONE clear CTA.
6. Don't fabricate data.
"""

def compose(category: dict, merchant: dict, trigger: dict, customer: dict | None = None) -> dict:
    context_str = (
        f"--- CATEGORY CONTEXT ---\n{json.dumps(category, indent=2)}\n\n"
        f"--- MERCHANT CONTEXT ---\n{json.dumps(merchant, indent=2)}\n\n"
        f"--- TRIGGER CONTEXT ---\n{json.dumps(trigger, indent=2)}\n\n"
    )
    if customer:
        context_str += f"--- CUSTOMER CONTEXT ---\n{json.dumps(customer, indent=2)}\n\n"

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate the WhatsApp message based on the following contexts:\n\n{context_str}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result = json.loads(response.choices[0].message.content)
        
        if "body" not in result: result["body"] = "Hello, checking in on your profile."
        if "cta" not in result: result["cta"] = "open_ended"
        if "send_as" not in result: result["send_as"] = "merchant_on_behalf" if customer else "vera"
        if "suppression_key" not in result: result["suppression_key"] = trigger.get("suppression_key", "default")
        if "rationale" not in result: result["rationale"] = "Generated message based on trigger."
        return result
    except Exception as e:
        return {
            "body": "Hi there! I have some updates for your business. Reply YES to know more.",
            "cta": "YES/STOP",
            "send_as": "merchant_on_behalf" if customer else "vera",
            "suppression_key": trigger.get("suppression_key", "error_fallback"),
            "rationale": "Fallback message due to error."
        }

REPLY_PROMPT = """You are Vera, magicpin's AI assistant. You are in an ongoing WhatsApp chat with a merchant.
You MUST reply with a JSON object containing exactly these fields: 'action' (string: 'send', 'wait', or 'end'), 'body' (string, only if action is send), 'cta' (string, only if send), and 'rationale' (string).

Rules:
1. If they say no, stop, or are hostile -> action: 'end'.
2. If they say yes or agree -> action: 'send', acknowledge it specifically based on what they agreed to, and conclude the flow gracefully (cta: 'none').
3. Keep it conversational, match their language.
"""

def respond(history: list[dict], merchant: dict | None = None) -> dict:
    context_str = ""
    if merchant:
        context_str += f"--- MERCHANT CONTEXT ---\n{json.dumps(merchant, indent=2)}\n\n"
    
    history_str = "--- CONVERSATION HISTORY ---\n"
    for msg in history[-5:]:  # Last 5 turns
        history_str += f"{msg['from']}: {msg['msg']}\n"
        
    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": REPLY_PROMPT},
                {"role": "user", "content": f"Context:\n{context_str}\n\nHistory:\n{history_str}\n\nGenerate the next bot action:"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result = json.loads(response.choices[0].message.content)
        if "action" in result: result["action"] = result["action"].lower()
        return result
    except Exception as e:
        last_msg = history[-1]['msg'].lower() if history else ""
        if any(w in last_msg for w in ["stop", "no", "fuck", "hate", "unsubscribe"]):
            return {"action": "end", "rationale": "Fallback: user requested stop or was hostile."}
        return {"action": "send", "body": "Got it, thanks!", "cta": "none", "rationale": "Fallback reply"}
