import os
import logging
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import storage
import boto3
import pystac
from rio_stac import stac
from pypgstac.db import PgstacDB
from pypgstac.load import Methods, Loader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_datetime_from_filename(filename):
    """
    Extract acquisition datetime from filename using regex.
    Example: MSAT_L4_COG_GEE_interim_c01460640_p5129_v00009003_20240911T220558Z_220620Z.tif
    Extracts: 20240911T220558Z
    """
    pattern = r"(\d{8}T\d{6}Z)"
    match = re.search(pattern, filename)
    if match:
        dt_str = match.group(1)
        try:
            return datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ")
        except ValueError as e:
            logger.error(f"Failed to parse datetime string {dt_str}: {e}")
    return None

def get_gcs_client():
    project = os.getenv("GEE_PROJECT")
    client = storage.Client(project=project)
    return client

def list_gee_files(client, bucket_name, prefix=None, suffixes=('.tif', '.tiff')):
    logger.info(f"Listing files in bucket: {bucket_name} with prefix: {prefix}")
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    files = [blob.name for blob in blobs if blob.name.lower().endswith(suffixes)]
    logger.info(f"Found {len(files)} files matching suffixes {suffixes}.")
    return files

def download_gee_file(client, bucket_name, file_name, destination_dir):
    logger.info(f"Downloading {file_name} from {bucket_name} to {destination_dir}")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    os.makedirs(destination_dir, exist_ok=True)
    destination_path = os.path.join(destination_dir, os.path.basename(file_name))
    
    blob.download_to_filename(destination_path)
    logger.info(f"Successfully downloaded to {destination_path}")
    return destination_path

def get_s3_client():
    client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    return client

def upload_to_s3(client, bucket_name, local_path, s3_key):
    logger.info(f"Uploading {local_path} to s3://{bucket_name}/{s3_key}")
    try:
        client.upload_file(local_path, bucket_name, s3_key)
        logger.info(f"Successfully uploaded to s3://{bucket_name}/{s3_key}")
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to S3: {e}")
        raise

def cleanup_local_file(local_path):
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Cleaned up local file: {local_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup local file {local_path}: {e}")

def create_stac_collection():
    collection_id = os.getenv("STAC_COLLECTION_ID")
    title = os.getenv("STAC_COLLECTION_TITLE")
    description = os.getenv("STAC_COLLECTION_DESCRIPTION")
    
    collection = pystac.Collection(
        id=collection_id,
        description=description,
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
            temporal=pystac.TemporalExtent([[None, None]]),
        ),
        title=title,
    )
    return collection

def ingest_collection(collection):
    logger.info(f"Ingesting STAC collection: {collection.id}")
    with PgstacDB() as db:
        loader = Loader(db)
        loader.load_collections([collection.to_dict()], Methods.upsert)

def create_stac_item(local_path, s3_url, collection_id, item_datetime=None):
    logger.info(f"Generating STAC item for {s3_url}")
    item = stac.create_stac_item(
        local_path,
        id=os.path.basename(local_path).split('.')[0],
        collection=collection_id,
        datetime=item_datetime,
        assets={
            "data": pystac.Asset(
                href=s3_url,
                media_type=pystac.MediaType.COG,
                roles=["data"],
            )
        },
        with_proj=True,
        with_raster=True,
    )
    return item

def ingest_items(items):
    logger.info(f"Ingesting {len(items)} STAC items")
    with PgstacDB() as db:
        loader = Loader(db)
        loader.load_items([item.to_dict() for item in items], Methods.upsert)

def is_geojson_valid(local_path):
    logger.info(f"Checking GeoJSON content: {local_path}")
    try:
        with open(local_path, 'r') as f:
            data = json.load(f)
            features = data.get('features', [])
            is_valid = len(features) > 0
            if not is_valid:
                logger.info(f"GeoJSON file {local_path} is empty (no features).")
            return is_valid
    except Exception as e:
        logger.error(f"Error reading GeoJSON {local_path}: {e}")
        return False

def main():
    load_dotenv()
    
    logger.info("--- Starting GEE to AWS Ingestion ---")
    
    # Required environment variables
    gee_bucket_name = os.getenv("GEE_BUCKET")
    aws_bucket_name = os.getenv("AWS_S3_BUCKET")
    gee_prefix = os.getenv("GEE_PREFIX", "")
    local_data_dir = os.getenv("LOCAL_DATA_DIR", "./data")
    limit = os.getenv("LIMIT")
    if limit:
        limit = int(limit)
    skip_ingestion = os.getenv("SKIP_INGESTION", "false").lower() == "true"
    aws_s3_prefix = os.getenv("AWS_S3_PREFIX", "methanesat_l4")

    if not all([gee_bucket_name, aws_bucket_name]):
        logger.error("Missing required environment variables (GEE_BUCKET, AWS_S3_BUCKET).")
        return

    try:
        gcs_client = get_gcs_client()
        s3_client = get_s3_client()
        logger.info("Cloud clients initialized.")
        
        # 4.2 Create/Ingest Collection
        collection = create_stac_collection()
        if not skip_ingestion:
            ingest_collection(collection)
        else:
            logger.info("SKIP_INGESTION is true. Skipping STAC collection ingestion.")
        
        # Determine suffixes based on prefix
        suffixes = ('.tif', '.tiff')
        if 'divergence_integral' in gee_prefix:
            suffixes = ('.geojson',)
            
        # 1. GEE Data Collection
        gee_files = list_gee_files(gcs_client, gee_bucket_name, gee_prefix, suffixes=suffixes)
        
        # Filter core files
        if 'core/' in gee_prefix:
            gee_files = [f for f in gee_files if 'COG_GEE' in f]
            logger.info(f"Filtered for COG_GEE in core/. Remaining files: {len(gee_files)}")
            
        if not gee_files:
            logger.warning("No files found to process.")
            return

        files_to_process = gee_files[:limit] if limit else gee_files
        logger.info(f"Processing {len(files_to_process)} files.")

        items_to_ingest = []
        for gcs_name in files_to_process:
            try:
                # Download
                local_path = download_gee_file(gcs_client, gee_bucket_name, gcs_name, local_data_dir)
                
                # Content filtering for GeoJSON
                if gcs_name.lower().endswith('.geojson'):
                    if not is_geojson_valid(local_path):
                        cleanup_local_file(local_path)
                        continue
                
                # Upload
                s3_key = os.path.join(aws_s3_prefix, gcs_name)
                s3_url = upload_to_s3(s3_client, aws_bucket_name, local_path, s3_key)
                
                # Extract datetime from filename
                item_dt = extract_datetime_from_filename(gcs_name)
                
                # 4.3 Create STAC Item
                item = create_stac_item(local_path, s3_url, collection.id, item_datetime=item_dt)
                items_to_ingest.append(item)
                
                # Cleanup
                cleanup_local_file(local_path)
                
            except Exception as e:
                logger.error(f"Failed to process {gcs_name}: {e}")
                continue
        
        # 4.4 Ingest Items
        if items_to_ingest:
            if not skip_ingestion:
                ingest_items(items_to_ingest)
            else:
                logger.info(f"SKIP_INGESTION is true. Skipping ingestion of {len(items_to_ingest)} STAC items.")
            
    except Exception as e:
        logger.critical(f"Ingestion process failed: {e}")
        return
    
    logger.info("--- Ingestion Process Completed ---")

if __name__ == "__main__":
    main()
