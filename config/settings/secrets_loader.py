"""GCP Secret Manager 에서 시크릿 로드. prod 환경 전용."""
import functools
import os


@functools.lru_cache(maxsize=None)
def get_secret(secret_id: str) -> str:
    """`projects/<P>/secrets/<ID>/versions/latest` 의 페이로드 반환."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT 환경변수 누락")

    # lazy import (dev 환경엔 라이브러리 없을 수 있음)
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    resp = client.access_secret_version(request={"name": name})
    return resp.payload.data.decode("utf-8")
