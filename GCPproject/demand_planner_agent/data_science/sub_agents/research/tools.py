# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for the Research Agent - Fetch from BigQuery and insert new records."""

import logging
import os
from datetime import date
from typing import Any, Dict, Optional

from google.adk.tools import ToolContext
from google.cloud import bigquery

logger = logging.getLogger(__name__)

# Fixed identifiers for PONDS data
PRODUCT_ID = "PONDS"
CUSTOMER_ID = "BLINKIT"
LOCATION_ID = "Bangalore"

# Feature columns to copy from random row (excluding identifiers and target)
FEATURE_COLUMNS = [
    "consensus_baseline_forecast",
    "real_time_sales_velocity",
    "ingredient_trend_velocity",
    "brand_sentiment_score",
    "viral_hashtag_volume",
    "influencer_mention_count",
    "performance_marketing_spend",
    "campaign_ctr",
    "video_completion_rate",
    "retargeting_pool_size",
    "on_platform_discount_depth",
    "bundle_offer_active_status",
    "flash_sale_participation",
    "cart_level_offer_conversion",
    "share_of_search_keyword_rank",
    "pdp_views",
    "buy_box_win_rate",
    "rating_and_review_velocity",
    "max_temperature_forecast",
    "humidity_index",
    "uv_index",
    "air_quality_index_aqi",
    "competitor_price_gap",
    "competitor_out_of_stock_status",
    "competitor_promo_intensity",
    "competitor_new_launch_signal",
    "inventory_days_on_hand",
    "distributor_open_orders",
    "stock_out_incidents",
]


def fetch_and_insert_demand_data(
    target_date: str,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """
    Fetch a random row from BigQuery, copy its feature values, and insert 
    a new row with PONDS/BLINKIT/Bangalore and the requested date.
    
    Args:
        target_date: Date in YYYY-MM-DD format for the new record.
        tool_context: ADK tool context for state management.
    
    Returns:
        Dictionary with the fetched features and insertion status.
    """
    logger.info(f"fetch_and_insert_demand_data called for date: {target_date}")
    
    # Validate date
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        return {"success": False, "error": f"Invalid date format: {target_date}. Use YYYY-MM-DD."}
    
    # Check date is not in future
    if parsed_date > date.today():
        return {
            "success": False, 
            "error": f"Cannot insert data for future date {target_date}. Today is {date.today().isoformat()}."
        }
    
    project_id = os.getenv("BQ_COMPUTE_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_TABLE_ID", "demand_driver_values_dataset")
    
    if not project_id or not dataset_id:
        return {"success": False, "error": "BQ_COMPUTE_PROJECT_ID or BQ_DATASET_ID not configured."}
    
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Step 1: Fetch ONE random row from BigQuery
        feature_cols_str = ", ".join(FEATURE_COLUMNS)
        query = f"""
            SELECT {feature_cols_str}
            FROM `{table_ref}`
            ORDER BY RAND()
            LIMIT 1
        """
        
        logger.info(f"Fetching random row from {table_ref}")
        query_job = client.query(query)
        results = list(query_job.result())
        
        if not results:
            return {"success": False, "error": "No existing data in BigQuery to copy from."}
        
        random_row = dict(results[0])
        logger.info(f"Fetched random row with {len(random_row)} features")
        
        # Step 2: Build new row with fixed identifiers + requested date + random features
        new_row = {
            "product_id": PRODUCT_ID,
            "customer_id": CUSTOMER_ID,
            "location_id": LOCATION_ID,
            "date_consensus": target_date,
        }
        
        # Add all feature values from random row
        for col in FEATURE_COLUMNS:
            if col in random_row:
                new_row[col] = random_row[col]
        
        # Step 3: Insert new row to BigQuery
        logger.info(f"Inserting new row for {PRODUCT_ID}/{CUSTOMER_ID}/{LOCATION_ID}/{target_date}")
        errors = client.insert_rows_json(table_ref, [new_row])
        
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return {
                "success": False,
                "error": "BigQuery insert failed",
                "bq_errors": str(errors),
            }
        
        # Step 4: Store features in context for qualitative description generation
        feature_data = {
            "product_id": PRODUCT_ID,
            "customer_id": CUSTOMER_ID,
            "location_id": LOCATION_ID,
            "date": target_date,
            "features": random_row,
        }
        
        if tool_context:
            tool_context.state["inserted_demand_data"] = feature_data
        
        return {
            "success": True,
            "message": f"Successfully inserted demand driver data for {PRODUCT_ID} at {LOCATION_ID} (customer: {CUSTOMER_ID}) on {target_date}",
            "product_id": PRODUCT_ID,
            "customer_id": CUSTOMER_ID,
            "location_id": LOCATION_ID,
            "date": target_date,
            "features": random_row,
        }
        
    except Exception as e:
        logger.exception("Error in fetch_and_insert_demand_data")
        return {"success": False, "error": str(e)}


def store_qualitative_description(
    description: str,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """
    Store the LLM-generated qualitative description in tool context.
    
    The Research Agent LLM should call this AFTER fetch_and_insert_demand_data
    to provide a human-readable explanation of the feature values.
    
    The description should:
    - Mention PONDS, BLINKIT, Bangalore explicitly
    - Explain what the feature values mean for demand
    - Highlight notable patterns (high/low values, opportunities, risks)
    
    Args:
        description: The qualitative description text generated by the LLM.
        tool_context: ADK tool context for state management.
    
    Returns:
        Dictionary confirming the description was stored.
    """
    logger.info("store_qualitative_description called")
    
    if not description:
        return {"success": False, "error": "Description cannot be empty."}
    
    if tool_context:
        tool_context.state["qualitative_description"] = description
        
        # Also include product/customer/location context
        if "inserted_demand_data" in tool_context.state:
            data = tool_context.state["inserted_demand_data"]
            tool_context.state["qualitative_context"] = {
                "product_id": data.get("product_id", PRODUCT_ID),
                "customer_id": data.get("customer_id", CUSTOMER_ID),
                "location_id": data.get("location_id", LOCATION_ID),
                "date": data.get("date"),
                "description": description,
            }
    
    return {
        "success": True,
        "message": "Qualitative description stored successfully.",
        "description_preview": description[:200] + "..." if len(description) > 200 else description,
    }
