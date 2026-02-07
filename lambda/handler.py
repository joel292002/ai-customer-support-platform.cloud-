import json
import logging
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# -------------------------
# AWS clients
# -------------------------
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ConversationMessages")

sns = boto3.client("sns")

# Feature flags / config
AI_PROVIDER = os.getenv("AI_PROVIDER", "stub")  # stub | bedrock
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

# -------------------------
# Business rule keywords
# -------------------------
FORBIDDEN_KEYWORDS = [
    "lawsuit", "legal advice", "sue",
    "financial advice", "investment",
    "medical advice", "diagnosis"
]

ANGRY_KEYWORDS = [
    "stupid", "useless", "angry",
    "terrible", "hate", "sucks"
]


# -------------------------
# Lambda handler
# -------------------------
def lambda_handler(event, context):
    start_time = datetime.utcnow()

    try:
        # 1. Parse request
        body = json.loads(event.get("body", "{}"))

        user_id = body.get("userId")
        message = body.get("message")
        channel = body.get("channel", "unknown")

        if not user_id or not message:
            return response(400, {"error": "userId and message are required"})

        logger.info(f"Received message from user {user_id} via {channel}")

        # 2. Apply business rules FIRST
        allowed, violation = apply_business_rules(message)

        if not allowed:
            logger.warning(f"Business rule triggered: {violation}")

            reply = (
                "This request needs to be reviewed by a human support agent. "
                "We’ve forwarded it to the appropriate team."
            )

            # Save messages
            save_message(user_id, "user", message)
            save_message(user_id, "assistant", reply)

            # Notify human (NON-FATAL)
            notify_human(user_id, message, violation)

            return response(
                200,
                {
                    "reply": reply,
                    "needsHuman": True
                }
            )

        # 3. Fetch conversation history
        history = get_recent_messages(user_id)

        # 4. Save user message
        save_message(user_id, "user", message)

        # 5. Build prompt
        prompt = build_prompt(history, message)

        # 6. AI provider (feature-flagged)
        if AI_PROVIDER == "bedrock":
            ai_reply = call_bedrock(prompt)  # intentionally disabled
        else:
            ai_reply = call_ai_stub(prompt)

        # 7. Save assistant response
        save_message(user_id, "assistant", ai_reply)

        return response(
            200,
            {
                "reply": ai_reply,
                "needsHuman": False
            }
        )

    except Exception:
        logger.exception("Unhandled error")
        return response(500, {"error": "Internal server error"})

    finally:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Execution completed in {duration}s")


# -------------------------
# Business rules engine
# -------------------------
def apply_business_rules(message):
    msg = message.lower()

    for word in FORBIDDEN_KEYWORDS:
        if word in msg:
            return False, "forbidden_topic"

    for word in ANGRY_KEYWORDS:
        if word in msg:
            return False, "angry_user"

    return True, None


# -------------------------
# Prompt builder (AI-ready)
# -------------------------
def build_prompt(history, user_message):
    conversation = ""
    for item in reversed(history):
        conversation += f"{item['role']}: {item['message']}\n"

    prompt = f"""
You are a professional customer support assistant.

Guidelines:
- Be calm, friendly, and concise
- Do not provide legal, medical, or financial advice
- Ask clarifying questions if needed
- Escalate to a human if appropriate

Conversation history:
{conversation}

User message:
{user_message}

Response:
"""
    return prompt.strip()


# -------------------------
# AI implementations
# -------------------------
def call_ai_stub(prompt):
    """
    Cost-free AI stub used in dev/demo environments.
    """
    return (
        "Thanks for reaching out! Based on your request, here are a few steps you can try. "
        "If the issue continues, I can connect you with a human support agent."
    )


def call_bedrock(prompt):
    """
    Placeholder for Amazon Bedrock integration.
    Intentionally disabled to control costs.
    """
    raise NotImplementedError("Bedrock integration disabled for cost control")


# -------------------------
# SNS escalation (HARDENED)
# -------------------------
def notify_human(user_id, message, reason):
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not set; skipping notification")
        return

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Customer Support Escalation",
            Message=(
                f"User ID: {user_id}\n"
                f"Reason: {reason}\n"
                f"Message: {message}"
            )
        )
    except Exception:
        logger.exception("Failed to publish SNS notification")


# -------------------------
# DynamoDB helpers
# -------------------------
def get_recent_messages(user_id, limit=6):
    response = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,
        Limit=limit
    )
    return response.get("Items", [])


def save_message(user_id, role, message):
    table.put_item(
        Item={
            "userId": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "message": message
        }
    )


# -------------------------
# HTTP response helper
# -------------------------
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
