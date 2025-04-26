import os
import time
import json
from uuid import uuid4
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends

from configs.logger import logger
from utils.agent import run_agent
from utils.auth import get_api_key
from utils.helper import sort_by_index
from utils.helper import ResponseHelper
from utils.qdrant_store import QdrantStore
from utils.redis_cache import redis_client, get_query_cache_key
from utils.extract_doc import prepare_documents_from_csv_stream
from schemas.qdrant_store import CollectionCreatePayload, SearchPayload
from utils.prometheus_metrics import REQUEST_COUNT, REQUEST_ERRORS, REQUEST_LATENCY

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

qdrant = QdrantStore()
response = ResponseHelper()
router = APIRouter(prefix="", tags=["Qdrant Store"])


@router.post("/create_collection")
def collection_create(
    request: Request,
    data: CollectionCreatePayload,
    _: None = Depends(get_api_key),
):
    REQUEST_COUNT.inc()
    start_time = time.time()
    try:
        qdrant.create_collection(collection_name=data.collection_name)
        return response.success_response(201, "Collection created.")
    except Exception as e:
        REQUEST_ERRORS.inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        logger.error(f"Failed to create collection: {e}")
        return response.error_response(500, "Failed to create collection.", str(e))


@router.post("/add_document")
def document_add(
    request: Request,
    collection_name: str = Form(..., description="Name of the collection"),
    file: UploadFile = File(..., description="CSV file containing documents"),
    vector_columns: str = Form(...,
                               description="Comma-separated list of columns"),
    skip_empty: bool = Form(
        False, description="If True, skip rows with empty values in the specified columns"),
    batch_size: int = Form(
        100, description="Number of documents to yield per batch"),
    _: None = Depends(get_api_key),
):
    REQUEST_COUNT.inc()
    start_time = time.time()
    if file.content_type not in ["text/csv"]:
        REQUEST_ERRORS.inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        return response.error_response(400, "Invalid file type. Only CSV files are allowed.")

    vector_columns = [col.strip() for col in vector_columns.split(",")]

    filename = uuid4().hex + ".csv"
    file_path = f"{DATA_DIR}/{filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        # Stream batches and upload to Qdrant
        for batch in prepare_documents_from_csv_stream(file_path=file_path, skip_empty=skip_empty, batch_size=batch_size):
            qdrant.add_documents(
                collection_name=collection_name,
                documents=batch,
                vector_columns=vector_columns
            )
        # Clean up the file after processing
        os.remove(file_path)
        REQUEST_LATENCY.observe(time.time() - start_time)
        return response.success_response(200, "Documents added successfully.")
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Failed to add documents: {e}")
        REQUEST_ERRORS.inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        return response.error_response(500, "Failed to add documents.", str(e))


@router.post("/search")
def document_search(
    request: Request,
    payload: SearchPayload,
    _: None = Depends(get_api_key),
):
    REQUEST_COUNT.inc()
    start_time = time.time()
    query = payload.query.strip()

    if not query:
        REQUEST_ERRORS.inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        return response.error_response(400, "Query cannot be empty.")

    try:
        # === Step 1: Try fetching from Redis Cache ===
        cache_key = get_query_cache_key(
            payload.collection_name, query, payload.limit)
        cached_result = redis_client.get(cache_key)

        if cached_result:
            # Cache hit
            REQUEST_LATENCY.observe(time.time() - start_time)
            results = json.loads(cached_result)
            return response.success_response(200, "Success (from cache)", results)

        # === Step 2: Perform normal search ===
        results = qdrant.search_documents(
            payload.collection_name, query, limit=payload.limit
        )
        if not results:
            return response.error_response(404, "No results found.")

        results = [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results.points
        ]

        # === Step 3: Run the agent to sort the results ===
        # agent_result = run_agent(query, results)
        # if agent_result:
        #     sorted_index = agent_result.sorted_index
        #     results = sort_by_index(results, sorted_index)
        # else:
        #     logger.error("Agent returned no result.")

        # === Step 4: Cache the result in Redis ===
        redis_client.set(cache_key, json.dumps(
            results), ex=86400)  # 1 hour expiry

        REQUEST_LATENCY.observe(time.time() - start_time)
        return response.success_response(200, "Success", results)

    except Exception as e:
        REQUEST_ERRORS.inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        logger.error(f"Failed to search documents: {e}")
        return response.error_response(500, "Failed to search documents.", str(e))
