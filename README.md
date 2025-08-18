# Duotopia

AI-powered English learning platform for K-12 students.

## Project Structure

```
duotopia/
├── frontend/        # Vite + React + TypeScript frontend
├── backend/         # Python + FastAPI server
├── shared/          # Shared types and utilities
├── .env.example     # Environment variables template
└── package.json     # Monorepo root package
```

## Prerequisites

- Node.js 18+
- PostgreSQL 14+
- Google Cloud Platform account (project ID: duotopia-469413)
- Google OAuth 2.0 credentials

## Setup

1. Clone and install dependencies:
```bash
cd duotopia
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Configure your `.env` file with actual values

4. Set up PostgreSQL database

5. Run development servers:
```bash
npm run dev
```

## Architecture

- **Frontend**: Vite + React 18 + TypeScript + Tailwind CSS
- **Backend**: Python + FastAPI + SQLAlchemy ORM
- **Database**: PostgreSQL on Google Cloud SQL
- **Storage**: Google Cloud Storage for audio files
- **Authentication**: Google OAuth 2.0 for teachers, custom auth for students
- **AI**: OpenAI API for speech analysis

## Development

- Frontend runs on http://localhost:5173
- Backend API runs on http://localhost:3000
- API documentation at http://localhost:3000/api-docs