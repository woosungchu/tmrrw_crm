"""
대시보드 집계 서비스.

StatsDaily 모델 없이 SQL aggregate 로 실시간 계산.
Phase 2 에서 양 늘면 캐시(5분 TTL) or StatsDaily 마이그레이션.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.leads.models import Lead
from apps.communications.models import Callback


def _scope_qs_for_user(user, company):
    qs = Lead.objects.filter(company=company, is_deleted=False)
    if user.role in ("owner", "admin"):
        return qs
    if user.role == "intake":
        return qs.filter(intake=user)
    if user.role == "agent":
        return qs.filter(agent=user)
    return qs.none()


def compute_dashboard(user, company) -> dict:
    """KPI · 추이 · 분포 · 최근 활동."""
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    week_ago = today - timedelta(days=6)  # 오늘 포함 7일

    scope = _scope_qs_for_user(user, company)

    # ── KPI 카드 ──
    today_start = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time()), tz,
    )
    today_qs = scope.filter(received_at__gte=today_start)

    kpi = {
        "today_new": today_qs.count(),
        "in_progress": scope.filter(status__in=["contacted", "qualified", "negotiating"]).count(),
        "won_this_week": scope.filter(
            status="won", closed_at__gte=today_start - timedelta(days=6),
        ).count(),
        "unassigned": scope.filter(agent__isnull=True, status="new").count(),
        "noti_failed": scope.filter(noti_status="failed").count(),
        "callbacks_pending": _callbacks_pending_for(user, company),
    }

    # ── 7일 일별 유입 ──
    daily = {(week_ago + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    rows = (
        scope.filter(received_at__date__gte=week_ago)
        .annotate(d=TruncDate("received_at"))
        .values("d").annotate(n=Count("id"))
    )
    for r in rows:
        if r["d"] is None:
            continue
        key = r["d"].isoformat()
        if key in daily:
            daily[key] = r["n"]
    daily_series = [{"date": k, "count": v} for k, v in sorted(daily.items())]

    # ── 상태 분포 (도넛) ──
    status_counts_map = {code: 0 for code, _ in Lead.STATUS_CHOICES}
    for r in scope.values("status").annotate(n=Count("id")):
        status_counts_map[r["status"]] = r["n"]
    status_dist = [
        {"code": c, "label": dict(Lead.STATUS_CHOICES)[c], "count": status_counts_map[c]}
        for c in ("new", "contacted", "qualified", "negotiating", "won", "lost")
    ]

    # ── 채널별 TOP 5 ──
    source_dist = list(
        scope.values("source__title")
        .annotate(n=Count("id"))
        .order_by("-n")[:5]
    )

    # ── 상담사별 현재 오픈 리드 (won/lost 제외) TOP 10 ──
    if user.role in ("owner", "admin"):
        agent_qs = scope.exclude(status__in=["won", "lost"]).filter(agent__isnull=False)
    else:
        agent_qs = scope.exclude(status__in=["won", "lost"])
    agent_dist = list(
        agent_qs.values("agent__name", "agent__login_id")
        .annotate(n=Count("id"))
        .order_by("-n")[:10]
    )

    # ── 최근 리드 10 ──
    recent_leads = scope.select_related("source", "agent").order_by("-received_at")[:10]

    return {
        "kpi": kpi,
        "daily_series": daily_series,
        "status_dist": status_dist,
        "source_dist": source_dist,
        "agent_dist": agent_dist,
        "recent_leads": recent_leads,
        "week_start": week_ago,
        "today": today,
    }


def _callbacks_pending_for(user, company) -> int:
    qs = Callback.objects.filter(company=company, status="pending")
    if user.role == "agent":
        qs = qs.filter(agent=user)
    elif user.role == "intake":
        qs = qs.filter(Q(agent=user) | Q(created_by=user))
    # owner/admin 은 전체
    return qs.count()
