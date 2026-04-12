"""Procore integration — OAuth2 and project/document sync."""

import httpx

PROCORE_BASE_URL = "https://api.procore.com"
PROCORE_AUTH_URL = "https://login.procore.com/oauth/authorize"
PROCORE_TOKEN_URL = "https://login.procore.com/oauth/token"


async def exchange_code(code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            PROCORE_TOKEN_URL,
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


async def list_projects(access_token: str, company_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PROCORE_BASE_URL}/rest/v1.0/projects",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"company_id": company_id},
        )
        resp.raise_for_status()
        return resp.json()
