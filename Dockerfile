# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install the project and its dependencies
RUN pip install --no-cache-dir .

# Final stage
FROM python:3.12-slim AS final

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create and set up entrypoint script
RUN <<EOF cat > /entrypoint.sh
#!/bin/bash

# Execute the Python module with all arguments
exec python -m local_flight_map \
  --app-port \${PORT:-5006} \
  --app-dev-mode false
EOF
RUN chmod +x /entrypoint.sh

# Expose the app port
EXPOSE ${PORT:-5006}

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"] 