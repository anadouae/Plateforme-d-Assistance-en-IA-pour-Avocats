"""Backward-compatible re-exports — prefer app.services.local_llm."""

from app.services.local_llm import (  # noqa: F401
    SYSTEM_PROMPT,
    generate_from_sources,
    generate_from_sources_sync,
    generate_stream_chunks,
    generate_synthesis_text,
    generate_case_analysis_text,
    generate_with_prompt,
    llm_health,
)
