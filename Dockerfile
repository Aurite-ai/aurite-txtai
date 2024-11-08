# Use the official txtai CPU image as the base
FROM neuml/txtai-cpu:latest

# Copy the configuration files
COPY config/config.yml /app/config.yml
COPY config/service-account.json /app/service-account.json

# Copy the handler script
COPY handler.sh /app/handler.sh

# Make the handler script executable
RUN chmod +x /app/handler.sh

# Set the working directory
WORKDIR /app

# Cloud Run uses PORT environment variable
ENV PORT 8000

# Start the txtai API service using the handler script
CMD ["/app/handler.sh"]