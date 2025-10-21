# Port Configuration Changes

This document summarizes the port changes made to avoid conflicts with existing Docker containers.

## Port Conflicts Resolved

### 1. PostgreSQL Database
- **Conflict**: Port 5432 was used by `ai-plus-postgres-db` and port 5433 was used by `supabase-pooler`
- **Resolution**: Changed local-ai-packaged Postgres to use port **5434**
- **Files Modified**:
  - `.env`: `POSTGRES_PORT=5434`
  - `docker-compose.override.private.yml`: `127.0.0.1:5434:5432`
  - `supabase/docker/docker-compose.yml`: Updated pooler to use `${POSTGRES_PORT}`

### 2. Ollama Service
- **Conflict**: Port 11434 was used by `aiplus-ollama`
- **Resolution**: Changed local-ai-packaged Ollama to use port **11435**
- **Files Modified**:
  - `docker-compose.override.private.yml`: Changed all Ollama profiles to use `127.0.0.1:11435:11434`
- **Access**: Connect to local-ai-packaged Ollama at `http://localhost:11435`

### 3. Kong API Gateway
- **Conflict**: Ports 18000 and 18443 were already in use by running Supabase Kong
- **Resolution**: Changed local-ai-packaged Kong to use ports **19000** and **19443**
- **Files Modified**:
  - `.env`:
    - `KONG_HTTP_PORT=19000`
    - `KONG_HTTPS_PORT=19443`
    - `SUPABASE_PUBLIC_URL=http://localhost:19000`
    - `API_EXTERNAL_URL=http://localhost:19000`

### 4. Supabase Pooler Transaction Port
- **Conflict**: Port 6543 might conflict with other services
- **Resolution**: Changed to port **6544**
- **Files Modified**:
  - `.env`: `POOLER_PROXY_PORT_TRANSACTION=6544`

### 5. Open WebUI
- **Conflict**: Port 8080 was used by `searxng` container from existing environment
- **Resolution**: Changed local-ai-packaged Open WebUI to use port **8082**
- **Files Modified**:
  - `docker-compose.override.private.yml`: Changed to `127.0.0.1:8082:8080`
- **Access**: Connect to Open WebUI at `http://localhost:8082`

## Current Port Assignments

### Local AI Packaged Stack (This Project)
- **Postgres**: 5434 (127.0.0.1:5434 → 5432)
- **Ollama**: 11435 (127.0.0.1:11435 → 11434)
- **Kong HTTP**: 19000 (external) → 8000 (internal)
- **Kong HTTPS**: 19443 (external) → 8443 (internal)
- **Supabase Pooler**: 6544 (external) → 6543 (internal)
- **Open WebUI**: 8082 (127.0.0.1:8082 → 8080)
- **SearXNG**: 8081 (127.0.0.1:8081 → 8080)
- **Flowise**: 3001 (127.0.0.1:3001 → 3001)
- **n8n**: 5678 (127.0.0.1:5678 → 5678)
- **Langfuse Web**: 3000 (127.0.0.1:3000 → 3000)
- **Langfuse Worker**: 3030 (127.0.0.1:3030 → 3030)
- **Qdrant**: 6333, 6334 (127.0.0.1)
- **Neo4j**: 7473, 7474, 7687 (127.0.0.1)
- **ClickHouse**: 8123, 9000, 9009 (127.0.0.1)
- **MinIO**: 9010, 9011 (127.0.0.1:9010/9011 → 9000/9001)
- **Redis**: 6379 (127.0.0.1)
- **Caddy HTTP**: 80
- **Caddy HTTPS**: 443

### Existing AI Plus Stack
- **Postgres**: 5432
- **Ollama**: 11434
- **Triton Server**: 7000-7002
- **Consul HTTP**: 8500
- **Consul DNS**: 8600 (UDP)

### Running Supabase Stack
- **Kong HTTP**: 18000
- **Kong HTTPS**: 18443
- **Analytics**: 4000 (this conflicts, but running stack has it)

## Notes

1. **Consul - No Action Needed**: The Consul containers visible in `docker ps` are running from `/home/winadmin/.aiplus/base/`, which is **outside** the local-ai-packaged environment. There is **no Consul service** defined in the local-ai-packaged docker-compose files, so no port conflicts exist for this project.

2. **Analytics Port 4000**: Both Supabase stacks expose port 4000. The running Supabase stack is using it. If you need to run both simultaneously, you'll need to change the analytics port for one of them.

3. **Internal Communication**: Services within each Docker Compose stack communicate using internal container names and internal ports. The port mappings above only affect external access.

4. **NVIDIA GPU Driver**: If you encounter the error `could not select device driver "nvidia" with capabilities: [[gpu]]`, this is unrelated to port conflicts. This indicates:
   - NVIDIA Container Toolkit may not be installed
   - The nvidia-docker2 runtime may not be configured
   - GPU drivers may not be properly installed
   - You may need to use the `cpu` profile instead: `--profile cpu`

## How to Apply Changes

The changes have already been applied to:
- `.env`
- `docker-compose.yml`
- `docker-compose.override.private.yml`
- `supabase/docker/docker-compose.yml`

To start the services:
```bash
python start_services.py --profile gpu-nvidia --environment private
```

Or directly with docker compose:
```bash
docker compose -p localai --profile gpu-nvidia -f docker-compose.yml -f docker-compose.override.private.yml up -d
```

To verify no port conflicts:
```bash
docker ps
```

## Accessing Services

After starting, you can access:

### Via Caddy (Production URLs - requires hostname configuration)
- **n8n**: http://localhost:8001 (via Caddy)
- **Open WebUI**: http://localhost:8002 (via Caddy)
- **Flowise**: http://localhost:8003 (via Caddy)
- **Ollama**: http://localhost:8004 (via Caddy)
- **Supabase Studio**: http://localhost:8005 (via Caddy)
- **SearXNG**: http://localhost:8006 (via Caddy)
- **Langfuse**: http://localhost:8007 (via Caddy)
- **Neo4j**: http://localhost:8008 (via Caddy)

### Direct Access (Development/Private Network)
- **Supabase API**: http://localhost:19000
- **Open WebUI**: http://localhost:8082
- **Ollama**: http://localhost:11435
- **Flowise**: http://localhost:3001
- **n8n**: http://localhost:5678
- **Langfuse Web**: http://localhost:3000
- **Langfuse Worker**: http://localhost:3030
- **Postgres**: localhost:5434
- **SearXNG**: http://localhost:8081
- **Qdrant**: http://localhost:6333
- **Neo4j Browser**: http://localhost:7474
- **ClickHouse**: http://localhost:8123
- **MinIO Console**: http://localhost:9011
- **Redis**: localhost:6379
