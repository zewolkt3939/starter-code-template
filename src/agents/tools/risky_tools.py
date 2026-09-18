"""Tools rủi ro — LUÔN đi qua Human-in-the-loop interrupt trước khi chạy.

Vì sao tồn tại: hành động có tác dụng phụ ngoài hệ thống (gửi email, xóa
dữ liệu, charge tiền...) không được phép tự chạy chỉ vì LLM "quyết định".
Graph route tool có tên trong RISKY_TOOL_NAMES qua node `human_review`
dùng interrupt() của LangGraph — user phê duyệt thì mới execute.
"""

from langchain_core.tools import tool

# Tập tool bắt buộc HITL — graph đọc set này để route (kiểu frozenset như
# BLOCKED_MODULES của team 010 VibeSchool: một hằng số duy nhất để audit).
RISKY_TOOL_NAMES: frozenset[str] = frozenset({"send_email"})


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """[RISKY — cần human approval] Gửi email cho người nhận.

    Đây là tool MÔ PHỎNG (demo HITL) — chỉ log, không gửi thật. Đội thay
    bằng SMTP/API thật nhưng GIỮ nguyên tên trong RISKY_TOOL_NAMES.

    Args:
        to: Địa chỉ email người nhận.
        subject: Tiêu đề email.
        body: Nội dung email.

    Returns:
        Xác nhận gửi (giả).
    """
    # Mô phỏng gửi — trong dự án thật đây là gọi SMTP / Resend / SES.
    return f"Email sent to {to!r} with subject {subject!r} ({len(body)} chars)"
