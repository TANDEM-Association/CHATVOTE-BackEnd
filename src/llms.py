# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import logging
import os
from typing import AsyncIterator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages.base import BaseMessage, BaseMessageChunk
from pydantic import BaseModel
from src.firebase_service import awrite_llm_status
from src.models.general import LLM, LLMSize
from src.utils import load_env, safe_load_api_key

load_env()

logger = logging.getLogger(__name__)


CAPACITY_GEMINI_2_FLASH = 108
CAPACITY_GPT_4O_OPENAI_TIER_5 = 3759
CAPACITY_GPT_4O_AZURE = 112
CAPACITY_GPT_4O_MINI_OPENAI_TIER_5 = 4054
CAPACITY_GPT_4O_MINI_AZURE = 108
CAPACITY_CLAUDE_SONNET = 50
CAPACITY_CLAUDE_HAIKU = 100


azure_gpt_4o = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name="gpt-4o-2024-08-06",
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    api_key=safe_load_api_key("AZURE_OPENAI_API_KEY"),
    max_retries=0,
)

azure_gpt_4o_mini = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name="gpt-4o-mini-2024-07-18",
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    api_key=safe_load_api_key("AZURE_OPENAI_API_KEY"),
    max_retries=0,
)

google_gemini_2_flash = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=safe_load_api_key("GOOGLE_API_KEY"),
    max_retries=0,
)

openai_gpt_4o = ChatOpenAI(
    model="gpt-4o-2024-08-06",
    api_key=safe_load_api_key("OPENAI_API_KEY"),
    max_retries=0,
)

openai_gpt_4o_mini = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=safe_load_api_key("OPENAI_API_KEY"),
    max_retries=0,
)

# Anthropic Claude models (conditionally initialized)
_anthropic_api_key = safe_load_api_key("ANTHROPIC_API_KEY")

anthropic_claude_sonnet = (
    ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=_anthropic_api_key,
        max_retries=0,
    )
    if _anthropic_api_key
    else None
)

anthropic_claude_haiku = (
    ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        api_key=_anthropic_api_key,
        max_retries=0,
    )
    if _anthropic_api_key
    else None
)

_base_non_deterministic_llms: list[LLM] = [
    LLM(
        name="google-gemini-2.0-flash",
        model=google_gemini_2_flash,
        sizes=[LLMSize.SMALL, LLMSize.LARGE],
        priority=100,
        user_capacity_per_minute=CAPACITY_GEMINI_2_FLASH,
        is_at_rate_limit=False,
    ),
    LLM(
        name="azure-gpt-4o",
        model=azure_gpt_4o,
        sizes=[LLMSize.LARGE],
        priority=90,
        user_capacity_per_minute=CAPACITY_GPT_4O_AZURE,
        is_at_rate_limit=False,
        premium_only=True,
    ),
    LLM(
        name="openai-gpt-4o",
        model=openai_gpt_4o,
        sizes=[LLMSize.LARGE],
        priority=98,
        user_capacity_per_minute=CAPACITY_GPT_4O_OPENAI_TIER_5,
        is_at_rate_limit=False,
        premium_only=False,
    ),
    LLM(
        name="azure-gpt-4o-mini",
        model=azure_gpt_4o_mini,
        sizes=[LLMSize.SMALL],
        priority=50,
        user_capacity_per_minute=CAPACITY_GPT_4O_MINI_AZURE,
        is_at_rate_limit=False,
    ),
    LLM(
        name="openai-gpt-4o-mini",
        model=openai_gpt_4o_mini,
        sizes=[LLMSize.SMALL],
        priority=40,
        user_capacity_per_minute=CAPACITY_GPT_4O_MINI_OPENAI_TIER_5,
        is_at_rate_limit=False,
    ),
]

# Add Anthropic Claude models if API key is available
if anthropic_claude_sonnet is not None:
    _base_non_deterministic_llms.append(
        LLM(
            name="anthropic-claude-sonnet",
            model=anthropic_claude_sonnet,
            sizes=[LLMSize.LARGE],
            priority=95,
            user_capacity_per_minute=CAPACITY_CLAUDE_SONNET,
            is_at_rate_limit=False,
        )
    )

if anthropic_claude_haiku is not None:
    _base_non_deterministic_llms.append(
        LLM(
            name="anthropic-claude-haiku",
            model=anthropic_claude_haiku,
            sizes=[LLMSize.SMALL],
            priority=45,
            user_capacity_per_minute=CAPACITY_CLAUDE_HAIKU,
            is_at_rate_limit=False,
        )
    )

NON_DETERMINISTIC_LLMS: list[LLM] = _base_non_deterministic_llms

azure_gpt_4o_mini_det = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name="gpt-4o-mini-2024-07-18",
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    api_key=safe_load_api_key("AZURE_OPENAI_API_KEY"),
    temperature=0.0,
    max_retries=0,
)

google_gemini_2_flash_det = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=safe_load_api_key("GOOGLE_API_KEY"),
    temperature=0.0,
    max_retries=0,
)


openai_gpt_4o_mini_det = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=safe_load_api_key("OPENAI_API_KEY"),
    temperature=0.0,
    max_retries=0,
)

# Anthropic Claude deterministic models (conditionally initialized)
anthropic_claude_sonnet_det = (
    ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=_anthropic_api_key,
        temperature=0.0,
        max_retries=0,
    )
    if _anthropic_api_key
    else None
)

anthropic_claude_haiku_det = (
    ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        api_key=_anthropic_api_key,
        temperature=0.0,
        max_retries=0,
    )
    if _anthropic_api_key
    else None
)

_base_deterministic_llms: list[LLM] = [
    LLM(
        name="google-gemini-2.0-flash-det",
        model=google_gemini_2_flash_det,
        sizes=[LLMSize.SMALL, LLMSize.LARGE],
        priority=100,
        user_capacity_per_minute=CAPACITY_GEMINI_2_FLASH,
        is_at_rate_limit=False,
    ),
    LLM(
        name="azure-gpt-4o-mini-det",
        model=azure_gpt_4o_mini_det,
        sizes=[LLMSize.SMALL],
        priority=90,
        user_capacity_per_minute=CAPACITY_GPT_4O_MINI_AZURE,
        is_at_rate_limit=False,
    ),
    LLM(
        name="openai-gpt-4o-mini-det",
        model=openai_gpt_4o_mini_det,
        sizes=[LLMSize.SMALL],
        priority=80,
        user_capacity_per_minute=CAPACITY_GPT_4O_MINI_OPENAI_TIER_5,
        is_at_rate_limit=False,
    ),
]

# Add Anthropic Claude deterministic models if API key is available
if anthropic_claude_sonnet_det is not None:
    _base_deterministic_llms.append(
        LLM(
            name="anthropic-claude-sonnet-det",
            model=anthropic_claude_sonnet_det,
            sizes=[LLMSize.LARGE],
            priority=95,
            user_capacity_per_minute=CAPACITY_CLAUDE_SONNET,
            is_at_rate_limit=False,
        )
    )

if anthropic_claude_haiku_det is not None:
    _base_deterministic_llms.append(
        LLM(
            name="anthropic-claude-haiku-det",
            model=anthropic_claude_haiku_det,
            sizes=[LLMSize.SMALL],
            priority=85,
            user_capacity_per_minute=CAPACITY_CLAUDE_HAIKU,
            is_at_rate_limit=False,
        )
    )

DETERMINISTIC_LLMS: list[LLM] = _base_deterministic_llms


async def handle_rate_limit_hit_for_all_llms():
    await awrite_llm_status(is_at_rate_limit=True)


async def get_answer_from_llms(
    llms: list[LLM], messages: list[BaseMessage]
) -> BaseMessage:
    llms = sorted(llms, key=lambda x: x.priority, reverse=True)
    back_up_llms = [llm for llm in llms if llm.back_up_only]
    llms = [llm for llm in llms if not llm.back_up_only]
    for llm in llms:
        try:
            logger.debug(f"Invoking LLM {llm.name}...")
            response = await llm.model.ainvoke(messages)
            llm.is_at_rate_limit = False
            return response
        except Exception as e:
            logger.warning(f"Error invoking LLM {llm.name}: {e}")
            llm.is_at_rate_limit = True
            continue

    await handle_rate_limit_hit_for_all_llms()

    for llm in back_up_llms:
        try:
            logger.debug(f"Invoking LLM {llm.name}...")
            response = await llm.model.ainvoke(messages)
            llm.is_at_rate_limit = False
            return response
        except Exception as e:
            logger.warning(f"Error invoking LLM {llm.name}: {e}")
            llm.is_at_rate_limit = True
    raise Exception("All LLMs are at rate limit.")


async def get_structured_output_from_llms(
    llms: list[LLM], messages: list[BaseMessage], schema: dict | type
) -> dict | BaseModel:
    llms = sorted(llms, key=lambda x: x.priority, reverse=True)
    back_up_llms = [llm for llm in llms if llm.back_up_only]
    llms = [llm for llm in llms if not llm.back_up_only]
    for llm in llms:
        try:
            logger.debug(f"Invoking LLM {llm.name}...")
            prepared_model = llm.model.with_structured_output(schema)
            response = await prepared_model.ainvoke(messages)
            llm.is_at_rate_limit = False
            return response
        except Exception as e:
            logger.warning(f"Error invoking LLM {llm.name}: {e}")
            llm.is_at_rate_limit = True
            # TODO: consider writing to Firestore that this LLM now is at rate limit
            continue

    await handle_rate_limit_hit_for_all_llms()

    for llm in back_up_llms:
        try:
            logger.debug(f"Invoking LLM {llm.name}...")
            prepared_model = llm.model.with_structured_output(schema)
            response = await prepared_model.ainvoke(messages)
            llm.is_at_rate_limit = False
            return response
        except Exception as e:
            logger.warning(f"Error invoking LLM {llm.name}: {e}")
            llm.is_at_rate_limit = True
    raise Exception("All LLMs are at rate limit.")


async def stream_answer_from_llms(
    llms: list[LLM],
    messages: list[BaseMessage],
    preferred_llm_size: LLMSize = LLMSize.LARGE,
    use_premium_llms: bool = False,
) -> AsyncIterator[BaseMessageChunk]:
    logger.debug(f"Preferred LLM size: {preferred_llm_size}")
    if not use_premium_llms:
        llms = [llm for llm in llms if not llm.premium_only]
    if preferred_llm_size == LLMSize.LARGE:
        large_llms = [llm for llm in llms if LLMSize.LARGE in llm.sizes]
        small_llms = [
            llm
            for llm in llms
            if LLMSize.SMALL in llm.sizes and LLMSize.LARGE not in llm.sizes
        ]
        large_llms = sorted(large_llms, key=lambda x: x.priority, reverse=True)
        small_llms = sorted(small_llms, key=lambda x: x.priority, reverse=True)
        llms = large_llms + small_llms
    elif preferred_llm_size == LLMSize.SMALL:
        small_llms = [llm for llm in llms if LLMSize.SMALL in llm.sizes]
        large_llms = [
            llm
            for llm in llms
            if LLMSize.LARGE in llm.sizes and LLMSize.SMALL not in llm.sizes
        ]
        large_llms = sorted(large_llms, key=lambda x: x.priority, reverse=True)
        small_llms = sorted(small_llms, key=lambda x: x.priority, reverse=True)
        llms = small_llms + large_llms
    else:
        raise ValueError(f"Invalid preferred LLM size: {preferred_llm_size}")
    for llm in llms:
        try:
            logger.debug(f"Invoking LLM {llm.name}...")
            response = llm.model.astream(messages)
            llm.is_at_rate_limit = False
            return response
        except Exception as e:
            logger.warning(f"Error invoking LLM {llm.name}: {e}")
            llm.is_at_rate_limit = True
            continue

    return await handle_rate_limit_hit_for_all_llms()
