# GitHub Actions Workflows

## Docker Build and Push

**File**: `.github/workflows/docker-build-push.yml`

### Description
Automated workflow that builds the Docker image and pushes it to GitHub Container Registry (ghcr.io).

### Triggers
- **Push to `main`**: Automatically builds and pushes the image
- **Pull Request to `main`**: Builds the image but does NOT push it
- **Manual**: Can be triggered manually from the Actions tab

### Changes that trigger the workflow
- `src/**` - Changes in source code
- `Dockerfile` - Changes in Dockerfile
- `pyproject.toml` - Changes in dependencies
- `.github/workflows/docker-build-push.yml` - Changes in the workflow

### Generated tags

| Trigger | Tags |
|---------|------|
| Push to main | `latest`, `main`, `commit-sha` |
| Pull Request | `pr-N` (build only) |
| Git tag (vX.Y.Z) | `vX.Y.Z`, `X.Y`, `X` |

### Requirements

No additional configuration required. The workflow uses:
- `GITHUB_TOKEN` automatically available
- Read/write permissions in packages already configured

### Usage

#### Accessing the built image

**From GitHub CLI**:
```bash
# List images
gh api user/packages?package_type=container

# Download image
docker pull ghcr.io/JCTekDev/ai-risk-analyzer:latest
```

**From the repository**:
- Go to `Packages` in the sidebar
- Select the `ai-risk-analyzer` package
- View download instructions

#### Running the image

```bash
# From GitHub Packages
docker run -d \
  --name risk-analyzer \
  -p 8000:8000 \
  --add-host host.local:YOUR_HOST_IP \
  --env-file .env \
  ghcr.io/JCTekDev/ai-risk-analyzer:latest
```

### Troubleshooting

#### Error: "permission denied"
Ensure the token has `packages:write` permissions.

#### Error: "unauthorized"
Verify that you are logged in correctly:
```bash
cat $HOME/.docker/config.json | jq '.auths["ghcr.io"]'
```

#### Manual login (if necessary)
```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_TOKEN
```

### Available variables in the workflow
- `REGISTRY`: `ghcr.io`
- `IMAGE_NAME`: Value of `github.repository` (owner/repo-name)

### Cache information

The workflow uses GitHub Actions cache to speed up subsequent builds:
- `cache-from: type=gha` - Read from cache
- `cache-to: type=gha,mode=max` - Save everything to cache

### Monitoring

You can view the workflow status at:
1. GitHub > Actions tab
2. Search for `Build and Push Docker Image`
3. View logs in real-time
