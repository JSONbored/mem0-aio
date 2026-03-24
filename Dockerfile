FROM node:22-slim AS ui-builder

# Enable corepack for pnpm
RUN corepack enable

WORKDIR /build/ui
# Copy package files first to cache dependencies
COPY openmemory/ui/package.json openmemory/ui/pnpm-lock.yaml* ./
# Note: In the Github Actions of Mem0, they might just use npm, but the repo showed pnpm
RUN pnpm install --frozen-lockfile || npm install

# Copy source and build
COPY openmemory/ui/ ./
# We need to set a dummy URL during build so Next.js doesn't fail static generation
ENV NEXT_PUBLIC_API_URL=http://localhost:8765
RUN pnpm build || npm run build

# Stage 2: Main Image (Ubuntu for S6 + Python + Node + Qdrant)
FROM ubuntu:24.04

# S6 Overlay version
ARG S6_OVERLAY_VERSION=3.2.0.0

# Install system dependencies, python, nodejs
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    xz-utils \
    tzdata \
    git \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Setup python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Qdrant statically
RUN cd /tmp && \
    wget -qO qdrant.tar.gz https://github.com/qdrant/qdrant/releases/download/v1.13.0/qdrant-x86_64-unknown-linux-gnu.tar.gz && \
    tar -xzf qdrant.tar.gz && \
    mv qdrant /usr/local/bin/ && \
    rm qdrant.tar.gz

# Install S6 Overlay
RUN set -e && \
    S6_ARCH=$(uname -m) && \
    if [ "$S6_ARCH" = "x86_64" ]; then S6_ARCH="x86_64"; \
    elif [ "$S6_ARCH" = "aarch64" ]; then S6_ARCH="aarch64"; \
    else echo "Unsupported architecture: $S6_ARCH" && exit 1; fi && \
    curl -jkL -o /tmp/s6-overlay-noarch.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    curl -jkL -o /tmp/s6-overlay-${S6_ARCH}.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-${S6_ARCH}.tar.xz && \
    rm /tmp/s6-overlay-*.tar.xz

# Setup App Directory
WORKDIR /app

# Copy API files
COPY openmemory/api/ /app/api/
RUN cd /app/api && pip install --no-cache-dir -r requirements.txt

# Copy built UI from Stage 1
COPY --from=ui-builder /build/ui/ /app/ui/

# Setup S6 configuration
COPY rootfs/ /

# Set environment variables for services
ENV QDRANT__STORAGE__STORAGE_PATH=/mem0/storage
ENV HOST="0.0.0.0"
ENV PORT="3000"

# Volumes
VOLUME ["/mem0/storage"]

# Expose ports: UI (3000), MCP API (8765), Qdrant (6333)
EXPOSE 3000 8765 6333

# Start s6 init
ENTRYPOINT ["/init"]
