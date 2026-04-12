# SiteDiligence

A platform for site diligence, GIS analysis, and field observations.

## Monorepo Structure

```
sitediligence/
├── packages/
│   └── shared/          # Shared TypeScript types, constants, and utilities
├── apps/
│   ├── backend/         # FastAPI Python backend
│   ├── web-app/         # React frontend
│   ├── website/         # Next.js marketing site
│   ├── mobile/          # Expo React Native
│   ├── desktop/         # Electron
│   └── hosted-service/  # Hosted storage backend
├── infrastructure/      # Docker, CI/CD configs
├── pnpm-workspace.yaml
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- pnpm 9+
- Docker Desktop

## Getting Started

```bash
# Install dependencies
pnpm install

# Start the backend
pnpm dev:backend

# Start the web app
pnpm dev:web

# Start the marketing website
pnpm dev:website

# Start everything
pnpm dev:all
```

## Packages

### `@sitediligence/shared`

Shared TypeScript types, constants, and utilities used across all apps.
