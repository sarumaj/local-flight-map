# Build stage
FROM python:3.14-slim

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
