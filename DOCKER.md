# Docker Setup for Risk Analyzer

This guide covers building and running the Risk Analyzer in Docker containers.

## Quick Start

### 1. Build the Docker image
```bash
docker build -t risk-analyzer:latest .
```

### 2. Run with Docker Compose (recommended for local development with Joget)
```bash
# Set up .env file first
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and other credentials

# Run risk-analyzer service only (connect to external Joget)
docker-compose up -d risk-analyzer

# Run with local Joget instance
docker-compose --profile with-joget up -d
```

### 3. Run standalone container
```bash
docker run -d \
  --name risk-analyzer \
  -p 8000:8000 \
  -e JOGET_BASE_URL=http://joget:8080/jw \
  -e JOGET_USERNAME=admin \
  -e JOGET_PASSWORD=admin \
  -e JOGET_APP_ID=insurancePoliciesWorkflow \
  -e JOGET_TRAMITE_FORM_ID=insurance_policies \
  -e OPENAI_API_KEY=sk-... \
  risk-analyzer:latest
```

## Accessing the API

Once running, access the API at:
- **Base URL**: http://localhost:8000
- **Health check**: http://localhost:8000/health
- **Swagger UI docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Analyze a folio
```bash
curl -X POST "http://localhost:8000/analyze/34666095-2358-4109-a63d-abaf8c215e82"
```

## Environment Variables

The container accepts the following environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JOGET_BASE_URL` | Yes | `http://joget/jw` | Joget base URL |
| `JOGET_USERNAME` | Yes | `admin` | Joget admin username |
| `JOGET_PASSWORD` | Yes | `admin` | Joget admin password |
| `JOGET_APP_ID` | Yes | `insurancePoliciesWorkflow` | Joget application ID |
| `JOGET_TRAMITE_FORM_ID` | Yes | `insurance_policies` | Joget form ID for trámites |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key (or compatible LLM provider) |
| `LANGCHAIN_TRACING_V2` | No | `false` | Enable LangChain tracing |
| `ENV_FILE` | No | `.env` | Path to .env file inside container |

## Docker Compose Services

### risk-analyzer
- Main FastAPI service
- Exposes port 8000
- Depends on network access to Joget

### joget (optional, with-joget profile)
Enable with: `docker-compose --profile with-joget up`
- Joget Enterprise 8.0.10
- Exposes port 8080
- Useful for local development and testing

## Volumes

- `joget-data`: Persistent storage for Joget data (optional, when using with-joget profile)

## Networks

- `risk-analyzer-network`: Bridge network connecting risk-analyzer and joget services

## Build Variants

### Development Dockerfile (standard)
- Based on `python:3.11-slim`
- Includes build tools (gcc)
- Suitable for development and debugging

### Production Dockerfile (Dockerfile.prod)
- Multi-stage build reduces image size
- Virtual environment in builder stage
- Recommended for production deployments

To use the production Dockerfile:
```bash
docker build -f Dockerfile.prod -t risk-analyzer:prod .
```

## Troubleshooting

### Container won't start
Check logs:
```bash
docker logs risk-analyzer
```

### Connection refused to Joget
Ensure:
1. Joget is running and accessible at `JOGET_BASE_URL`
2. Credentials in `.env` are correct
3. Network configuration allows communication (use docker-compose for automatic networking)

### Health check failing
Verify:
```bash
docker exec risk-analyzer curl -f http://localhost:8000/health
```

### Permission denied errors
Ensure `.env` file exists and has proper permissions:
```bash
chmod 644 .env
```

## Maintenance

### View logs
```bash
# Risk analyzer logs
docker logs -f risk-analyzer

# With Joget
docker logs -f risk-analyzer-joget
```

### Stop containers
```bash
docker-compose down

# Remove volumes
docker-compose down -v
```

### Rebuild image (after code changes)
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Production Considerations

For production deployments:

1. **Use environment-specific configurations**: Create separate `.env.production` files
2. **Use multi-stage Dockerfile**: Reduces image size (see `.dockerignore.example`)
3. **Secrets management**: Use Docker secrets or orchestration platform (Kubernetes) instead of .env
4. **Resource limits**: Set CPU and memory limits in compose or orchestration
5. **Logging**: Configure appropriate log drivers (JSON file, syslog, etc.)
6. **Registry**: Push to Docker registry (Docker Hub, ECR, GCR, etc.)

Example with resource limits in docker-compose.yml:
```yaml
services:
  risk-analyzer:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## CI/CD Integration

### GitHub Actions example
Create `.github/workflows/docker.yml`:
```yaml
name: Build and Push Docker Image

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            my-registry/risk-analyzer:latest
            my-registry/risk-analyzer:${{ github.ref_name }}
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Python Docker Best Practices](https://docs.docker.com/language/python/)
