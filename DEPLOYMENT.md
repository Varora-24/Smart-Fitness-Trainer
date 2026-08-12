# Arogya Vision Deployment Documentation

## Recommended Architecture
For this MVP, we decouple the frontend, FastAPI backend, and legacy Streamlit WebRTC features into optimized execution environments:

```text
                    ┌──────────────────┐
                    │     Vercel       │
                    │ Next.js Frontend │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Render/Railway  │
                    │ FastAPI Container│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Existing Python  │
                    │   CV / ML Core   │
                    └──────────────────┘

                    ┌──────────────────┐
                    │  Render/Railway  │
                    │  Streamlit App   │
                    │ (Separate Cont.) │
                    └──────────────────┘
```

## Required Environment Variables
### Frontend (Next.js)
- `NEXT_PUBLIC_API_BASE_URL`: Full URL of the FastAPI production service.

### Backend (FastAPI & Streamlit)
- `CORS_ORIGINS`: Comma-separated list of permitted frontend URLs (e.g., `https://my-app.vercel.app`).
- (Plus any Supabase / PostgreSQL strings expected by the `core.data` implementation).

## Build & Startup Commands
### Next.js Frontend (Vercel Node.js target)
- **Build:** `npm ci && npm run build`
- **Start:** `npm start`

### FastAPI Backend (Docker Container)
- **Build:** `docker build -f Dockerfile.api -t arogya-api .`
- **Start:** `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`

### Streamlit (Docker Container)
- **Start:** `streamlit run main.py --server.address 0.0.0.0 --server.port $PORT`

## Resource & Configuration Considerations
### CPU / RAM
Processing 30 FPS video via XNNPACK/MediaPipe is heavily CPU-bound. Deploy the FastAPI container on a plan with at least **1-2 Dedicated vCPUs** and **1GB+ RAM**. GPU acceleration is not required.

### Upload Limits
The FastAPI endpoint is configured to safely enforce a 100MB maximum file size limit. Your reverse-proxy (e.g., Nginx, Cloudflare, or Render load balancers) must explicitly support a 100MB body upload limit (`client_max_body_size 100M`).

### Reverse-Proxy Timeouts
Processing a large video may take over 30 seconds. Ensure the chosen platform permits long-running HTTP connections before dropping the connection with a 504 Gateway Timeout.

### Temporary File Behavior
Videos are uploaded directly into memory and safely flushed to ephemeral storage (`tempfile.NamedTemporaryFile`) on the container. Persistence is not required for processing.

### Concurrency Note
The FastAPI video-analysis endpoint executes completely synchronously. While it is executed on FastAPI's underlying Starlette background threadpool to prevent ASGI event loop starvation, it still consumes finite CPU and thread pool capacity. If concurrent video-analysis traffic becomes heavy, a future architecture may require offloading this to an asynchronous background worker (e.g., Celery/Redis job queue).

## Known MVP Limitations
- **Development User ID:** A static ID (`dev-test-user-123`) is hardcoded because full authentication and multi-tenant per-user isolation are explicitly out of scope for this migration phase.
- **Live Trainer & Yoga WebRTC:** Live camera functionality heavily couples with `streamlit-webrtc`. These remain correctly routed to the legacy Streamlit platform for this phase, as porting them to Next.js requires a different signaling architecture.

## MANUAL DEPLOYMENT CHECKLIST
### Vercel
- create/login to Vercel
- import repository
- select frontend directory
- configure build settings if necessary
- set NEXT_PUBLIC_API_BASE_URL after backend deployment
- deploy
- record frontend URL

### Backend
- create Render/Railway/AWS/container service
- select Docker deployment
- use Dockerfile.api
- configure environment variables
- configure CPU/RAM appropriately
- deploy
- record backend URL
- verify `/health`

### CORS
- set CORS_ORIGINS to the actual production frontend origin
- redeploy/restart backend
- verify browser requests from frontend succeed

### Database
- configure required production database/Supabase variables
- never commit credentials

### Streamlit
- deploy separately
- configure WebRTC/STUN/TURN if required
- verify camera functionality over HTTPS/public internet

### Final Smoke Test
Verify:
- frontend homepage
- History
- Nutrition
- Supplements
- Video Analysis
- Live Trainer placeholder
- Yoga placeholder
- backend `/health`
- backend CORS
- actual video upload
- database-backed data
- Streamlit Live Trainer
