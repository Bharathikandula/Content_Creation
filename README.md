# Fashion Creator Agent

A web app for solo fashion Creators on Instagram. The Creator uploads an Outfit Photo and gets a ready-to-post Caption, an Outfit Description, Hashtags, shoppable Matching Suggestions on a Creator Page, and optionally a Script for a video voiceover.

## Features

- **Caption Generation**: AI-powered captions matching Creator's voice style
- **Outfit Description**: Structured breakdown of items, colors, fabrics, occasion
- **Hashtags**: Mix of broad and niche fashion hashtags
- **Matching Suggestions**: Up to 3 catalog products per item with affiliate links
- **Creator Page**: Public shop page for each post
- **Voiceover Script**: 15/30/45 second scripts for video content
- **Multi-language**: English, Hindi, Telugu, Tamil, Malayalam

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js / React (mobile-first)
- **Orchestration**: LangGraph
- **AI**: Gemini API (multimodal, JSON schema output)
- **Product Search**: SerpAPI Google Shopping
- **Affiliate Links**: Cuelinks API
- **Database**: PostgreSQL
- **Photo Storage**: S3-compatible (MinIO for local dev)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Quick Start with Docker

```bash
# Clone the repository
git clone <repo-url>
cd fashion-creator

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
# - GEMINI_API_KEY
# - SERPAPI_API_KEY
# - CUELINKS_API_KEY

# Start all services
docker-compose up -d

# Create database tables
docker-compose exec backend python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new Creator
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Posts
- `POST /api/v1/posts/` - Create new post
- `GET /api/v1/posts/` - List all posts
- `GET /api/v1/posts/{id}` - Get post details
- `POST /api/v1/posts/{id}/photo` - Upload outfit photo
- `POST /api/v1/posts/{id}/generate` - Generate content
- `POST /api/v1/posts/{id}/script` - Generate voiceover script

### Creator Pages
- `POST /api/v1/pages/` - Create creator page
- `GET /api/v1/pages/{slug}` - View creator page (public)

### Voice Samples
- `POST /api/v1/voice-samples/` - Add voice sample
- `GET /api/v1/voice-samples/` - List voice samples
- `DELETE /api/v1/voice-samples/{id}` - Delete voice sample

## Architecture

### LangGraph Pipeline

```
[START] → load_context → analyze_photo → write_caption
                                    → write_description
                                    → generate_hashtags
              ↓
         plan_queries → search_products → rank_candidates
              ↓
         (conditional) → resolve_links → assemble_post
              ↓
         write_script → (check length) → [END]
```

### Data Model

- **Creator**: User account with preferences
- **Post**: Single outfit post with all content
- **Photo**: Outfit photo (24h expiry)
- **CaptionVersion**: Generated caption versions
- **Product**: Catalog product from search
- **PostProduct**: Link between post and products
- **CreatorPage**: Public shop page
- **Script**: Voiceover script

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `SERPAPI_API_KEY` | SerpAPI key | - |
| `CUELINKS_API_KEY` | Cuelinks API key | - |
| `S3_ENDPOINT_URL` | S3 endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET_NAME` | S3 bucket name | `fashion-creator-photos` |
| `PHOTO_EXPIRY_HOURS` | Photo retention period | `24` |

## Build Order

1. **Phase 1**: Photo → Description, Caption, Hashtags (English + Hindi)
2. **Phase 2**: Catalog search, Matching Suggestions, Affiliate Links, Creator Page
3. **Phase 3**: Telugu, Tamil, Malayalam support
4. **Phase 4**: Hardening (retention jobs, quotas, monitoring)

## Open Items

- **Merchant URL**: SerpAPI Google Shopping results link to Google item pages. May need follow-up call for merchant URL.
- **SerpAPI India Coverage**: Confirm Indian results are good for fashion in all five languages.
- **Languages**: Telugu, Tamil, Malayalam may be weaker; test with native speakers.
- **Creator Page Photo Opt-in**: Confirm handling of photo retention for pages.
- **Sign-in**: Assumed email or Google sign-in.
- **Terms Review**: Check SerpAPI, Google, retailer, and Cuelinks terms.

## License

[Your License]

---

Built with ❤️ for fashion creators