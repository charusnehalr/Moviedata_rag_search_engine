# ─────────────────────────────────────────────────────────────
# Stage: runtime image
#
# We build from the project root (docker-compose.yml context = .)
# so Docker can see both backend/ and cli/ in one build context.
# ─────────────────────────────────────────────────────────────

FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# ─────────────────────────────────────────────────────────────
# Install uv (our package manager)
# We copy only the version lockfile first so this layer is cached
# unless dependencies actually change.
# ─────────────────────────────────────────────────────────────
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# ─────────────────────────────────────────────────────────────
# Download the SentenceTransformer model at BUILD time.
#
# Why here and not at runtime?
#   - Container startup would need internet access to download ~90MB
#   - Slow first boot on every new container
#   - Baking it into the image means instant startup, no internet needed
# ─────────────────────────────────────────────────────────────
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ─────────────────────────────────────────────────────────────
# Copy application code
#
# This layer comes AFTER dependency installation.
# Changing your code only invalidates this layer — not the pip install layer.
# Order matters for build cache efficiency.
# ─────────────────────────────────────────────────────────────
COPY cli/ ./cli/
COPY backend/ ./backend/
COPY data/ ./data/

# cache/ is mounted as a Docker volume (see docker-compose.yml)
# so we don't COPY it — it comes from the host at runtime

# ─────────────────────────────────────────────────────────────
# Runtime configuration
# ─────────────────────────────────────────────────────────────

# Port the server listens on inside the container
EXPOSE 8000

# Start the FastAPI server
# --host 0.0.0.0 makes it reachable from outside the container
# --workers 1 keeps one process so the singleton loads once
CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
