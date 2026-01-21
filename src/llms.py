# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import logging
import os
from typing import AsyncIterator, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI
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


def _build_azure_chat_model(
    deployment_name: str, temperature: Optional[float] = None
) -> Optional[AzureChatOpenAI]:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("OPENAI_API_VERSION")
    api_key = safe_load_api_key("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_version or not api_key:
        logger.info(
            "Skipping Azure deployment '%s' because Azure env vars are not fully configured.",
            deployment_name,
        )
        return None
    kwargs = {
        "azure_endpoint": endpoint,
        "deployment_name": deployment_name,
        "openai_api_version": api_version,
        "api_key": api_key,
        "max_retries": 0,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return AzureChatOpenAI(**kwargs)


def _build_google_gemini_model(
    temperature: Optional[float] = None,
) -> Optional[ChatGoogleGenerativeAI]:
    api_key = safe_load_api_key("GOOGLE_API_KEY")
    if not api_key:
        logger.info("Skipping Google Gemini because GOOGLE_API_KEY is not configured.")
        return None
    kwargs = {
        "model": "gemini-2.0-flash",
        "api_key": api_key,
        "max_retries": 0,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatGoogleGenerativeAI(**kwargs)


def _build_llm(
    *,
    name: str,
    model,
    sizes: list[LLMSize],
    priority: int,
    user_capacity_per_minute: int,
    premium_only: bool = False,
) -> Optional[LLM]:
    if model is None:
        return None
    return LLM(
        name=name,
        model=model,
        sizes=sizes,
        priority=priority,
        user_capacity_per_minute=user_capacity_per_minute,
        is_at_rate_limit=False,
        premium_only=premium_only,
    )


def _filter_available_llms(llms: list[Optional[LLM]]) -> list[LLM]:
    return [llm for llm in llms if llm is not None]


azure_gpt_4o = _build_azure_chat_model("gpt-4o-2024-08-06")
azure_gpt_4o_mini = _build_azure_chat_model("gpt-4o-mini-2024-07-18")
azure_gpt_4o_mini_det = _build_azure_chat_model(
    "gpt-4o-mini-2024-07-18", temperature=0.0
)

google_gemini_2_flash = _build_google_gemini_model()
google_gemini_2_flash_det = _build_google_gemini_model(temperature=0.0)

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

openai_gpt_4o_mini_det = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=safe_load_api_key("OPENAI_API_KEY"),
    temperature=0.0,
    max_retries=0,
)

NON_DETERMINISTIC_LLMS: list[LLM] = _filter_available_llms(
    [
        _build_llm(
            name="google-gemini-2.0-flash",
            model=google_gemini_2_flash,
            sizes=[LLMSize.SMALL, LLMSize.LARGE],
            priority=100,
            user_capacity_per_minute=CAPACITY_GEMINI_2_FLASH,
        ),
        _build_llm(
            name="azure-gpt-4o",
            model=azure_gpt_4o,
            sizes=[LLMSize.LARGE],
            priority=90,
            user_capacity_per_minute=CAPACITY_GPT_4O_AZURE,
            premium_only=True,
        ),
        _build_llm(
            name="openai-gpt-4o",
            model=openai_gpt_4o,
            sizes=[LLMSize.LARGE],
            priority=98,
            user_capacity_per_minute=CAPACITY_GPT_4O_OPENAI_TIER_5,
        ),
        _build_llm(
            name="azure-gpt-4o-mini",
            model=azure_gpt_4o_mini,
            sizes=[LLMSize.SMALL],
            priority=50,
            user_capacity_per_minute=CAPACITY_GPT_4O_MINI_AZURE,
        ),
        _build_llm(
            name="openai-gpt-4o-mini",
            model=openai_gpt_4o_mini,
            sizes=[LLMSize.SMALL],
            priority=40,
            user_capacity_per_minute=CAPACITY_GPT_4O_MINI_OPENAI_TIER_5,
        ),
    ]
)

DETERMINISTIC_LLMS: list[LLM] = _filter_available_llms(
    [
        _build_llm(
            name="google-gemini-2.0-flash-det",
            model=google_gemini_2_flash_det,
            sizes=[LLMSize.SMALL, LLMSize.LARGE],
            priority=100,
            user_capacity_per_minute=CAPACITY_GEMINI_2_FLASH,
        ),
        _build_llm(
            name="azure-gpt-4o-mini-det",
            model=azure_gpt_4o_mini_det,
            sizes=[LLMSize.SMALL],
            priority=90,
            user_capacity_per_minute=CAPACITY_GPT_4O_MINI_AZURE,
        ),
        _build_llm(
            name="openai-gpt-4o-mini-det",
            model=openai_gpt_4o_mini_det,
            sizes=[LLMSize.SMALL],
            priority=80,
            user_capacity_per_minute=CAPACITY_GPT_4O_MINI_OPENAI_TIER_5,
        ),
    ]
)


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
