import os
import logging
from dotenv import load_dotenv
from google.cloud import storage
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_gcs_client():
    project = os.getenv("GEE_PROJECT")
    client = storage.Client(project=project)
    return client

def list_gee_files(client, bucket_name, prefix=None):
    logger.info(f"Listing files in bucket: {bucket_name} with prefix: {prefix}")
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    cog_files = [blob.name for blob in blobs if blob.name.lower().endswith(('.tif', '.tiff'))]
    logger.info(f"Found {len(cog_files)} COG files.")
    return cog_files

def download_gee_file(client, bucket_name, file_name, destination_dir):
    logger.info(f"Downloading {file_name} from {bucket_name} to {destination_dir}")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    os.makedirs(destination_dir, exist_ok=True)
    destination_path = os.path.join(destination_dir, os.path.basename(file_name))
    
    blob.download_to_filename(destination_path)
    logger.info(f"Successfully downloaded to {destination_path}")
    return destination_path

def main():
    load_dotenv()
    
    # Placeholder for GEE to AWS ingestion logic
    logger.info("Starting GEE to AWS ingestion script...")
    
    gee_bucket_name = os.getenv("GEE_BUCKET")
    gee_prefix = os.getenv("GEE_PREFIX", "")
    local_data_dir = os.getenv("LOCAL_DATA_DIR", "./data")
    
    try:
        gcs_client = get_gcs_client()
        logger.info("GCS client initialized successfully.")
        
        # 1. GEE Data Collection
        gee_files = list_gee_files(gcs_client, gee_bucket_name, gee_prefix)
        
        local_files = []
        for file_name in gee_files:
            local_path = download_gee_file(gcs_client, gee_bucket_name, file_name, local_data_dir)
            local_files.append((file_name, local_path))
            
    except Exception as e:
        logger.error(f"Error during GEE data collection: {e}")
        return
    
    # 2. AWS Data Upload
    # 3. eoapi Ingestion
    
    logger.info("Ingestion script completed.")

if __name__ == "__main__":
    main()
