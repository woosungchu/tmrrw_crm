"""자동 배정 엔진 (v3 §11)."""
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Count, F, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.companies.models import AssignmentConfig
from apps.leads.models import TimelineEntry


def _in_window(config, now_local):
    """요일·시간대 조건 통과 여부."""
    if now_local.weekday() not in (config.weekdays or []):
        return False
    return config.time_start <= now_local.time() <= config.time_end


def _eligible_agents(company, today):
    """쿼터 여유가 있는 활성 상담사 queryset."""
    qs = User.objects.filter(
        company=company, role="agent", is_active=True,
    ).annotate(
        today_count=Count(
            "agent_leads",
            filter=Q(
                agent_leads__received_at__date=today,
                agent_leads__is_deleted=False,
            ),
        ),
    )
    return qs.filter(Q(daily_quota__isnull=True) | Q(today_count__lt=F("daily_quota")))


def _pick_round_robin(candidates_ordered, last_id):
    """last_id 이후 첫 agent. 없으면 처음으로 회귀."""
    agents = list(candidates_ordered)
    if not agents:
        return None
    if last_id is None:
        return agents[0]
    for a in agents:
        if a.id > last_id:
            return a
    return agents[0]


def _pick_weighted(candidates_ordered, cursor):
    """
    가중치 기반 stride 스케줄링.
    예: A=2, B=1, C=4 → 시퀀스 [A,A,B,C,C,C,C] 를 cursor 위치로 순환.
    weight=0 인 agent 는 시퀀스에서 제외 (다만 quota 초과 등 외부 필터에 걸렸으면 _eligible 단계에서 이미 빠짐).
    """
    expanded = []
    for a in candidates_ordered:
        weight = max(int(a.assignment_weight or 0), 0)
        for _ in range(weight):
            expanded.append(a)
    if not expanded:
        return None
    return expanded[cursor % len(expanded)]


@transaction.atomic
def auto_assign(lead):
    """
    리드 수신 직후 호출. 조건 충족 시 agent 배정 + TimelineEntry 기록.
    반환: 배정된 User 또는 None (배정 안 됨).
    """
    try:
        config = AssignmentConfig.objects.select_for_update().get(company=lead.company)
    except AssignmentConfig.DoesNotExist:
        return None

    if not config.auto_on:
        return None

    tz = ZoneInfo(lead.company.timezone or "Asia/Seoul")
    now_local = timezone.now().astimezone(tz)
    if not _in_window(config, now_local):
        return None

    candidates = _eligible_agents(lead.company, now_local.date())
    if not candidates.exists():
        return None

    if config.tie_breaker == "round_robin":
        ordered = candidates.order_by("id")
        chosen = _pick_round_robin(ordered, config.last_assigned_agent_id)
    elif config.tie_breaker == "weighted":
        ordered = candidates.order_by("id")
        chosen = _pick_weighted(ordered, config.weighted_cursor)
    else:  # least_loaded
        chosen = candidates.order_by("today_count", "id").first()

    if not chosen:
        return None

    lead.agent = chosen
    lead.assignment_type = "auto"
    lead.save(update_fields=["agent", "assignment_type", "updated_at"])

    config.last_assigned_agent = chosen
    if config.tie_breaker == "weighted":
        config.weighted_cursor = (config.weighted_cursor or 0) + 1
        config.save(update_fields=["last_assigned_agent", "weighted_cursor", "updated_at"])
    else:
        config.save(update_fields=["last_assigned_agent", "updated_at"])

    TimelineEntry.objects.create(
        lead=lead, type="assigned", actor=None,
        payload={
            "agent_id": chosen.id,
            "reason": "auto",
            "tie_breaker": config.tie_breaker,
        },
    )
    return chosen
