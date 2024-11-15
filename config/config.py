import os

class Config:
    PROJECT_ID = os.environ.get('PROJECT_ID', 'your-project-id')
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'your-bucket-name')
    
    # Add other configuration variables as needed

