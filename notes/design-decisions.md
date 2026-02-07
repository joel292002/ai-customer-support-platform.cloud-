# Design Decisions

This document explains the key architectural decisions behind the AI-Ready Customer Support Platform.

---

## Why Serverless (API Gateway + Lambda)?

Serverless allows the system to:
- Scale automatically with traffic
- Avoid idle infrastructure costs
- Keep operational complexity low

The request-driven nature of customer support fits naturally with Lambda’s execution model.

---

## Why DynamoDB for Conversation Memory?

DynamoDB was chosen because:
- Access patterns are simple and predictable
- Single-partition queries per user are fast
- No joins or complex transactions are required

This keeps latency low and costs predictable.

---

## Why Business Rules Before AI?

AI should not be the first line of defense.

Business rules are applied first to:
- Prevent unsafe responses
- Enforce compliance requirements
- Reduce unnecessary AI usage and cost

This mirrors real-world AI safety practices.

---

## Why Feature-Flagged AI?

The AI layer is implemented behind a feature flag to:
- Control cloud costs
- Separate development and production behavior
- Allow safe iteration on prompts and models

Switching to Amazon Bedrock in production requires only a configuration change.

---

## Why SNS for Escalation?

SNS provides:
- Decoupled alerting
- Multiple delivery options (email, SMS, HTTP, etc.)
- High reliability

Escalation notifications are treated as non-fatal side effects to preserve customer experience.

---

## Failure Isolation

External dependencies (AI, SNS) are isolated so failures:
- Do not break the API
- Are logged for observability
- Can be retried or handled asynchronously
