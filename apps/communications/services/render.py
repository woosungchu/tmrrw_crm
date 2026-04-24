import re


_VAR_RE = re.compile(r"\{([\w.]+)\}")


def render_template_body(body: str, lead) -> str:
    """
    템플릿 본문의 `{name}`, `{phone}`, `{fields.키}` 를 lead 값으로 치환.
    알 수 없는 변수는 원문 그대로 유지.
    """
    ctx = {
        "name": getattr(lead, "name", "") or "",
        "phone": getattr(lead, "phone", "") or "",
    }
    fields = getattr(lead, "fields", {}) or {}
    # `fields.xxx` 와 `xxx` 양쪽 다 허용 (편의)
    for k, v in fields.items():
        ctx[f"fields.{k}"] = str(v)
        ctx.setdefault(k, str(v))

    def repl(m):
        key = m.group(1)
        return ctx.get(key, m.group(0))

    return _VAR_RE.sub(repl, body or "")
