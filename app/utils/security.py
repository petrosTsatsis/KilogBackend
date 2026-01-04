import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from svix.webhooks import Webhook

from app.database import get_db
from app.schemas import UserCreate, UserUpdate
from app.services import user_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/clerk")
async def handle_clerk_webhook(
        request: Request,
        db: Session = Depends(get_db)
):
    webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("CLERK_WEBHOOK_SECRET is not set in environment")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # 1. Read & Verify Signature
    body = await request.body()
    payload = body.decode("utf-8")
    headers = dict(request.headers)

    try:
        wh = Webhook(webhook_secret)
        wh.verify(payload, headers)
    except Exception as e:
        logger.error(f"Invalid Clerk Webhook Signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Parse Event
    data = json.loads(payload)
    event_type = data.get("type")
    event_data = data.get("data", {})

    logger.info(f"Received Clerk Webhook: {event_type}")

    try:
        # --- CASE 1: USER CREATED ---
        if event_type == "user.created":
            clerk_id = event_data.get("id")
            email_addresses = event_data.get("email_addresses", [])
            email = email_addresses[0]["email_address"] if email_addresses else None

            # Smart Username: Clerk Username -> Email Prefix -> Fallback
            username = event_data.get("username")
            if not username and email:
                username = email.split("@")[0]

            if not email:
                logger.error(f"Skipping user {clerk_id}: No email found")
                return {"status": "error", "detail": "Missing email"}

            # Check if exists (Idempotency)
            if user_service.get_user_by_auth_id(db, clerk_id):
                logger.info(f"User {clerk_id} already exists. Skipping create.")
                return {"status": "ok"}

            internal_user = UserCreate(
                email=email,
                auth_id=clerk_id,
                username=username
            )
            user_service.create_user(db, internal_user)
            logger.info(f"Created user {email} from Clerk")

        # --- CASE 2: USER UPDATED ---
        elif event_type == "user.updated":
            clerk_id = event_data.get("id")
            user = user_service.get_user_by_auth_id(db, clerk_id)

            if user:
                # Update username if changed
                new_username = event_data.get("username")
                if new_username and new_username != user.username:
                    user_service.update_user(db, user.id, UserUpdate(username=new_username))
                    logger.info(f"Updated username for user {user.id}")
            else:
                logger.warning(f"Received update for unknown user {clerk_id}")

        # --- CASE 3: SESSION CREATED (LOGIN) ---
        elif event_type == "session.created":
            # Clerk sends "user_id" in the session object
            clerk_user_id = event_data.get("user_id")
            user = user_service.get_user_by_auth_id(db, clerk_user_id)

            if user:
                # Update last_login_at
                user_service.update_user(
                    db,
                    user.id,
                    UserUpdate(last_login_at=datetime.now(timezone.utc))
                )
                logger.info(f"Updated last_login_at for user {user.id}")
            else:
                # This can happen if the webhook for creation is slower than session creation
                logger.warning(f"Session started for unknown user {clerk_user_id}")

        # --- CASE 4: USER DELETED ---
        elif event_type == "user.deleted":
            clerk_id = event_data.get("id")
            user = user_service.get_user_by_auth_id(db, clerk_id)
            if user:
                user_service.delete_user(db, user.id)
                logger.info(f"Deleted user {user.id}")

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}")
        # Return 200 to Clerk so they don't retry endlessly on logic errors
        return {"status": "error", "detail": str(e)}

    return {"status": "success"}
