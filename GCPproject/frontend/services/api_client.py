"""
API client for communicating with backend services.

Supports:
- Cloud Run services (legacy)
- Vertex AI Agent Engine (deployed Data Science Agent)
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Generator, List, Optional

import httpx

from config.settings import get_settings


def get_gcp_access_token() -> str:
    """Get GCP access token using gcloud CLI."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


@dataclass
class APIResponse:
    """Standard API response wrapper."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DemandPlannerClient:
    """
    Client for the Demand Planner Agent Cloud Run service.
    
    Endpoints:
    - POST /predict: Get demand prediction for a context
    - POST /approve: Approve/reject a forecast with optional override
    - GET /drivers: Get demand driver values for a context
    """

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.demand_planner_api
        self.timeout = 30.0

    async def predict_demand(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: date,
    ) -> APIResponse:
        """
        Request a demand prediction from the Demand Planner Agent.
        
        The agent will:
        1. Check BigQuery for driver data
        2. If missing, trigger Research Agent to fetch
        3. Apply heuristic functions
        4. Return prediction with reasoning
        """
        payload = {
            "sku_id": sku_id,
            "customer_id": customer_id,
            "location_id": location_id,
            "as_of_date": as_of_date.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict",
                    json=payload,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                error="Request timed out. The Research Agent may be fetching data.",
            )
        except httpx.HTTPStatusError as e:
            return APIResponse(
                success=False,
                error=f"API error: {e.response.status_code} - {e.response.text}",
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))

    async def approve_forecast(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: str,
        action: str,  # "approve" or "reject"
        override_value: Optional[float] = None,
        comments: Optional[str] = None,
    ) -> APIResponse:
        """
        Submit HITL approval/rejection for a forecast.
        
        On approval, the final consensus demand is written to Cloud SQL.
        """
        payload = {
            "sku_id": sku_id,
            "customer_id": customer_id,
            "location_id": location_id,
            "as_of_date": as_of_date,
            "action": action,
            "override_value": override_value,
            "comments": comments,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/approve",
                    json=payload,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except Exception as e:
            return APIResponse(success=False, error=str(e))

    async def get_driver_data(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: date,
    ) -> APIResponse:
        """
        Fetch demand driver values from BigQuery.
        """
        params = {
            "sku_id": sku_id,
            "customer_id": customer_id,
            "location_id": location_id,
            "as_of_date": as_of_date.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/drivers",
                    params=params,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except Exception as e:
            return APIResponse(success=False, error=str(e))


class DataScienceClient:
    """
    Client for the Data Science Agent Cloud Run service.
    
    Endpoints:
    - POST /query: Natural language query about data/drivers
    - POST /chart: Generate a chart based on request
    - GET /importance: Get driver importance scores
    """

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.data_science_agent_api
        self.timeout = 60.0  # Longer timeout for analysis

    async def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Send a natural language query to the Data Science Agent.
        
        Examples:
        - "What's the importance of weather for demand prediction?"
        - "Show me the trend of sales velocity over the last month"
        """
        payload = {
            "question": question,
            "context": context or {},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    json=payload,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except Exception as e:
            return APIResponse(success=False, error=str(e))

    async def get_driver_importance(
        self,
        sku_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Get feature importance scores for demand drivers.
        """
        params = {}
        if sku_id:
            params["sku_id"] = sku_id
        if customer_id:
            params["customer_id"] = customer_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/importance",
                    params=params,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except Exception as e:
            return APIResponse(success=False, error=str(e))

    async def generate_chart(
        self,
        chart_type: str,
        data_request: Dict[str, Any],
    ) -> APIResponse:
        """
        Request a chart generation from the Data Science Agent.
        
        Chart types: "trend", "bar", "scatter", "heatmap", "importance"
        """
        payload = {
            "chart_type": chart_type,
            "data_request": data_request,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chart",
                    json=payload,
                )
                response.raise_for_status()
                return APIResponse(success=True, data=response.json())

        except Exception as e:
            return APIResponse(success=False, error=str(e))


@dataclass
class AgentResponse:
    """Rich response from Agent Engine with text, images, and metadata."""
    
    text: str = ""
    images: List[Dict[str, Any]] = None  # Base64 encoded images
    artifacts: List[Dict[str, Any]] = None  # Files, charts, etc.
    tool_calls: List[str] = None  # Tools that were called
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.artifacts is None:
            self.artifacts = []
        if self.tool_calls is None:
            self.tool_calls = []
        if self.metadata is None:
            self.metadata = {}


class AgentEngineClient:
    """
    Client for the Data Science Agent deployed on Vertex AI Agent Engine.
    
    This replaces the Cloud Run-based DataScienceClient for production use.
    Uses the streamQuery endpoint for streaming responses.
    Supports rich content: text, images, artifacts.
    """

    def __init__(self):
        settings = get_settings()
        self.endpoint_url = settings.agent_engine_url
        self.timeout = 180.0  # Agent Engine may take longer

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        token = get_gcp_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def query_stream(
        self,
        message: str,
        user_id: str = "frontend-user",
        session_id: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Stream a response from the Agent Engine.
        
        Args:
            message: The natural language query
            user_id: User identifier for session management
            session_id: Optional session ID for conversation continuity
            
        Yields:
            Response text chunks as they arrive
        """
        headers = self._get_headers()
        if not headers.get("Authorization", "").endswith(" "):
            # Token exists
            pass
        else:
            yield "Error: Could not get GCP access token. Run `gcloud auth login`"
            return

        payload = {
            "input": {
                "message": message,
                "user_id": user_id
            }
        }
        if session_id:
            payload["input"]["session_id"] = session_id

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    self.endpoint_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        yield f"Error {response.status_code}: {response.text}"
                        return

                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                # Extract text from model response
                                if "content" in data and "parts" in data["content"]:
                                    for part in data["content"]["parts"]:
                                        if "text" in part:
                                            yield part["text"]
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException:
            yield "Error: Request timed out"
        except Exception as e:
            yield f"Error: {str(e)}"

    def query_rich(
        self,
        message: str,
        user_id: str = "frontend-user",
        session_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Query Agent Engine and return rich response with all content types.
        
        Args:
            message: The natural language query
            user_id: User identifier
            session_id: Optional session ID
            
        Returns:
            AgentResponse with text, images, artifacts, and metadata
        """
        headers = self._get_headers()
        
        if not headers.get("Authorization") or headers["Authorization"] == "Bearer ":
            return AgentResponse(text="Error: Could not get GCP access token. Run `gcloud auth login`")

        payload = {
            "input": {
                "message": message,
                "user_id": user_id
            }
        }
        if session_id:
            payload["input"]["session_id"] = session_id

        result = AgentResponse()
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.endpoint_url,
                    headers=headers,
                    json=payload,
                )
                
                if response.status_code != 200:
                    result.text = f"Error {response.status_code}: {response.text}"
                    return result

                # Parse all events from the streaming response
                for line in response.text.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        
                        # Track tool calls and artifacts
                        if "actions" in data:
                            actions = data["actions"]
                            if "state_delta" in actions and actions["state_delta"]:
                                result.metadata["state"] = actions["state_delta"]
                            
                            # Handle artifact_delta from analytics agent / code executor
                            # ADK artifacts use google.genai.types.Content format:
                            # { "artifact_name": { "parts": [{ "inline_data": { "mime_type": "...", "data": "base64..." }}] }}
                            if "artifact_delta" in actions and actions["artifact_delta"]:
                                for artifact_name, artifact_data in actions["artifact_delta"].items():
                                    image_extracted = False
                                    
                                    if isinstance(artifact_data, dict):
                                        # Format 1: Direct inline_data
                                        if "inline_data" in artifact_data:
                                            inline = artifact_data["inline_data"]
                                            if inline.get("mime_type", "").startswith("image/"):
                                                data_str = inline.get("data", "")
                                                # Handle bytes if needed
                                                if isinstance(data_str, bytes):
                                                    import base64
                                                    data_str = base64.b64encode(data_str).decode('utf-8')
                                                result.images.append({
                                                    "mime_type": inline["mime_type"],
                                                    "data": data_str,
                                                    "name": artifact_name
                                                })
                                                image_extracted = True
                                        
                                        # Format 2: ADK Content format with parts array
                                        if "parts" in artifact_data:
                                            for part in artifact_data["parts"]:
                                                if "inline_data" in part:
                                                    inline = part["inline_data"]
                                                    if inline.get("mime_type", "").startswith("image/"):
                                                        data_str = inline.get("data", "")
                                                        if isinstance(data_str, bytes):
                                                            import base64
                                                            data_str = base64.b64encode(data_str).decode('utf-8')
                                                        result.images.append({
                                                            "mime_type": inline["mime_type"],
                                                            "data": data_str,
                                                            "name": artifact_name
                                                        })
                                                        image_extracted = True
                                                # Also check for text parts in artifacts
                                                if "text" in part:
                                                    result.artifacts.append({
                                                        "name": artifact_name,
                                                        "data": {"type": "text", "content": part["text"]}
                                                    })
                                        
                                        # Format 3: fileData format (GCS URIs, etc.)
                                        if "fileData" in artifact_data:
                                            file_data = artifact_data["fileData"]
                                            result.artifacts.append({
                                                "name": artifact_name,
                                                "data": {"type": "file", "uri": file_data.get("fileUri", ""), "mime_type": file_data.get("mimeType", "")}
                                            })
                                    
                                    # Store non-image artifacts for reference
                                    if not image_extracted and artifact_data:
                                        result.artifacts.append({
                                            "name": artifact_name,
                                            "data": artifact_data
                                        })
                        
                        # Extract content parts
                        if "content" in data and "parts" in data["content"]:
                            for part in data["content"]["parts"]:
                                # Text content
                                if "text" in part:
                                    result.text = part["text"]
                                
                                # Image content (inline data from model or code executor)
                                if "inline_data" in part:
                                    inline = part["inline_data"]
                                    if inline.get("mime_type", "").startswith("image/"):
                                        result.images.append({
                                            "mime_type": inline["mime_type"],
                                            "data": inline.get("data", "")
                                        })
                                
                                # Code execution results (from analytics agent / VertexAiCodeExecutor)
                                if "code_execution_result" in part:
                                    exec_result = part["code_execution_result"]
                                    
                                    # Check for output_files (primary method for matplotlib/charts)
                                    # Format: [{"name": "...", "mime_type": "image/png", "data": "base64..."}]
                                    if "output_files" in exec_result and exec_result["output_files"]:
                                        for file_info in exec_result["output_files"]:
                                            mime = file_info.get("mime_type", file_info.get("mimeType", ""))
                                            if mime.startswith("image/"):
                                                data_str = file_info.get("data", "")
                                                if isinstance(data_str, bytes):
                                                    import base64
                                                    data_str = base64.b64encode(data_str).decode('utf-8')
                                                result.images.append({
                                                    "mime_type": mime,
                                                    "data": data_str,
                                                    "name": file_info.get("name", "chart")
                                                })
                                            else:
                                                # Non-image file artifact
                                                result.artifacts.append({
                                                    "name": file_info.get("name", "file"),
                                                    "data": {"type": "file", "mime_type": mime, "data": file_info.get("data", "")}
                                                })
                                    
                                    # Check for output text (might contain data URLs or plain output)
                                    if "output" in exec_result and exec_result["output"]:
                                        output = exec_result["output"]
                                        if isinstance(output, str):
                                            # Check for data URL format
                                            if "data:image" in output:
                                                try:
                                                    # Extract base64 data from data URL
                                                    data_parts = output.split(",", 1)
                                                    if len(data_parts) == 2:
                                                        mime_part = data_parts[0].split(";")[0].replace("data:", "")
                                                        result.images.append({
                                                            "mime_type": mime_part,
                                                            "data": data_parts[1]
                                                        })
                                                except Exception:
                                                    pass
                                            # Store text output as artifact for reference
                                            elif len(output) > 0 and len(output) < 10000:
                                                result.artifacts.append({
                                                    "name": "code_output",
                                                    "data": {"type": "text", "content": output}
                                                })
                                
                                # Function calls (for tracking)
                                if "function_call" in part:
                                    result.tool_calls.append(part["function_call"].get("name", "unknown"))
                                
                                # Executable code (for transparency)
                                if "executable_code" in part:
                                    code = part["executable_code"]
                                    if "code" in code:
                                        result.artifacts.append({
                                            "name": "executed_code",
                                            "data": {"language": code.get("language", "python"), "code": code["code"]}
                                        })
                        
                        # Track model metadata
                        if "model_version" in data:
                            result.metadata["model"] = data["model_version"]
                        if "usage_metadata" in data:
                            result.metadata["usage"] = data["usage_metadata"]
                            
                    except json.JSONDecodeError:
                        continue

                return result

        except httpx.TimeoutException:
            result.text = "Error: Request timed out"
            return result
        except Exception as e:
            result.text = f"Error: {str(e)}"
            return result

    async def query(
        self,
        message: str,
        user_id: str = "frontend-user",
        session_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Send a query and get the complete response (non-streaming).
        
        Args:
            message: The natural language query
            user_id: User identifier
            session_id: Optional session ID
            
        Returns:
            APIResponse with the agent's answer
        """
        headers = self._get_headers()
        
        payload = {
            "input": {
                "message": message,
                "user_id": user_id
            }
        }
        if session_id:
            payload["input"]["session_id"] = session_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint_url,
                    headers=headers,
                    json=payload,
                )
                
                if response.status_code != 200:
                    return APIResponse(
                        success=False,
                        error=f"Error {response.status_code}: {response.text}"
                    )

                # Parse streaming response to get final text
                full_text = ""
                images = []
                for line in response.text.strip().split('\n'):
                    if line:
                        try:
                            data = json.loads(line)
                            if "content" in data and "parts" in data["content"]:
                                for part in data["content"]["parts"]:
                                    if "text" in part:
                                        full_text = part["text"]
                                    if "inline_data" in part:
                                        inline = part["inline_data"]
                                        if inline.get("mime_type", "").startswith("image/"):
                                            images.append({
                                                "mime_type": inline["mime_type"],
                                                "data": inline.get("data", "")
                                            })
                        except json.JSONDecodeError:
                            continue

                return APIResponse(
                    success=True,
                    data={"response": full_text, "images": images}
                )

        except httpx.TimeoutException:
            return APIResponse(success=False, error="Request timed out")
        except Exception as e:
            return APIResponse(success=False, error=str(e))

