# AI-Ready Serverless Customer Support Platform (AWS)
<img width="850" height="1100" alt="image" src="https://github.com/user-attachments/assets/9bca493a-36d8-4b90-9c60-8dd71167ca21" />


A production-style, serverless backend for customer support conversations built on AWS.  
The system focuses on **infrastructure, safety, and escalation**, not just AI responses.

This project demonstrates how cloud engineers can design **AI-ready systems** with:
- conversation memory
- business rules & guardrails
- human escalation
- cost-controlled AI integration

---

## 🚀 High-Level Architecture

Client → API Gateway → Lambda → DynamoDB  
          ↘ CloudWatch Logs  
          ↘ SNS (Human Escalation)  
          ↘ AI Provider (Feature-Flagged)

---

## 🧩 Core Components

### API Gateway
- Public HTTPS endpoint (`/chat`)
- Handles incoming customer messages
- Routes requests to Lambda securely

---

### AWS Lambda
Acts as the **orchestration layer**:
- Parses and validates requests
- Applies business rules before AI
- Fetches and stores conversation history
- Decides whether to respond automatically or escalate
- Publishes escalation alerts via SNS
- Returns a consistent API response

---

### DynamoDB (Conversation Memory)
- Stores all user and assistant messages
- Enables multi-turn conversation context
- Schema:
  - `userId` (partition key)
  - `timestamp` (sort key)
  - `role` (`user` | `assistant`)
  - `message`

---

### Business Rules & Guardrails
Before any AI logic runs, messages are evaluated for:
- Forbidden topics (legal, medical, financial advice)
- Aggressive or abusive language

If a rule is triggered:
- AI is skipped
- The conversation is escalated to a human
- The customer still receives a safe response

---

### Human Escalation (Amazon SNS)
- When escalation is required, Lambda publishes an alert to SNS
- Email notifications are sent to support staff
- Escalation is **non-fatal**:
  - SNS failures do not impact customer responses
  - All failures are logged to CloudWatch

---

## 🧠 AI Integration (Feature-Flagged)

The system is designed to integrate with **Amazon Bedrock** for AI-generated responses using full conversation context and business rules.

To control cloud costs:
- The AI layer is **feature-flagged**
- In this environment, a **stubbed AI provider** is used
- Switching to Bedrock requires only an environment variable change

```text
AI_PROVIDER = stub | bedrock
