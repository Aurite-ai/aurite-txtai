echo "Uploading to github..."
source /home/ryan_aurite_ai/TrendAI/dev/git_upload.sh
echo "Upload complete!"

echo "Uploading to GCR..."
source /home/ryan_aurite_ai/TrendAI/dev/gcr_upload.sh
echo "GCR upload complete!"

echo "Running on GCP..."
docker-compose down
docker-compose up --build -d
echo "Running on GCP complete!"
