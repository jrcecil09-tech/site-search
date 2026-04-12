"""Autodesk Construction Cloud / BIM 360 integration."""

import httpx

APS_BASE_URL = "https://developer.api.autodesk.com"
APS_AUTH_URL = f"{APS_BASE_URL}/authentication/v2/authorize"
APS_TOKEN_URL = f"{APS_BASE_URL}/authentication/v2/token"


async def exchange_code(code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            APS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def list_hubs(access_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{APS_BASE_URL}/project/v1/hubs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
