# Port Configuration Guide

This document explains the port configuration for the Local AI Packaged stack, including how to avoid conflicts with existing Docker containers.

## Understanding Port Configuration

### Internal vs External Ports

Docker containers use two types of ports:
- **Internal Ports**: Ports that services listen on inside the Docker network (used for container-to-container communication)
- **External Ports**: Ports mapped to the host machine (used for accessing services from your computer)

**Important**: When configuring services in `.env` files, use **internal ports** for database connections and service communication. External port mappings are defined separately in `docker-compose.yml` files.

## Critical Configuration: PostgreSQL

### The Correct Way

The PostgreSQL database configuration uses two different port variables:

1. **`POSTGRES_PORT`**: The **internal** port that PostgreSQL listens on inside the Docker network
   - **Must be**: `5432` (standard PostgreSQL port)
   - Used by: All Supabase services (auth, storage, meta, analytics, etc.) to connect to the database

2. **`POSTGRES_EXTERNAL_PORT`**: The **external** port for accessing the database from your host machine
   - Set to: `5434` (to avoid conflicts with other PostgreSQL instances)
   - Used by: External clients connecting from localhost

### Configuration in .env Files

```bash
# Database - Internal configuration
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432                    # Internal port - must be 5432
POSTGRES_USER=postgres
POSTGRES_EXTERNAL_PORT=5434           # External port - customizable
```

### Why This Matters

If `POSTGRES_PORT` is set to anything other than `5432`, the following will happen:
- PostgreSQL will listen on the wrong port inside the container
- Supabase services (auth, storage, etc.) will fail with "connection refused" errors
- Your SQL operations will fail with validation errors

## Port Conflicts Resolved

### 1. PostgreSQL Database
- **Internal Port**: 5432 (standard, used by all Supabase services)
- **External Port**: 5434 (mapped to avoid conflicts with other PostgreSQL instances)
- **Conflict Avoided**: Port 5432 used by `ai-plus-postgres-db` and other services
- **Access from Host**: `localhost:5434`
- **Files Modified**:
  - `.env`: `POSTGRES_PORT=5432` and `POSTGRES_EXTERNAL_PORT=5434`
  - `supabase/docker/docker-compose.yml`: Updated pooler to use `${POSTGRES_EXTERNAL_PORT:-5432}:5432`

### 2. Kong API Gateway
- **Conflict**: Ports 18000 and 18443 were used by another Supabase instance
- **Resolution**: Changed to ports **19000** (HTTP) and **19443** (HTTPS)
- **Files Modified**:
  - `.env`:
    - `KONG_HTTP_PORT=19000`
    - `KONG_HTTPS_PORT=19443`
    - `SUPABASE_PUBLIC_URL=http://localhost:19000`
    - `API_EXTERNAL_URL=http://localhost:19000`

### 3. Supabase Pooler Transaction Port
- **Conflict**: Port 6543 might conflict with other services
- **Resolution**: Changed to port **6544**
- **Files Modified**:
  - `.env`: `POOLER_PROXY_PORT_TRANSACTION=6544`

### 4. Ollama Service
- **Conflict**: Port 11434 was used by `aiplus-ollama`
- **Resolution**: Changed to port **11435** (if applicable in your setup)
- **Access**: `http://localhost:11435`

### 5. Open WebUI
- **Conflict**: Port 8080 was used by `searxng` container
- **Resolution**: Changed to port **8082**
- **Access**: `http://localhost:8082`

## Current Port Assignments

### Supabase Stack
| Service | Internal Port | External Port | Access URL |
|---------|--------------|---------------|------------|
| PostgreSQL Database | 5432 | 5434 | `localhost:5434` |
| Kong API Gateway (HTTP) | 8000 | 19000 | `http://localhost:19000` |
| Kong API Gateway (HTTPS) | 8443 | 19443 | `https://localhost:19443` |
| Supabase Pooler | 5432 | 5434 | `localhost:5434` |
| Supabase Pooler (Transaction) | 6543 | 6544 | `localhost:6544` |
| Analytics (Logflare) | 4000 | 4000 | `http://localhost:4000` |
| Studio | 3000 | *(via Kong)* | `http://localhost:19000` |
| REST API | 3000 | *(via Kong)* | `http://localhost:19000/rest/v1/` |
| Auth API | 9999 | *(via Kong)* | `http://localhost:19000/auth/v1/` |
| Storage API | 5000 | *(via Kong)* | `http://localhost:19000/storage/v1/` |
| Realtime | 4000 | *(via Kong)* | `http://localhost:19000/realtime/v1/` |

### Other Services
| Service | Internal Port | External Port | Access URL |
|---------|--------------|---------------|------------|
| n8n | 5678 | 5678 | `http://localhost:5678` |
| Open WebUI | 8080 | 8082 | `http://localhost:8082` |
| Flowise | 3001 | 3001 | `http://localhost:3001` |
| Ollama | 11434 | 11435 | `http://localhost:11435` |
| SearXNG | 8080 | 8081 | `http://localhost:8081` |
| Langfuse Web | 3000 | 3000 | `http://localhost:3000` |
| Qdrant | 6333 | 6333 | `http://localhost:6333` |
| Neo4j Browser | 7474 | 7474 | `http://localhost:7474` |
| Neo4j Bolt | 7687 | 7687 | `bolt://localhost:7687` |
| ClickHouse HTTP | 8123 | 8123 | `http://localhost:8123` |
| MinIO API | 9000 | 9010 | `http://localhost:9010` |
| MinIO Console | 9001 | 9011 | `http://localhost:9011` |
| Redis | 6379 | 6379 | `localhost:6379` |

### Existing Conflicting Services (External to This Project)
- **ai-plus-postgres-db**: Port 5432
- **aiplus-ollama**: Port 11434
- **searxng** (external): Port 8080
- **Other Supabase instance**: Ports 18000, 18443

## How to Start Services

### Using the Start Script
```bash
python start_services.py --profile gpu-nvidia --environment private
```

### Using Docker Compose Directly
```bash
# From project root
docker compose up -d

# Or with specific profiles
docker compose --profile gpu-nvidia up -d
```

### Restarting After Configuration Changes

**Important**: If you change port configurations in `.env` files, you must recreate the containers:

```bash
# Stop and remove containers
docker compose down

# Recreate with new configuration
docker compose up -d
```

**Note**: Simply using `docker compose restart` will NOT apply `.env` changes. You must remove and recreate the containers.

## Troubleshooting

### "Connection Refused" Errors

If you see errors like:
```
connect ECONNREFUSED 172.20.0.4:5432
```

**Cause**: PostgreSQL is not listening on port 5432 inside the container.

**Solution**:
1. Check `.env` file: Ensure `POSTGRES_PORT=5432`
2. Remove containers: `docker compose down`
3. Unset any environment variables: `unset POSTGRES_PORT`
4. Recreate containers: `docker compose up -d`

### Services in Restart Loop

Check logs to identify the issue:
```bash
docker logs supabase-auth --tail 50
docker logs supabase-storage --tail 50
```

Common causes:
- Database not ready (wait for health check)
- Wrong port configuration
- Missing environment variables

### Port Already in Use

If you get port binding errors:
```bash
# Find what's using the port (e.g., port 5434)
sudo lsof -i :5434

# Or check all Docker containers
docker ps -a
```

Change the external port in `.env` to an available port.

### Verifying Database Port

Check what port PostgreSQL is actually listening on:
```bash
docker exec supabase-db psql -U postgres -c "SHOW port;"
```

Should return `5432`. If it shows anything else, your `POSTGRES_PORT` variable is incorrect.

## Environment Variables Priority

Docker Compose uses this priority order (highest to lowest):
1. Shell environment variables (e.g., `export POSTGRES_PORT=5434`)
2. `.env` file in the directory where you run `docker compose`
3. `.env` file in included compose file directories
4. Default values in `docker-compose.yml`

**Recommendation**: Clear any conflicting shell variables before starting:
```bash
unset POSTGRES_PORT
unset KONG_HTTP_PORT
docker compose up -d
```

## Testing Your Setup

### Test Database Connection
```bash
# Via Docker exec
docker exec supabase-db psql -U postgres -c "SELECT version();"

# From host machine (requires psql client)
psql -h localhost -p 5434 -U postgres -d postgres
```

### Test Supabase API
```bash
# Get API schema
curl http://localhost:19000/rest/v1/

# Health check (with your actual ANON_KEY from .env)
curl http://localhost:19000/rest/v1/ \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### Check All Service Health
```bash
docker ps --filter "name=supabase" --format "table {{.Names}}\t{{.Status}}"
```

All services should show "Up" and "(healthy)" status.

## Best Practices

1. **Always use internal ports in .env for service communication**
2. **Only change external ports to avoid conflicts**
3. **Recreate containers after .env changes** (don't just restart)
4. **Check for shell environment variables** that might override .env
5. **Verify database is on port 5432 internally** before starting dependent services
6. **Use health checks** to ensure services are ready before they're accessed

## Quick Reference: Connection Strings

### From Host Machine
```bash
# PostgreSQL
postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5434/postgres

# Supabase REST API
http://localhost:19000/rest/v1/
```

### From Within Docker Network
```bash
# PostgreSQL
postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/postgres

# Supabase REST API
http://kong:8000/rest/v1/
```

## Additional Notes

1. **Analytics Port 4000**: If you need to run multiple Supabase instances simultaneously, change the analytics port in one of them by adding `ANALYTICS_PORT` to `.env` and updating the docker-compose configuration.

2. **Consul**: The Consul containers visible in `docker ps` are from external environments (e.g., `/home/winadmin/.aiplus/base/`). There is no Consul service in this project, so no action needed.

3. **GPU Drivers**: If you encounter `could not select device driver "nvidia"` errors, this is unrelated to port configuration. Install NVIDIA Container Toolkit or use `--profile cpu` instead.

4. **Network Isolation**: Each Docker Compose project creates its own network. Services in different projects can use the same internal ports without conflict, as long as external port mappings don't overlap.
