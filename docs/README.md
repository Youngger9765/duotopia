# Duotopia

![Test CI](https://github.com/duotopia/duotopia/workflows/Test%20CI/badge.svg)
![Deploy](https://github.com/duotopia/duotopia/workflows/Deploy%20to%20GCP/badge.svg)
[![Test Coverage](https://img.shields.io/badge/coverage-97.3%25-brightgreen)](./FINAL_TEST_REPORT.md)

AI-powered English learning platform for K-12 students.

## Project Structure

```
duotopia/
├── frontend/        # Vite + React + TypeScript frontend
├── backend/         # Python + FastAPI server
├── shared/          # Shared types and utilities
├── terraform/       # Infrastructure as Code
├── .github/         # CI/CD workflows
├── .env.example     # Environment variables template
└── package.json     # Monorepo root package
```

## Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Google Cloud Platform account (project ID: duotopia-469413)
- Google OAuth 2.0 credentials

## Setup

1. Clone and install dependencies:
```bash
cd duotopia
npm install
cd backend && pip install -r requirements.txt
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
- **Testing**: Vitest (Frontend) + Pytest (Backend)
- **CI/CD**: GitHub Actions

## Development

- Frontend runs on http://localhost:5173
- Backend API runs on http://localhost:8000
- API documentation at http://localhost:8000/docs

## Testing

Run the test suite:

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Test coverage
npm run test:coverage
```

- **Test Coverage**: 97.3% (72/74 tests passing)
- **Backend**: 21 tests, 100% passing
- **Frontend**: 53 tests, 96% passing

See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for detailed testing documentation.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **Test CI**: Runs on every push and PR
- **Deploy**: Automatically deploys to GCP on main branch

See [GITHUB_SETUP.md](./GITHUB_SETUP.md) for setup instructions.

## Documentation

- [Testing Guide](./TESTING_GUIDE.md) - How to run and write tests
- [Deployment Guide](./README_DEPLOYMENT.md) - GCP deployment instructions
- [Feature Verification](./FEATURE_VERIFICATION.md) - Feature testing checklist
- [GitHub Setup](./GITHUB_SETUP.md) - CI/CD configuration
- [Security](./SECURITY.md) - Security best practices

## License

This project is proprietary and confidential.