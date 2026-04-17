"""Shared Azure OpenAI client for benchmark tasks and judge evaluations.

Includes retry on empty responses and structured logging for debugging.
"""

import logging
import time

from openai import AsyncAzureOpenAI

from bench.config import cfg

log = logging.getLogger("bench")

MAX_EMPTY_RETRIES = 2


def get_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=cfg.azure_endpoint,
        api_key=cfg.azure_api_key,
        api_version="2025-04-01-preview",
    )


async def call_llm(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str | None = None,
    max_tokens: int = 4000,
    label: str = "",
) -> str:
    """Call Azure OpenAI and return the text response.

    Retries up to MAX_EMPTY_RETRIES times if the model returns an empty response.
    Logs request/response details for debugging.
    """
    client = get_client()
    m = model or cfg.task_model
    is_gpt5 = m.startswith("gpt-5")

    params = {
        "model": m,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if is_gpt5:
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens
        params["temperature"] = 0.0

    tag = label or m
    prompt_preview = prompt[:150].replace("\n", " ")
    max_out = max_tokens
    log.info(
        f"[{tag}] Calling {m} | prompt: {len(prompt)} chars (~{len(prompt)//4} tokens) | "
        f"max_completion_tokens={max_out} | \"{prompt_preview}...\""
    )

    for attempt in range(1 + MAX_EMPTY_RETRIES):
        t0 = time.monotonic()
        resp = await client.chat.completions.create(**params)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        text = resp.choices[0].message.content or ""
        text = text.strip()

        usage = resp.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        finish_reason = resp.choices[0].finish_reason if resp.choices else "unknown"

        log.info(
            f"[{tag}] Response: {elapsed_ms}ms | "
            f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} | "
            f"finish_reason={finish_reason} | response_len={len(text)} chars"
        )

        if finish_reason == "length":
            log.error(
                f"[{tag}] TRUNCATED: output hit max_completion_tokens={max_out}. "
                f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens}. "
                f"Response is likely incomplete."
            )

        if finish_reason == "content_filter":
            log.error(f"[{tag}] CONTENT FILTERED: response blocked by safety filter")
            if attempt < MAX_EMPTY_RETRIES:
                log.warning(f"[{tag}] Content filtered (attempt {attempt + 1}), retrying...")
                continue
            return ""

        if prompt_tokens > 12000:
            log.warning(
                f"[{tag}] Large prompt: {prompt_tokens} tokens — may be near context window limit"
            )

        if text:
            if len(text) < 200:
                log.debug(f"[{tag}] Full response: {text}")
            else:
                log.debug(f"[{tag}] Response preview: {text[:200]}...")
            return text

        # Empty response — retry
        if attempt < MAX_EMPTY_RETRIES:
            log.warning(
                f"[{tag}] Empty response (attempt {attempt + 1}/{1 + MAX_EMPTY_RETRIES}), retrying..."
            )
        else:
            log.error(
                f"[{tag}] Empty response after {1 + MAX_EMPTY_RETRIES} attempts. "
                f"prompt_tokens={prompt_tokens}"
            )

    return ""
