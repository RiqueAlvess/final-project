"""
Supabase Storage client utility.

Usage (future):
    from apps.core.storage import get_storage_client, upload_file, get_public_url

    url = upload_file("avatars/user-1.png", file_bytes, content_type="image/png")
"""

import logging
from functools import lru_cache
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_storage_client():
    """Return a Supabase client configured with the service role key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set to use storage."
        )
    from supabase import create_client, Client
    client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return client


def upload_file(
    path: str,
    file_data: bytes,
    content_type: str = "application/octet-stream",
    bucket: str | None = None,
    upsert: bool = True,
) -> str:
    """
    Upload a file to Supabase Storage and return its public URL.

    Args:
        path:         Storage path inside the bucket, e.g. "avatars/user-1.png"
        file_data:    Raw bytes of the file.
        content_type: MIME type, e.g. "image/png".
        bucket:       Bucket name (defaults to SUPABASE_STORAGE_BUCKET setting).
        upsert:       Overwrite if the file already exists.

    Returns:
        The public URL of the uploaded file.
    """
    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    client = get_storage_client()

    client.storage.from_(bucket).upload(
        path=path,
        file=file_data,
        file_options={"content-type": content_type, "upsert": str(upsert).lower()},
    )

    return get_public_url(path, bucket=bucket)


def get_public_url(path: str, bucket: str | None = None) -> str:
    """Return the public URL for a file already in Supabase Storage."""
    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    client = get_storage_client()
    return client.storage.from_(bucket).get_public_url(path)


def delete_file(path: str, bucket: str | None = None) -> None:
    """Delete a file from Supabase Storage."""
    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    client = get_storage_client()
    client.storage.from_(bucket).remove([path])
    logger.info(f"Deleted storage file: {bucket}/{path}")
