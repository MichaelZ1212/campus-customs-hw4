"""PydanticAI configuration for the Campus Customs shopping assistant."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import time
from typing import Any
from uuid import uuid4

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext, capture_run_messages
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

try:
    from .audit import append_events, preview, utc_now
    from .models import ChatApiResponse, ChatMessage, ChatResponse
    from .tools import check_size_inventory, get_product_cards_by_ids, get_product_details, search_products
except ImportError:  # Supports `uvicorn main:app` from inside backend/.
    from audit import append_events, preview, utc_now
    from models import ChatApiResponse, ChatMessage, ChatResponse
    from tools import check_size_inventory, get_product_cards_by_ids, get_product_details, search_products


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"
AGENT_TOOLS = [search_products, get_product_details, check_size_inventory]
TOOL_NAMES = {tool.__name__ for tool in AGENT_TOOLS}
HISTORY_MESSAGES_IN_PROMPT = 10
# Loop limits for one chat turn: model requests (each tool round trip is one request) and function-tool calls.
AGENT_USAGE_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=6)


def configured_model() -> tuple[str, bool]:
    """Return the model name and whether it is reached through the Portkey gateway."""
    use_portkey = not os.getenv("OPENAI_API_KEY") and bool(os.getenv("PORTKEY_API_KEY"))
    default = "gpt-5.6-luna" if use_portkey else "gpt-5.2"
    return os.getenv("CAMPUS_CUSTOMS_AI_MODEL", default), use_portkey


@dataclass
class AgentDependencies:
    user_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    page_path: str = "/"
    product_id: str | None = None


@lru_cache(maxsize=1)
def get_agent() -> Agent[AgentDependencies, ChatResponse]:
    """Build lazily so non-AI endpoints still start when no API key is set."""
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    # A direct OpenAI key takes precedence; Portkey is only the fallback.
    model_name, use_portkey = configured_model()
    if use_portkey:
        portkey_key = os.environ["PORTKEY_API_KEY"]
        client = AsyncOpenAI(
            api_key=portkey_key,
            base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            default_headers={"x-portkey-api-key": portkey_key, "x-portkey-provider": "openai"},
            timeout=90.0,
        )
        model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
    else:
        model = f"openai-responses:{model_name}"
    agent = Agent(
        model,
        deps_type=AgentDependencies,
        output_type=ChatResponse,
        system_prompt=system_prompt,
        tools=AGENT_TOOLS,
    )

    @agent.instructions
    def request_context(ctx: RunContext[AgentDependencies]) -> str:
        deps = ctx.deps
        customer = (
            f"Authenticated customer: {deps.customer_name} ({deps.customer_email}), internal user ID {deps.user_id}."
            if deps.user_id is not None
            else "The shopper is a guest. Do not assume an identity or claim their chat will be saved."
        )
        product = (
            f"The shopper is viewing product ID '{deps.product_id}'. Resolve words such as 'this', 'it', or 'this item' to that product and use a product database tool before stating facts."
            if deps.product_id
            else "No specific product is identified by the current page. Ask for clarification when a reference such as 'this' is ambiguous."
        )
        return f"Current request context:\n- {customer}\n- Page path: {deps.page_path}\n- {product}"

    return agent


def _tool_call_events(run_id: str, messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """One audit event per function-tool call, paired with its result or retry by tool_call_id."""
    outcomes: dict[str, ToolReturnPart | RetryPromptPart] = {}
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, (ToolReturnPart, RetryPromptPart)) and part.tool_call_id:
                    outcomes[part.tool_call_id] = part
    events = []
    for message in messages:
        if not isinstance(message, ModelResponse):
            continue
        for part in message.parts:
            if not isinstance(part, ToolCallPart) or part.tool_name not in TOOL_NAMES:
                continue  # Skips PydanticAI's internal `final_result` output tool.
            outcome = outcomes.get(part.tool_call_id)
            events.append({
                "timestamp": message.timestamp.isoformat(timespec="milliseconds"),
                "event": "tool_call",
                "run_id": run_id,
                "tool": part.tool_name,
                "arguments": preview(part.args_as_dict()),
                "status": "ok" if isinstance(outcome, ToolReturnPart) else "retry" if outcome else "no_result",
                "result": preview(outcome.content) if outcome else None,
            })
    return events


def _model_finish_reason(messages: list[ModelMessage]) -> str | None:
    responses = [message for message in messages if isinstance(message, ModelResponse)]
    return responses[-1].finish_reason if responses else None


async def chat(message: str, history: list[ChatMessage], deps: AgentDependencies) -> ChatApiResponse:
    history_text = "\n".join(f"{item.role.title()}: {item.content}" for item in history[-HISTORY_MESSAGES_IN_PROMPT:])
    prompt = f"Conversation so far:\n{history_text}\n\nUser: {message}" if history_text else message
    run_id = uuid4().hex[:12]
    started = time.perf_counter()
    events: list[dict[str, Any]] = [{
        "timestamp": utc_now(),
        "event": "agent_run_started",
        "run_id": run_id,
        "model": configured_model()[0],
        "shopper": f"user:{deps.user_id}" if deps.user_id is not None else "guest",
        "page_path": deps.page_path,
        "product_id": deps.product_id,
        "history_messages": min(len(history), HISTORY_MESSAGES_IN_PROMPT),
        "message": preview(message, 200),
    }]

    def finish(stop_reason: str, messages: list[ModelMessage], **details: Any) -> None:
        events.extend(_tool_call_events(run_id, messages))
        events.append({
            "timestamp": utc_now(),
            "event": "agent_run_finished",
            "run_id": run_id,
            "stop_reason": stop_reason,
            "model_finish_reason": _model_finish_reason(messages),
            "duration_ms": round((time.perf_counter() - started) * 1000),
            **details,
        })
        append_events(events)

    with capture_run_messages() as messages:
        try:
            result = await get_agent().run(prompt, deps=deps, usage_limits=AGENT_USAGE_LIMITS)
        except UsageLimitExceeded as error:
            finish("usage_limit_exceeded", messages, error=preview(str(error)))
            raise
        except Exception as error:
            finish("error", messages, error=type(error).__name__)
            raise

    verified_products = get_product_cards_by_ids([product.product_id for product in result.output.products])
    # Only catalogue searches update the page; single-product lookups stay in the chat panel.
    searched = any(
        isinstance(part, ToolCallPart) and part.tool_name == "search_products"
        for response in result.new_messages() if isinstance(response, ModelResponse)
        for part in response.parts
    )
    response = ChatApiResponse(
        message=result.output.message,
        products=verified_products,
        show_on_page=searched and bool(verified_products),
    )
    usage = result.usage
    finish(
        "final_result", result.new_messages(),
        usage={"requests": usage.requests, "tool_calls": usage.tool_calls,
               "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
        response=preview(response.message, 200),
        products_returned=[product.product_id for product in verified_products],
        show_on_page=response.show_on_page,
    )
    return response
