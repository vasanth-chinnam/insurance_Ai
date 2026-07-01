from pydantic import BaseModel, Field
from typing import Optional, Any


class AutomationRequest(BaseModel):
    message:        str   = Field(..., description="Natural language user message")
    insurance_type: Optional[str] = None   # override if known
    policy_number:  Optional[str] = None   # override if known
    context:        Optional[dict] = None  # any extra data


class AgentResult(BaseModel):
    agent_name:  str
    status:      str        # "success" | "skipped" | "failed"
    duration_ms: int
    summary:     str        # one-line summary of what the agent found
    data:        Optional[Any] = None


class AutomationResponse(BaseModel):
    user_message:    str
    intent:          str        # detected intent
    insurance_type:  str
    agents_run:      list[AgentResult]
    policy_context:  Optional[str] = None
    claim_result:    Optional[dict] = None
    fraud_result:    Optional[dict] = None
    risk_result:     Optional[dict] = None
    renewal_result:  Optional[dict] = None
    final_report:    str
    next_steps:      list[str]
    total_time_ms:   int
    confidence:      str
    degraded:        bool
