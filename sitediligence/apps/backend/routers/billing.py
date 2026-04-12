"""Billing router — Stripe subscriptions and webhook handling."""

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter()


@router.get("/plans")
async def list_plans():
    return {
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "features": ["3 projects", "1 user"]},
            {"id": "pro", "name": "Pro", "price": 4900, "features": ["Unlimited projects", "5 users"]},
            {"id": "enterprise", "name": "Enterprise", "price": None, "features": ["Custom"]},
        ]
    }


@router.post("/checkout")
async def create_checkout_session(plan_id: str):
    # TODO: create Stripe Checkout Session
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/portal")
async def create_billing_portal():
    # TODO: create Stripe Customer Portal session
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    # TODO: verify Stripe signature, handle subscription events
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/subscription")
async def get_subscription():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
