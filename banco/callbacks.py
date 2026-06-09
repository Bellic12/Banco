import httpx
import logging

logger = logging.getLogger(__name__)


async def notify_airline(callback_url: str, success: bool, user_account_id: str) -> None:
    payload = {"success": success, "user_account_id": user_account_id}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=payload)
            response.raise_for_status()
            logger.info("Airline notified: %s", payload)
    except Exception as exc:
        logger.error("Failed to notify airline at %s: %s", callback_url, exc)
