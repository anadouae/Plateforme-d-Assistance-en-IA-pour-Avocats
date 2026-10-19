import io
import logging
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)
_minio_client = None
_minio_bucket: str | None = None


class TransientStorageError(Exception):
    """Erreur réseau / MinIO temporaire — Celery peut retry."""


def _active_bucket() -> str:
    """Bucket réellement utilisable (celui avec lequel le client s'est connecté)."""
    return (_minio_bucket or settings.MINIO_BUCKET or "lexhub-documents").strip()


def _ensure_bucket(client, bucket: str) -> None:
    if not bucket:
        raise TransientStorageError("MINIO_BUCKET vide")
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("MinIO bucket créé: %s", bucket)
    except Exception as exc:
        # Course possible si créé en parallèle — re-vérifier
        try:
            if client.bucket_exists(bucket):
                return
        except Exception:
            pass
        raise TransientStorageError(f"Impossible de préparer le bucket MinIO « {bucket} »: {exc}") from exc


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
        # Fichier chiffré Fernet mais aucune clé → ne jamais traiter le ciphertext comme DOCX/PDF
        if data[:8].startswith(b"gAAAAA"):
            raise TransientStorageError(
                "Fichier chiffré mais ENCRYPTION_KEY absente sur ce service. "
                "Alignez la clé backend / celery-worker."
            )
        return data
    try:
        return fernet.decrypt(data)
    except InvalidToken:
        # Ne jamais renvoyer le ciphertext : python-docx lève BadZipFile sinon.
        if data[:8].startswith(b"gAAAAA"):
            logger.error(
                "ENCRYPTION_KEY mismatch — cannot decrypt stored file (Fernet token)"
            )
            raise TransientStorageError(
                "Clé de chiffrement incorrecte sur ce service (ENCRYPTION_KEY). "
                "Alignez la clé du worker Celery avec le backend."
            )
        return data


def assert_plaintext_file(content: bytes, *, filename: str = "") -> None:
    """Garantit que le contenu n'est pas un blob Fernet (évite BadZipFile opaque)."""
    if content[:8].startswith(b"gAAAAA"):
        raise TransientStorageError(
            "Contenu encore chiffré après lecture stockage — vérifiez ENCRYPTION_KEY."
        )
    name = (filename or "").lower()
    if name.endswith(".docx") and not content.startswith(b"PK"):
        raise ValueError(
            "Le fichier DOCX lu depuis le stockage est invalide (pas un ZIP). "
            "Réimportez le document après correction de la clé de chiffrement."
        )


def _build_minio_client(access_key: str, secret_key: str, bucket: str):
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
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=access_key,
        secret_key=secret_key,
        secure=settings.MINIO_SECURE,
        http_client=http_client,
    )
    # Valider les credentials (list_buckets) avant make_bucket
    client.list_buckets()
    _ensure_bucket(client, bucket)
    return client


def _get_minio():
    global _minio_client, _minio_bucket
    if not settings.USE_MINIO:
        return None
    if _minio_client is None:
        preferred = (settings.MINIO_BUCKET or "lexhub-documents").strip()
        creds_to_try = [
            (settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY, preferred),
            ("sanad_minio", "sanad_minio_secret", preferred),
            ("sanad_minio", "sanad_minio_secret", "sanad-documents"),
            ("lexhub_minio", "lexhub_minio_secret", preferred),
            ("lexhub_minio", "lexhub_minio_secret", "lexhub-documents"),
        ]
        # Remove duplicate tuples while preserving order
        seen = set()
        unique_creds = []
        for c in creds_to_try:
            if c not in seen:
                seen.add(c)
                unique_creds.append(c)

        last_exc = None
        for ak, sk, bkt in unique_creds:
            try:
                _minio_client = _build_minio_client(ak, sk, bkt)
                _minio_bucket = bkt
                logger.info("MinIO connected successfully (key: %s, bucket: %s)", ak, bkt)
                break
            except Exception as exc:
                last_exc = exc
                logger.warning("MinIO creds failed for key=%s bucket=%s: %s", ak, bkt, exc)
                continue

        if _minio_client is None:
            logger.warning("MinIO unavailable (%s), using local storage", last_exc)
            return None
    else:
        # Client déjà en cache : garantir le bucket actif avant write
        try:
            _ensure_bucket(_minio_client, _active_bucket())
        except Exception as exc:
            logger.warning("MinIO ensure bucket failed, reset client: %s", exc)
            _minio_client = None
            _minio_bucket = None
            return _get_minio()
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
        bucket = _active_bucket()
        try:
            _ensure_bucket(client, bucket)
            client.put_object(
                bucket,
                key,
                io.BytesIO(encrypted),
                length=len(encrypted),
            )
        except TransientStorageError:
            raise
        except Exception as exc:
            # Credentials/bucket drift — reset client and retry once
            global _minio_client, _minio_bucket
            logger.error("MinIO put_object failed: %s — retry with fresh client", exc)
            _minio_client = None
            _minio_bucket = None
            client = _get_minio()
            if not client:
                raise TransientStorageError(str(exc)) from exc
            bucket = _active_bucket()
            try:
                _ensure_bucket(client, bucket)
                client.put_object(
                    bucket,
                    key,
                    io.BytesIO(encrypted),
                    length=len(encrypted),
                )
            except Exception as exc2:
                logger.error("MinIO put_object retry failed: %s", exc2)
                raise TransientStorageError(str(exc2)) from exc2
        return f"minio://{bucket}/{key}"

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
            err = str(exc)
            if "NoSuchKey" in err or "does not exist" in err.lower():
                raise FileNotFoundError(storage_path) from exc
            logger.error("MinIO get_object failed: %s", exc)
            raise TransientStorageError(err) from exc
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
