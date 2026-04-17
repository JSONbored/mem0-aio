FROM node:24-slim@sha256:879b21aec4a1ad820c27ccd565e7c7ed955f24b92e6694556154f251e4bdb240 AS ui-builder

# Enable corepack for pnpm
RUN corepack enable

WORKDIR /build/ui
# Copy package files first to cache dependencies
COPY openmemory/openmemory/ui/package.json openmemory/openmemory/ui/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || npm install

# Copy source and build
COPY openmemory/openmemory/ui/ ./
# Route browser traffic back through the single published UI port.
RUN cat <<'EOF' > /build/ui/next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  skipTrailingSlashRedirect: true,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/openmemory-api/api/v1/config',
        destination: 'http://127.0.0.1:8765/api/v1/config/',
      },
      {
        source: '/openmemory-api/:path*',
        destination: 'http://127.0.0.1:8765/:path*',
      },
    ]
  },
}

export default nextConfig
EOF
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/openmemory-api
ENV NEXT_PUBLIC_USER_ID=default_user
RUN pnpm build || npm run build

ARG UPSTREAM_VERSION=v2.0.0
FROM qdrant/qdrant@sha256:94728574965d17c6485dd361aa3c0818b325b9016dac5ea6afec7b4b2700865f AS qdrant-bin

FROM ubuntu:24.04@sha256:c4a8d5503dfb2a3eb8ab5f807da5bc69a85730fb49b5cfca2330194ebcc41c7b
ARG S6_OVERLAY_VERSION=3.2.0.0
ARG TARGETARCH

# Install system dependencies, python, nodejs
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    xz-utils \
    tzdata \
    python3 \
    python3-pip \
    python3-venv \
    libunwind8 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 24 to match the UI builder runtime.
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Setup python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=qdrant-bin /qdrant/qdrant /usr/local/bin/qdrant
COPY --from=qdrant-bin /qdrant/config /qdrant/config
COPY --from=qdrant-bin /qdrant/static /qdrant/static

# Install S6 Overlay
RUN set -e && \
    S6_ARCH="${TARGETARCH:-$(uname -m)}" && \
    if [ "$S6_ARCH" = "x86_64" ]; then S6_ARCH="x86_64"; \
    elif [ "$S6_ARCH" = "amd64" ]; then S6_ARCH="x86_64"; \
    elif [ "$S6_ARCH" = "aarch64" ]; then S6_ARCH="aarch64"; \
    elif [ "$S6_ARCH" = "arm64" ]; then S6_ARCH="aarch64"; \
    else echo "Unsupported architecture: $S6_ARCH" && exit 1; fi && \
    curl -fsSL -o /tmp/s6-overlay-noarch.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    curl -fsSL -o /tmp/s6-overlay-${S6_ARCH}.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-${S6_ARCH}.tar.xz && \
    rm /tmp/s6-overlay-*.tar.xz

# Setup App Directory
WORKDIR /app

# Copy API files
COPY openmemory/openmemory/api/ /app/api/
RUN python3 <<'PY'
from pathlib import Path

database = Path("/app/api/app/database.py")
database.write_text(
    database.read_text().replace(
        """# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    connect_args={\"check_same_thread\": False}  # Needed for SQLite\n)\n""",
        """engine_kwargs = {}\nif DATABASE_URL.startswith(\"sqlite\"):\n    engine_kwargs[\"connect_args\"] = {\"check_same_thread\": False}\n\n# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    **engine_kwargs,\n)\n""",
    )
)

schemas = Path("/app/api/app/schemas.py")
schemas.write_text(
    schemas.read_text()
    .replace(
        "from pydantic import BaseModel, ConfigDict, Field, validator",
        "from pydantic import BaseModel, ConfigDict, Field, field_validator",
    )
    .replace(
        "    @validator('created_at', pre=True)\n    def convert_to_epoch(cls, v):",
        "    @field_validator('created_at', mode='before')\n    @classmethod\n    def convert_to_epoch(cls, v):",
    )
)
PY
RUN cd /app/api && pip install -r requirements.txt

# Copy standalone UI runtime from Stage 1
COPY --from=ui-builder /build/ui/public /app/ui/public
COPY --from=ui-builder /build/ui/.next/standalone /app/ui/
COPY --from=ui-builder /build/ui/.next/static /app/ui/.next/static
COPY --from=ui-builder /build/ui/entrypoint.sh /app/ui/entrypoint.sh
RUN sed -i 's|cd /app|cd /app/ui|' /app/ui/entrypoint.sh
COPY openmemory/openmemory/backup-scripts/ /app/backup-scripts/

# Setup S6 configuration
COPY rootfs/ /
RUN rm -rf \
    /etc/s6-overlay/s6-rc.d/fastapi \
    /etc/s6-overlay/s6-rc.d/nextjs \
    /etc/s6-overlay/s6-rc.d/qdrant && \
    rm -f \
    /etc/s6-overlay/s6-rc.d/user/contents.d/fastapi \
    /etc/s6-overlay/s6-rc.d/user/contents.d/nextjs \
    /etc/s6-overlay/s6-rc.d/user/contents.d/qdrant && \
    chmod +x /app/ui/entrypoint.sh && \
    find /app/backup-scripts -type f -name "*.sh" -exec chmod +x {} \; && \
    find /etc/cont-init.d -type f -exec chmod +x {} \; && \
    find /etc/services.d -type f -name "run" -exec chmod +x {} \;

# Set environment variables for services
ENV QDRANT__STORAGE__STORAGE_PATH=/mem0/storage
ENV QDRANT__TELEMETRY_DISABLED=true
ENV RUN_MODE=production
ENV QDRANT_HOST=127.0.0.1
ENV QDRANT_PORT=6333
ENV DATABASE_URL=sqlite:////mem0/storage/openmemory.db
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/openmemory-api
ENV NEXT_PUBLIC_USER_ID=default_user
ENV USER=default_user
ENV HOST="0.0.0.0"
ENV PORT="3000"

# Volumes
VOLUME ["/mem0/storage"]

# Expose ports: UI (3000), MCP API (8765), Qdrant (6333)
EXPOSE 3000 8765 6333

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
  CMD curl -fsS http://127.0.0.1:3000/ >/dev/null || exit 1

# Start s6 init
ENTRYPOINT ["/init"]
