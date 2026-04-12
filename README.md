# SiteDiligence

A GIS-enabled site diligence platform for managing field observations, layers, and project data.

## Monorepo Structure

```
sitediligence/
├── packages/
│   └── shared/           # Shared TypeScript types, constants, and utilities
├── apps/
│   ├── backend/          # FastAPI Python backend
│   ├── web-app/          # React frontend (Vite)
│   ├── website/          # Next.js marketing site
│   ├── mobile/           # Expo React Native
│   ├── desktop/          # Electron desktop app
│   └── hosted-service/   # Hosted storage backend
├── infrastructure/       # Docker, CI/CD configs
├── pnpm-workspace.yaml
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- Node.js 18+
- pnpm 9+
- Python 3.11+
- Docker Desktop

## Getting Started

```bash
# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env

# Start individual services
pnpm dev:backend    # FastAPI backend
pnpm dev:web        # React web app
pnpm dev:website    # Next.js marketing site

# Start all apps in parallel
pnpm dev:all

# Start full stack with Docker
docker-compose up
```

## Packages

### `@sitediligence/shared`

Shared TypeScript types, constants, and utilities used across all apps.

```ts
import { Project, Site, GISLayer } from '@sitediligence/shared';
import { LAYER_COLORS, OBSERVATION_CATEGORIES } from '@sitediligence/shared';
import { toWGS84, featureFromBounds } from '@sitediligence/shared';
```
