# ReadmitCare Frontend - Docker Setup

This directory contains the Docker configuration for the ReadmitCare frontend React application.

## Architecture

The Dockerfile uses a **multi-stage build** approach:

1. **Build Stage**: Uses Node.js 20 Alpine to build the React application with Vite
2. **Production Stage**: Uses Nginx 1.25 Alpine to serve the built static files

## Requirements

- Docker 20.10+
- Node.js 18+ (for local development)

## Building the Docker Image

### Production Build

```bash
# Build the image
docker build -t readmitcare-frontend:latest .

# Run the container
docker run -p 80:80 readmitcare-frontend:latest
```

The application will be available at `http://localhost`

### Development Build (with Docker Compose)

For development with hot-reload:

```bash
# From the project root
docker-compose up frontend
```

The development server will be available at `http://localhost:5173`

## Configuration

### Environment Variables

The frontend can be configured using environment variables in the `.env` file:

- `VITE_API_BASE_URL`: Backend API base URL (default: `http://localhost:8000`)

### Nginx Configuration

The `nginx.conf` file includes:

- **SPA Routing**: All routes are directed to `index.html`
- **Gzip Compression**: Enabled for optimal performance
- **Security Headers**: X-Frame-Options, CSP, X-XSS-Protection
- **Static Asset Caching**: 1-year cache for JS/CSS/images
- **Health Check Endpoint**: `/health` for monitoring

## Building for Different Environments

### Development
```bash
docker build --target build -t readmitcare-frontend:dev .
```

### Production
```bash
docker build -t readmitcare-frontend:prod .
```

## Image Size Optimization

The multi-stage build ensures a minimal production image:

- Build stage: ~400MB (includes Node.js and build tools)
- Production stage: ~40MB (only nginx and static files)

## Health Checks

The Dockerfile includes a health check that verifies nginx is serving content:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
```

## Troubleshooting

### Build Fails

1. **Node version mismatch**: Ensure package.json specifies Node 18+
2. **Dependencies issue**: Delete `node_modules` and `package-lock.json`, then rebuild

### Container Won't Start

1. Check logs: `docker logs <container-id>`
2. Verify nginx configuration: `docker exec -it <container-id> nginx -t`

### Application Not Loading

1. Check if nginx is running: `docker exec -it <container-id> ps aux`
2. Verify files are in place: `docker exec -it <container-id> ls /usr/share/nginx/html`

## Security Considerations

- The Dockerfile uses Alpine Linux for minimal attack surface
- Nginx runs as non-root user (default in nginx:alpine)
- Security headers are configured in nginx.conf
- Static files only - no application server vulnerabilities

## References

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- Design Document: Section 6.3 - Frontend Dockerfile
- Requirements: 24.6
