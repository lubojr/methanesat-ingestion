import os
import logging
import json
from pathlib import Path
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from dotenv import load_dotenv
from google.cloud import storage
import boto3
import pystac
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rio_stac import stac
from pypgstac.db import PgstacDB
from pypgstac.load import Methods, Loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="ingest_logs.log",
)
logger = logging.getLogger(__name__)


def extract_datetime_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract acquisition datetime from filename using regex.
    Example: MSAT_L4_COG_GEE_interim_c01460640_p5129_v00009003_20240911T220558Z_220620Z.tif
    Extracts: 20240911T220558Z
    """
    pattern = r"(\d{8}T\d{6}Z)"
    match = re.search(pattern, filename, re.IGNORECASE)
    if match:
        dt_str = match.group(1).upper()
        try:
            return datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError as e:
            logger.error(f"Failed to parse datetime string {dt_str}: {e}")
    return None


def extract_file_metadata(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extracts Location ID, P-version, and Timestamp from GEE filenames.
    Pattern covers: ..._c01460640_p5129_v00009003_20240911T220558Z...
    """
    # Regex to capture Location (c...), Process (p...), and Timestamp (YYYYMMDDTHHMMSSZ)
    pattern = r"(c[A-Z0-9]+)_p(\d+)_.*_(\d{8}T\d{6}Z)"
    match = re.search(pattern, filename, re.IGNORECASE)

    if not match:
        return None

    return {
        "location": match.group(1),
        "p_version": int(match.group(2)),
        "timestamp": match.group(3),
        "scene_key": f"{match.group(1)}_{match.group(3)}",  # Unique per location + capture time
    }


def group_and_filter_gee_files(
    client: Any,
    bucket_name: str,
    prefixes: List[str],
    cog_filter_allow: Optional[str] = None,
    cog_filter_deny: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Scans GCS, groups by Location+Timestamp, and selects the highest p-version.
    """
    # temp_map structure: { scene_key: { "max_p": int, "cog": str, "geojson": str } }
    temp_map = {}

    for prefix in prefixes:
        logger.info(f"Scanning prefix: {prefix}")
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)

        for blob in blobs:
            name = blob.name
            meta = extract_file_metadata(name)

            if not meta:
                continue

            scene_key = meta["scene_key"]
            p_val = meta["p_version"]
            is_cog = "core/" in name and name.lower().endswith(".tif")
            if is_cog:
                if cog_filter_allow and cog_filter_allow not in name:
                    is_cog = False
                if cog_filter_deny and cog_filter_deny in name:
                    is_cog = False

            is_json = "divergence_integral/" in name and name.lower().endswith(
                ".geojson"
            )

            if scene_key not in temp_map:
                temp_map[scene_key] = {"max_p": -1, "cog": None, "geojson": None}

            # Logic: If this file has a newer or equal processing version than what we've seen
            if p_val >= temp_map[scene_key]["max_p"]:
                # If it's a strictly newer version, reset the versions
                if p_val > temp_map[scene_key]["max_p"]:
                    temp_map[scene_key]["max_p"] = p_val
                    # Reset if new version found to ensure COG and JSON belong to same P-version
                    if is_cog:
                        temp_map[scene_key]["cog"] = name
                        temp_map[scene_key]["geojson"] = (
                            None  # Reset JSON, wait for matching P
                        )
                    elif is_json:
                        temp_map[scene_key]["geojson"] = name
                        temp_map[scene_key]["cog"] = (
                            None  # Reset COG, wait for matching P
                        )
                else:
                    # Same version, just fill the missing slot
                    if is_cog:
                        temp_map[scene_key]["cog"] = name
                    if is_json:
                        temp_map[scene_key]["geojson"] = name

    # Final cleanup: Only return groups that have at least a COG
    final_groups = {k: v for k, v in temp_map.items() if v["cog"]}

    logger.info(f"Grouped into {len(final_groups)} unique scenes.")
    return final_groups


def get_gcs_client() -> storage.Client:
    project = os.getenv("GEE_PROJECT")
    client = storage.Client(project=project)
    return client


def list_gee_files(
    client: storage.Client,
    bucket_name: str,
    prefix: Optional[str] = None,
    suffixes: Tuple[str, ...] = (".tif", ".tiff"),
) -> List[str]:
    logger.info(f"Listing files in bucket: {bucket_name} with prefix: {prefix}")
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    files = [blob.name for blob in blobs if blob.name.lower().endswith(suffixes)]
    logger.info(f"Found {len(files)} files matching suffixes {suffixes}.")
    return files


def download_gee_file(
    client: storage.Client,
    bucket_name: str,
    file_name: str,
    destination_dir: str,
    skip_if_exists: bool = False,
) -> str:
    os.makedirs(destination_dir, exist_ok=True)
    destination_path = os.path.join(destination_dir, os.path.basename(file_name))

    if skip_if_exists and os.path.exists(destination_path):
        logger.info(f"File {destination_path} already exists. Skipping download.")
        return destination_path

    logger.info(f"Downloading {file_name} from {bucket_name} to {destination_dir}")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    blob.download_to_filename(destination_path)
    logger.info(f"Successfully downloaded to {destination_path}")
    return destination_path


def convert_cog_file(local_path: str) -> str:
    """
    Convert COG to EPSG:4326 using rio-stac's stac.create_stac_item functionality.
    This is a workaround to ensure the COGs are in a consistent CRS for STAC metadata extraction.
    The converted file will have "_4326" appended before the file extension.
    """
    output_path = local_path.rsplit(".", 1)[0] + "_4326.tif"
    logger.info(f"Converting {local_path} to EPSG:4326 at {output_path}")
    dst_crs = "EPSG:4326"
    try:
        with rasterio.open(local_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            kwargs = src.meta.copy()
            kwargs.update(
                {
                    "crs": dst_crs,
                    "transform": transform,
                    "width": width,
                    "height": height,
                    "tiled": True,
                    "blockxsize": 512,
                    "blockysize": 512,
                    "compress": "deflate",
                }
            )
            with rasterio.open(
                output_path,
                "w+",
                driver="COG",
                transform=transform,
                height=height,
                width=width,
                dtype=src.dtypes[0],
                count=len(src.indexes),
                crs="EPSG:4326",
            ) as dst:
                for i in src.indexes:
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.bilinear,
                    )
                dst.colorinterp = src.colorinterp
                logger.info(f"Successfully converted to {output_path}")
                return output_path
    except Exception as e:
        logger.error(f"Failed to convert COG {local_path} to EPSG:4326: {e}")
        raise


def get_s3_client() -> Any:
    client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )
    return client


def upload_to_s3(
    client: Any,
    bucket_name: str,
    local_path: str,
    s3_key: str,
    skip_if_exists: bool = False,
) -> str:
    if skip_if_exists:
        try:
            client.head_object(Bucket=bucket_name, Key=s3_key)
            logger.info(f"s3://{bucket_name}/{s3_key} already exists. Skipping upload.")
            return f"s3://{bucket_name}/{s3_key}"
        except client.exceptions.ClientError:
            # Object does not exist, proceed with upload
            pass

    logger.info(f"Uploading {local_path} to s3://{bucket_name}/{s3_key}")
    try:
        client.upload_file(local_path, bucket_name, s3_key)
        logger.info(f"Successfully uploaded to s3://{bucket_name}/{s3_key}")
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to S3: {e}")
        raise


def cleanup_local_file(local_path: str) -> None:
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Cleaned up local file: {local_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup local file {local_path}: {e}")


def create_stac_collection() -> pystac.Collection:
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


def ingest_collection(collection: pystac.Collection) -> None:
    logger.info(f"Ingesting STAC collection: {collection.id}")
    with PgstacDB() as db:
        loader = Loader(db)
        loader.load_collections([collection.to_dict()], Methods.upsert)


def map_s3_to_public_url(s3_url: str, public_url_prefix: Optional[str]) -> str:
    """
    Map an S3 URL to a public HTTPS URL.
    The mapping is relative to the '/public/' folder in the bucket.
    """
    if not public_url_prefix:
        return s3_url

    # s3_url format: s3://bucket-name/key
    parts = s3_url.replace("s3://", "").split("/", 1)
    if len(parts) < 2:
        return s3_url

    full_path = parts[1]

    # The requirement says relative to the /public/ folder
    if "public/" in full_path:
        relative_path = full_path.split("public/", 1)[1]
    else:
        relative_path = full_path

    return public_url_prefix.rstrip("/") + "/" + relative_path.lstrip("/")


def create_alternate_links(s3_url: str) -> Dict[str, Any]:
    """
    Create the 'alternate' dictionary for STAC assets.
    """
    return {
        "s3": {
            "href": s3_url,
            "description": "Access through s3.",
            "alternate:name": "s3",
        }
    }


def create_stac_item(
    local_path: str,
    s3_url: str,
    collection_id: str,
    item_datetime: Optional[datetime] = None,
    geojson_s3_url: Optional[str] = None,
    style_url: Optional[str] = None,
    public_url_prefix: Optional[str] = None,
) -> pystac.Item:
    logger.info(f"Generating STAC item for {s3_url}")

    primary_href = map_s3_to_public_url(s3_url, public_url_prefix)

    # Create base assets
    assets = {
        "data": pystac.Asset(
            href=primary_href,
            media_type=pystac.MediaType.COG,
            roles=["data"],
            extra_fields={
                "alternate": create_alternate_links(s3_url),
                "alternate:name": "https",
            },
        )
    }

    # Add optional GeoJSON asset
    if geojson_s3_url:
        geojson_primary_href = map_s3_to_public_url(geojson_s3_url, public_url_prefix)
        assets["distinct_point_sources"] = pystac.Asset(
            href=geojson_primary_href,
            media_type=pystac.MediaType.GEOJSON,
            roles=["data"],
            extra_fields={
                "alternate": create_alternate_links(geojson_s3_url),
                "alternate:name": "https",
            },
        )

    item = stac.create_stac_item(
        local_path,
        id=os.path.basename(local_path).split(".")[0],
        collection=collection_id,
        input_datetime=item_datetime,
        assets=assets,
        with_proj=False,
        with_raster=True,
        with_eo=False,
    )

    # Add optional vector style link
    if style_url and geojson_s3_url:
        item.add_link(
            pystac.Link(
                rel="style",
                target=style_url,
                media_type="text/vector-styles",
                extra_fields={"asset:keys": ["distinct_point_sources"]},
            )
        )

    return item


def ingest_items(items: List[pystac.Item]) -> None:
    logger.info(f"Ingesting {len(items)} STAC items")
    with PgstacDB() as db:
        loader = Loader(db)
        loader.load_items([item.to_dict() for item in items], Methods.upsert)


def is_geojson_valid(local_path: str) -> bool:
    logger.info(f"Checking GeoJSON content: {local_path}")
    try:
        with open(local_path, "r") as f:
            data = json.load(f)
            features = data.get("features", [])
            is_valid = len(features) > 0
            if not is_valid:
                logger.info(f"GeoJSON file {local_path} is empty (no features).")
            return is_valid
    except Exception as e:
        logger.error(f"Error reading GeoJSON {local_path}: {e}")
        return False


def upload_json_to_s3(
    client: Any, bucket_name: str, data_dict: Dict[str, Any], s3_key: str
) -> None:
    logger.info(f"Uploading STAC JSON to s3://{bucket_name}/{s3_key}")
    try:
        client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data_dict, indent=2),
            ContentType="application/json",
        )
        logger.info(f"Successfully uploaded STAC JSON to {s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload STAC JSON to S3: {e}")
        raise


def list_stac_items_from_s3(client: Any, bucket_name: str, prefix: str) -> List[str]:
    logger.info(f"Listing STAC JSON files in s3://{bucket_name}/{prefix}")
    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    json_keys = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].lower().endswith(".json") and not obj["Key"].endswith(
                "collection.json"
            ):
                json_keys.append(obj["Key"])

    logger.info(f"Found {len(json_keys)} STAC JSON files.")
    return json_keys


def read_json_from_s3(client: Any, bucket_name: str, key: str) -> Dict[str, Any]:
    logger.info(f"Reading STAC JSON from s3://{bucket_name}/{key}")
    try:
        response = client.get_object(Bucket=bucket_name, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to read STAC JSON from S3: {e}")
        raise


def extract_scene_id(filename: str):
    """
    Extract core MethaneSAT scene ID from filename.
    """
    pattern = r"(c\d+[A-Z0-9]+_p\d+_v\d+_\d{8}T\d{6}Z_\d{6}Z)"
    match = re.search(pattern, filename)
    return match.group(1) if match else None


def find_items_by_asset_filename(
    feature_collection: dict, filename: str
) -> Dict[str, Any] | None:
    """
    Search STAC FeatureCollection for items whose asset href contains the given filename.

    :param feature_collection: dict (STAC API search response)
    :param filename: str (substring to match in asset href)
    :return: first matching item dict or None
    """
    scene_id = extract_scene_id(filename)
    if not scene_id:
        return None

    for feature in feature_collection.get("features", []):
        assets = feature.get("assets", {})

        for _, asset in assets.items():
            href = asset.get("href", "")
            if scene_id in href:
                logger.info(
                    f"Found matching item for filename {filename} with scene ID {scene_id}"
                )
                return feature
    logger.error(f"No matching item found in STAC collection for filename: {filename}")


def main() -> None:
    load_dotenv(override=True)

    logger.info("--- Starting GEE to AWS Ingestion ---")

    # Required environment variables
    gee_bucket_name = os.getenv("GEE_BUCKET")
    aws_bucket_name = os.getenv("AWS_S3_BUCKET")
    gee_prefixes = [p.strip() for p in os.getenv("GEE_PREFIX", "").split(",")]
    local_data_dir = os.getenv("LOCAL_DATA_DIR", "./data")
    limit = os.getenv("LIMIT")
    if limit:
        limit = int(limit)  # type: ignore
    skip_ingestion = os.getenv("SKIP_INGESTION", "false").lower() == "true"
    ingestion_only = os.getenv("INGESTION_ONLY", "false").lower() == "true"
    aws_s3_prefix = os.getenv("AWS_S3_PREFIX", "methanesat_l4")
    stac_public_url_prefix = os.getenv("STAC_PUBLIC_URL_PREFIX")
    skip_download = os.getenv("SKIP_DOWNLOAD", "false").lower() == "true"
    skip_upload = os.getenv("SKIP_UPLOAD", "false").lower() == "true"
    do_cleanup = os.getenv("DO_CLEANUP", "false").lower() == "true"
    cog_filter_allow = os.getenv("COG_FILTER_ALLOW", "COG_GEE")
    cog_filter_deny = os.getenv("COG_FILTER_DENY", "COG_Portal")

    style_url = os.getenv("STAC_STYLE_URL")
    if not all([gee_bucket_name, aws_bucket_name]):
        logger.error(
            "Missing required environment variables (GEE_BUCKET, AWS_S3_BUCKET)."
        )
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
        if STAC_REMOTE_ENDPOINT := os.getenv("STAC_REMOTE_ENDPOINT"):
            # fetch API response
            resp = requests.get(STAC_REMOTE_ENDPOINT)
            stac_feature_collection = resp.json()
        if ingestion_only:
            logger.info("--- INGESTION_ONLY mode active ---")
            stac_keys = list_stac_items_from_s3(
                s3_client, aws_bucket_name, aws_s3_prefix
            )

            if not stac_keys:
                logger.warning("No STAC items found in S3 to ingest.")
                return

            # Apply limit if set
            stac_keys_to_process = stac_keys[:limit] if limit else stac_keys  # type: ignore
            logger.info(f"Processing {len(stac_keys_to_process)} STAC items from S3.")

            items_to_ingest = []
            for key in stac_keys_to_process:
                try:
                    item_dict = read_json_from_s3(s3_client, aws_bucket_name, key)
                    items_to_ingest.append(pystac.Item.from_dict(item_dict))
                except Exception as e:
                    logger.error(f"Failed to load item from {key}: {e}")
                    continue
        else:
            # filter to only contain newest processing id for COGs
            grouped_items = group_and_filter_gee_files(
                gcs_client,
                gee_bucket_name,
                gee_prefixes,
                cog_filter_allow=cog_filter_allow,
                cog_filter_deny=cog_filter_deny,
            )

            if not grouped_items:
                logger.warning("No matched items found to process.")
                return

            keys_to_process = (
                list(grouped_items.keys())[:limit]
                if limit
                else list(grouped_items.keys())
            )

            logger.info(f"Processing {len(keys_to_process)} matched groups.")

            items_to_ingest = []
            for scene_key in keys_to_process:
                group = grouped_items[scene_key]
                cog_gcs_name = group["cog"]
                geojson_gcs_name = group["geojson"]

                try:
                    # 1. Process COG
                    cog_local_path = download_gee_file(
                        gcs_client,
                        gee_bucket_name,
                        cog_gcs_name,
                        local_data_dir,
                        skip_if_exists=skip_download,
                    )  # type: ignore
                    cog_s3_key = os.path.join(aws_s3_prefix, cog_gcs_name)  # type: ignore
                    cog_local_path_4326 = convert_cog_file(cog_local_path)
                    cog_s3_url = upload_to_s3(
                        s3_client,
                        aws_bucket_name,
                        cog_local_path_4326,
                        cog_s3_key,
                        skip_if_exists=skip_upload,
                    )

                    # 2. Process optional GeoJSON
                    geojson_s3_url = None
                    if geojson_gcs_name:
                        geojson_local_path = download_gee_file(
                            gcs_client,
                            gee_bucket_name,
                            geojson_gcs_name,
                            local_data_dir,
                            skip_if_exists=skip_download,
                        )

                        # Content filtering for GeoJSON
                        if is_geojson_valid(geojson_local_path):
                            geojson_s3_key = os.path.join(
                                aws_s3_prefix, geojson_gcs_name
                            )
                            geojson_s3_url = upload_to_s3(
                                s3_client,
                                aws_bucket_name,
                                geojson_local_path,
                                geojson_s3_key,
                                skip_if_exists=skip_upload,
                            )
                        if do_cleanup:
                            cleanup_local_file(geojson_local_path)

                    # 3. Create STAC Item
                    item_dt = extract_datetime_from_filename(cog_gcs_name)  # type: ignore
                    item = create_stac_item(
                        cog_local_path_4326,
                        cog_s3_url,
                        collection.id,
                        item_datetime=item_dt,
                        geojson_s3_url=geojson_s3_url,
                        style_url=style_url,
                        public_url_prefix=stac_public_url_prefix,
                    )
                    remote_item = find_items_by_asset_filename(
                        stac_feature_collection, Path(cog_local_path).name
                    )
                    # Merge properties from remote item if available
                    if remote_item:
                        for prop in remote_item.get("properties", {}):
                            if prop not in item.properties:
                                item.properties[prop] = remote_item["properties"][prop]

                        # Overwrite footprint with target_geometry if available
                        target_geometry = remote_item.get("properties", {}).get(
                            "target_geometry"
                        )
                        if target_geometry:
                            logger.info(
                                f"Overwriting footprint with target_geometry for {item.id}"
                            )
                            item.geometry = {
                                "type": "Polygon",
                                "coordinates": [target_geometry],
                            }
                            lons = [p[0] for p in target_geometry]
                            lats = [p[1] for p in target_geometry]
                            item.bbox = [min(lons), min(lats), max(lons), max(lats)]

                    # Persist STAC JSON to S3
                    stac_s3_key = cog_s3_key.rsplit(".", 1)[0] + ".json"
                    upload_json_to_s3(
                        s3_client, aws_bucket_name, item.to_dict(), stac_s3_key
                    )

                    items_to_ingest.append(item)

                    # Cleanup COG
                    if do_cleanup:
                        cleanup_local_file(cog_local_path)
                        cleanup_local_file(cog_local_path_4326)

                except Exception as e:
                    logger.error(f"Failed to process group for {scene_key}: {e}")
                    continue

        # 4.4 Ingest Items
        if items_to_ingest:
            if not skip_ingestion:
                ingest_items(items_to_ingest)
            else:
                logger.info(
                    f"SKIP_INGESTION is true. Skipping ingestion of {len(items_to_ingest)} STAC items."
                )

    except Exception as e:
        logger.critical(f"Ingestion process failed: {e}")
        return

    logger.info("--- Ingestion Process Completed ---")


if __name__ == "__main__":
    main()
