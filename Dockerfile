# Use the official txtai CPU image as the base
FROM neuml/txtai-cpu:latest

# Install wget and download yq
RUN apt-get update && apt-get install -y wget && \
    wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && \
    chmod +x /usr/bin/yq && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Create required directories first
RUN mkdir -p /app/data /app/models /app/info /app/config

# Copy the configuration files and scripts
COPY config/templates/config.yml /app/config/config.yml
COPY handler.sh /app/

# Make the handler script executable
RUN chmod +x /app/handler.sh

# Set Cloud Run's expected port
ENV PORT=8080 \
    PYTHONUNBUFFERED=1

# Start the txtai API service using the handler script
CMD ["/app/handler.sh"]