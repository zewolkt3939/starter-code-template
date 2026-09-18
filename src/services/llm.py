"""Cascade LLM router — model rẻ cho việc rẻ, model mạnh cho việc mạnh.

Vì sao tồn tại: template cũ dùng MỘT model cho mọi việc — đội nào cũng
đốt gpt-4o để classify query (bài học cost-management + good practice
router 2 tầng). `get_llm(task_type)` là điểm duy nhất quyết định model:

- "classify": model rẻ (gpt-4o-mini) — reason node, routing, guardrail mềm
- "generate": model mạnh (gpt-4o) — sinh câu trả lời cuối
- "judge":    model KHÁC generator — tránh self-preference bias khi tự
              chấm điểm (bài học team 002 DevCoach: judge phải tách khỏi
              generator, nếu không eval sẽ tự khen chính nó)

Đổi model = đổi 1 dòng .env, không sửa code.
"""

from typing import Literal

from langchain_openai import ChatOpenAI

from src.config import get_settings

TaskType = Literal["classify", "generate", "judge"]

_TASK_TO_SETTING = {
    "classify": "model_classify",
    "generate": "model_generate",
    "judge": "model_judge",
}


def get_llm(task_type: TaskType = "generate") -> ChatOpenAI:
    """Trả về LLM phù hợp với loại task (cascade router).

    Args:
        task_type: "classify" | "generate" | "judge".

    Raises:
        ValueError: nếu cấu hình để judge trùng model generate — đánh mất
            tính khách quan của eval (fail loudly, không fallback im lặng).
    """
    settings = get_settings()

    if task_type == "judge" and settings.model_judge == settings.model_generate:
        raise ValueError(
            "MODEL_JUDGE phải khác MODEL_GENERATE — judge trùng generator "
            "gây self-preference bias (xem team 002 RCA về eval tự khen). "
            "Sửa MODEL_JUDGE trong .env."
        )

    model_name = getattr(settings, _TASK_TO_SETTING[task_type])
    # Judge cần temperature thấp để chấm điểm ổn định, không sáng tạo.
    temperature = 0.0 if task_type in ("classify", "judge") else settings.llm_temperature

    return ChatOpenAI(
        model=model_name,
        api_key=settings.openai_api_key,
        temperature=temperature,
    )
