"""Supabase persistence layer.

Holds a single lazily-created Supabase client and the closet CRUD used by the
API. Degrades to None when credentials are absent so local/dev runs and tests
never hard-fail — callers treat a None client as "persistence disabled".

Required environment variables (set in .env locally, and in Vercel project
settings for production):

    SUPABASE_URL           https://<project>.supabase.co
    SUPABASE_SERVICE_KEY   service-role key (server-side only, never shipped to the browser)
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

_CLIENT = None  # None = unresolved; False = resolved-but-not-configured


def get_client():
    """Return a cached Supabase client, or None if not configured."""
    global _CLIENT
    if _CLIENT is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not (url and key):
            _CLIENT = False
        else:
            from supabase import create_client

            _CLIENT = create_client(url, key)
    return _CLIENT or None


def add_closet_item(
    user_id: str,
    category: str,
    image_url: str,
    tags: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
) -> Optional[Dict[str, object]]:
    """Insert one garment into a user's closet. Returns the row, or None if disabled."""
    client = get_client()
    if not client:
        return None
    row = {
        "user_id": user_id,
        "category": category,
        "image_url": image_url,
        "tags": tags or [],
        "colors": colors or [],
    }
    result = client.table("closet_items").insert(row).execute()
    return result.data[0] if result.data else None


def list_closet_items(user_id: str) -> List[Dict[str, object]]:
    """Return all closet items for a user (empty list if persistence disabled)."""
    client = get_client()
    if not client:
        return []
    result = (
        client.table("closet_items")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def delete_closet_item(user_id: str, item_id: str) -> bool:
    """Delete one closet item owned by the user. Returns True if a row was removed."""
    client = get_client()
    if not client:
        return False
    result = (
        client.table("closet_items")
        .delete()
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(result.data)
