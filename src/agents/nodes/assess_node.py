"""Node `assess` — self-assessment + escape hatch chống loop vô hạn.

Vì sao tồn tại (good practice #5, team 011 CareerPulse): nếu LLM cứ trả
"action=tool" mãi thì graph cũ chạy vô hạn. Node này đếm mỗi vòng và là
ĐƯỜNG DUY NHẤT quay lại reason — nên mọi path đều bị kiểm soát:

  enough_data=True                 -> finalize (đủ dữ kiện)
  iteration >= max_iterations      -> finalize_with_partial (escape hatch)
  còn lại                          -> reason (vòng tiếp)
"""

from __future__ import annotations

import logging

from src.agents.state import AgentState

logger = logging.getLogger("ai20k.assess")


async def assess_node(state: AgentState) -> dict:
    count = state.get("iteration_count", 0) + 1
    max_iter = state.get("max_iterations", 8)
    logger.info(
        "assess — vòng %d/%d, enough_data=%s",
        count,
        max_iter,
        state.get("last_decision", {}).get("enough_data", False),
    )
    return {"iteration_count": count, "stage": "assess"}
