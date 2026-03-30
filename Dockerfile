FROM node:24-slim@sha256:06e5c9f86bfa0aaa7163cf37a5eaa8805f16b9acb48e3f85645b09d459fc2a9f AS ui-builder

# Enable corepack for pnpm
RUN corepack enable

WORKDIR /build/ui
# Copy package files first to cache dependencies
COPY openmemory/openmemory/ui/package.json openmemory/openmemory/ui/pnpm-lock.yaml* ./
# Note: In the Github Actions of Mem0, they might just use npm, but the repo showed pnpm
RUN pnpm install --frozen-lockfile || npm install

# Copy source and build
COPY openmemory/openmemory/ui/ ./
# Route browser traffic back through the single published UI port.
RUN cat <<'EOF' > /build/ui/next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/openmemory-api/:path*',
        destination: 'http://127.0.0.1:8765/:path*',
      },
    ]
  },
}

export default nextConfig
EOF
ENV NEXT_PUBLIC_API_URL=/openmemory-api
ENV NEXT_PUBLIC_USER_ID=default_user
RUN pnpm build || npm run build

ARG UPSTREAM_VERSION=v1.0.9
FROM qdrant/qdrant@sha256:94728574965d17c6485dd361aa3c0818b325b9016dac5ea6afec7b4b2700865f AS qdrant-bin

FROM ubuntu:24.04
ARG S6_OVERLAY_VERSION=3.2.0.0
ARG TARGETARCH

# Install system dependencies, python, nodejs
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    xz-utils \
    tzdata \
    git \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    libunwind8 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Setup python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=qdrant-bin /qdrant/qdrant /usr/local/bin/qdrant

# Install S6 Overlay
RUN set -e && \
    S6_ARCH="${TARGETARCH:-$(uname -m)}" && \
    if [ "$S6_ARCH" = "x86_64" ]; then S6_ARCH="x86_64"; \
    elif [ "$S6_ARCH" = "amd64" ]; then S6_ARCH="x86_64"; \
    elif [ "$S6_ARCH" = "aarch64" ]; then S6_ARCH="aarch64"; \
    elif [ "$S6_ARCH" = "arm64" ]; then S6_ARCH="aarch64"; \
    else echo "Unsupported architecture: $S6_ARCH" && exit 1; fi && \
    curl -jkL -o /tmp/s6-overlay-noarch.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    curl -jkL -o /tmp/s6-overlay-${S6_ARCH}.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-${S6_ARCH}.tar.xz && \
    rm /tmp/s6-overlay-*.tar.xz

# Setup App Directory
WORKDIR /app

# Copy API files
COPY openmemory/openmemory/api/ /app/api/
ENV PIP_NO_CACHE_DIR=1
RUN cd /app/api && pip install -r requirements.txt

# Copy built UI from Stage 1
COPY --from=ui-builder /build/ui/ /app/ui/

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
    sed -i 's|cd /app|cd /app/ui|' /app/ui/entrypoint.sh && \
    find /etc/cont-init.d -type f -exec chmod +x {} \; && \
    find /etc/services.d -type f -name "run" -exec chmod +x {} \;

# Set environment variables for services
ENV QDRANT__STORAGE__STORAGE_PATH=/mem0/storage
ENV QDRANT_HOST=127.0.0.1
ENV QDRANT_PORT=6333
ENV DATABASE_URL=sqlite:////mem0/storage/openmemory.db
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
