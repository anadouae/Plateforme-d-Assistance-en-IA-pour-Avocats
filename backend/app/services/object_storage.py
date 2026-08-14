import io
import logging
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)
_minio_client = None


class TransientStorageError(Exception):
    """Erreur réseau / MinIO temporaire — Celery peut retry."""


def _get_fernet() -> Fernet | None:
    if not settings.ENCRYPTION_KEY:
        return None
    try:
        return Fernet(settings.ENCRYPTION_KEY.encode())
    except Exception:
        return None


def _encrypt(data: bytes) -> bytes:
    fernet = _get_fernet()
    return fernet.encrypt(data) if fernet else data


def _decrypt(data: bytes) -> bytes:
    fernet = _get_fernet()
    if not fernet:
        return data
    try:
        return fernet.decrypt(data)
    except InvalidToken:
        return data


def _get_minio():
    global _minio_client
    if not settings.USE_MINIO:
        return None
    if _minio_client is None:
        try:
            import urllib3
            from minio import Minio

            timeout = float(settings.MINIO_TIMEOUT_SEC or 30)
            http_client = urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=min(10.0, timeout), read=timeout),
                retries=urllib3.Retry(
                    total=2,
                    backoff_factor=0.5,
                    status_forcelist=[500, 502, 503, 504],
                ),
            )
            _minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                http_client=http_client,
            )
            if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
                _minio_client.make_bucket(settings.MINIO_BUCKET)
        except Exception as exc:
            logger.warning("MinIO unavailable (%s), using local storage", exc)
            return None
    return _minio_client


def ensure_upload_dir(cabinet_id: str, case_id: str) -> Path:
    path = Path(settings.UPLOAD_DIR) / cabinet_id / case_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _object_key(cabinet_id: str, case_id: str, filename: str) -> str:
    return f"{cabinet_id}/{case_id}/{filename}"


def save_file(content: bytes, cabinet_id: str, case_id: str, extension: str) -> str:
    filename = f"{uuid.uuid4().hex}{extension}"
    encrypted = _encrypt(content)
    client = _get_minio()

    if client:
        key = _object_key(cabinet_id, case_id, filename)
        try:
            client.put_object(
                settings.MINIO_BUCKET,
                key,
                io.BytesIO(encrypted),
                length=len(encrypted),
            )
        except Exception as exc:
            logger.error("MinIO put_object failed: %s", exc)
            raise TransientStorageError(str(exc)) from exc
        return f"minio://{settings.MINIO_BUCKET}/{key}"

    directory = ensure_upload_dir(cabinet_id, case_id)
    filepath = directory / filename
    filepath.write_bytes(encrypted)
    return str(filepath)


def read_file(storage_path: str) -> bytes:
    if storage_path.startswith("minio://"):
        client = _get_minio()
        if not client:
            raise TransientStorageError("MinIO not available")
        _, rest = storage_path.split("minio://", 1)
        bucket, key = rest.split("/", 1)
        try:
            response = client.get_object(bucket, key)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
        except FileNotFoundError:
            raise
        except Exception as exc:
            logger.error("MinIO get_object failed: %s", exc)
            raise TransientStorageError(str(exc)) from exc
        return _decrypt(data)

    path = Path(storage_path)
    if not path.exists():
        raise FileNotFoundError(storage_path)
    data = path.read_bytes()
    return _decrypt(data)


def delete_file(storage_path: str) -> None:
    if storage_path.startswith("minio://"):
        client = _get_minio()
        if not client:
            return
        _, rest = storage_path.split("minio://", 1)
        bucket, key = rest.split("/", 1)
        try:
            client.remove_object(bucket, key)
        except Exception:
            pass
        return

    path = Path(storage_path)
    if path.exists():
        path.unlink()
