"""
Enhanced Chatbot Interface - ADK Web Style
Uses SSE streaming to show intermediate agent calls
"""

import streamlit as st
import requests
import json
import base64
from datetime import datetime, timedelta
import re

# Try to import GCS client for fetching images from Cloud Storage
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# Page config
    st.set_page_config(
    page_title="Demand Planner Assistant",
    page_icon="🤖",
    layout="wide"
)

# Dark theme CSS matching ADK Web
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
    }
    
    /* Tool call badges */
    .tool-call {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 6px 14px;
        margin: 4px 4px 4px 0;
        font-size: 13px;
        color: #c9d1d9;
    }
    
    .tool-call.pending {
        border-color: #58a6ff;
    }
    
    .tool-call.complete {
        border-color: #3fb950;
    }
    
    /* Agent message bubble */
    .agent-message {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        color: #c9d1d9;
    }
    
    /* User message bubble */
    .user-message {
        background-color: #238636;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 10px 0;
        margin-left: auto;
        max-width: 70%;
        color: white;
        text-align: right;
    }
    
    /* Header */
    .main-header {
        color: #58a6ff;
        font-size: 24px;
                font-weight: 600;
        padding: 15px 0;
        border-bottom: 1px solid #30363d;
        margin-bottom: 15px;
    }
    
    /* Session ID */
    .session-badge {
        background-color: #21262d;
        color: #8b949e;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 12px;
        font-family: monospace;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Quick action buttons */
    .stButton > button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #30363d;
        border-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL - defaults to local, can be overridden by environment variable
import os
import subprocess

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Agent Engine Configuration
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "3467662861424132096")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0010459436")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
AGENT_ENGINE_URL = f"https://{GCP_REGION}-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/reasoningEngines/{AGENT_ENGINE_ID}"

# Use Agent Engine instead of local backend
USE_AGENT_ENGINE = os.getenv("USE_AGENT_ENGINE", "true").lower() == "true"

def get_gcp_access_token():
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

def fetch_gcs_image(gcs_uri: str):
    """Fetch image from Google Cloud Storage URI."""
    if not GCS_AVAILABLE:
        return None
    
    try:
        # Parse gs:// URI
        match = re.match(r'gs://([^/]+)/(.+)', gcs_uri)
        if not match:
            return None
        
        bucket_name, blob_name = match.groups()
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        return blob.download_as_bytes()
    except Exception as e:
        st.warning(f"Could not fetch image from GCS: {e}")
        return None

def display_image(img_data: dict):
    """Display an image from various formats."""
    try:
        if "data" in img_data and img_data["data"]:
            # Base64 encoded image
            image_bytes = base64.b64decode(img_data["data"])
            st.image(image_bytes, use_container_width=True)
            return True
    except Exception as e:
        pass
    return False

def display_gcs_image(uri: str):
    """Display an image from GCS URI."""
    image_bytes = fetch_gcs_image(uri)
    if image_bytes:
        st.image(image_bytes, use_container_width=True)
        return True
    else:
        # Show the URI as a link if we can't fetch it
        st.markdown(f"📊 [View Chart]({uri})")
        return False

def fetch_session_artifacts(session_id: str, already_shown: set = None):
    """Fetch only NEW artifacts (not previously shown) from the ADK session."""
    if already_shown is None:
        already_shown = set()
    
    artifacts = []
    fetched_names = set()
    
    def try_fetch_artifact(artifact_name: str, version: str):
        """Try to fetch a specific artifact version."""
        artifact_key = f"{artifact_name}:v{version}"
        
        # Skip if already shown or already fetched in this call
        if artifact_key in already_shown or artifact_key in fetched_names:
            return None
        
        try:
            artifact_url = f"{BACKEND_URL}/apps/data_science/users/user/sessions/{session_id}/artifacts/{artifact_name}/versions/{version}"
            artifact_response = requests.get(artifact_url, timeout=10)
            
            if artifact_response.status_code == 200:
                try:
                    artifact_json = artifact_response.json()
                    inline_data = artifact_json.get("inlineData", {})
                    
                    if "data" in inline_data:
                        b64_data = inline_data["data"]
                        b64_standard = b64_data.replace('-', '+').replace('_', '/')
                        
                        padding_needed = len(b64_standard) % 4
                        if padding_needed:
                            b64_standard += "=" * (4 - padding_needed)
                        
                        try:
                            image_data = base64.b64decode(b64_standard)
                        except Exception:
                            return None
                        
                        mime_type = inline_data.get("mimeType", "image/png")
                        
                        if len(image_data) > 100:
                            fetched_names.add(artifact_key)
                            return {
                                "name": artifact_name,
                                "version": version,
                                "key": artifact_key,
                                "data": image_data,
                                "content_type": mime_type
                            }
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        return None
    
    try:
        # Find the LATEST version of each artifact (most recently created)
        for i in range(1, 10):
            artifact_name = f"code_execution_image_{i}.png"
            
            # Find highest available version for this artifact
            highest_version = None
            for version in range(20, -1, -1):  # Check from high to low
                artifact_key = f"{artifact_name}:v{version}"
                if artifact_key in already_shown:
                    continue  # Skip already shown versions
                    
                try:
                    artifact_url = f"{BACKEND_URL}/apps/data_science/users/user/sessions/{session_id}/artifacts/{artifact_name}/versions/{version}"
                    check_response = requests.head(artifact_url, timeout=2)
                    if check_response.status_code == 200:
                        highest_version = str(version)
                        break
                except:
                    continue
            
            # Fetch the highest version if found and not already shown
            if highest_version is not None:
                artifact = try_fetch_artifact(artifact_name, highest_version)
                if artifact:
                    artifacts.append(artifact)
                    
    except Exception:
        pass
    
    return artifacts

def find_artifact_names(obj, found=None):
    """Recursively find artifact names in session data."""
    if found is None:
        found = set()
    
    if isinstance(obj, dict):
        # Look for artifact references
        if "artifact" in obj:
            artifact = obj["artifact"]
            if isinstance(artifact, dict) and "name" in artifact:
                found.add(artifact["name"])
            elif isinstance(artifact, str):
                found.add(artifact)
        
        # Look for file names that look like artifacts
        if "filename" in obj:
            filename = obj["filename"]
            if isinstance(filename, str) and (".png" in filename or ".jpg" in filename):
                found.add(filename)
        
        # Look for name fields with image extensions
        if "name" in obj:
            name = obj["name"]
            if isinstance(name, str) and ("image" in name.lower() or ".png" in name or ".jpg" in name):
                found.add(name)
        
        for v in obj.values():
            find_artifact_names(v, found)
    elif isinstance(obj, list):
        for item in obj:
            find_artifact_names(item, found)
    
    return list(found)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "quick_action" not in st.session_state:
    st.session_state.quick_action = None
if "shown_artifacts" not in st.session_state:
    st.session_state.shown_artifacts = set()  # Track artifacts already displayed

def create_session():
    """Create a new session with Agent Engine or ADK backend."""
    if USE_AGENT_ENGINE:
        try:
            token = get_gcp_access_token()
            if not token:
                st.error("Failed to get GCP access token. Run `gcloud auth login`")
                return None
            
            response = requests.post(
                f"{AGENT_ENGINE_URL}:query",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "class_method": "create_session",
                    "input": {"user_id": "streamlit-user"}
                },
                timeout=120  # Increased for cold start
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("output", {}).get("id")
            else:
                st.error(f"Failed to create session: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to create session: {e}")
        return None
    else:
        # Original ADK backend code
        try:
            response = requests.post(
                f"{BACKEND_URL}/apps/data_science/users/user/sessions",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
        except Exception as e:
            st.error(f"Failed to create session: {e}")
        return None

def send_message_with_events(session_id: str, message: str, status_container):
    """
    Send message and poll for events to show tool calls.
    Uses Agent Engine streamQuery or ADK /run endpoint.
    """
    
    events_shown = set()
    tool_calls = []
    
    # Show thinking status
    status_container.markdown("⏳ **Agent is thinking...**")
    
    if USE_AGENT_ENGINE:
        # Use Agent Engine streamQuery endpoint
        try:
            token = get_gcp_access_token()
            if not token:
                return {
                    "tool_calls": [],
                    "text": "Error: Could not get GCP access token",
                    "images": [],
                    "file_uris": [],
                    "artifacts": []
                }
            
            response = requests.post(
                f"{AGENT_ENGINE_URL}:streamQuery",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": {
                        "message": message,
                        "user_id": "streamlit-user",
                        "session_id": session_id
                    }
                },
                timeout=300
            )
            
            if response.status_code != 200:
                return {
                    "tool_calls": [],
                    "text": f"Error: {response.status_code} - {response.text}",
                    "images": [],
                    "file_uris": [],
                    "artifacts": []
                }
            
            # Parse streaming response
            text = ""
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        # Extract tool calls from actions
                        if "actions" in data:
                            actions = data.get("actions", {})
                            if actions.get("state_delta"):
                                tool_calls.append("database_settings_loaded")
                        # Extract text from model response
                        if "content" in data and "parts" in data["content"]:
                            for part in data["content"]["parts"]:
                                if "text" in part:
                                    text = part["text"]
                    except json.JSONDecodeError:
                        continue
            
            # Update status with tool calls
            if tool_calls:
                tools_html = ""
                for tool in tool_calls:
                    tools_html += f'<span class="tool-call complete">✓ {tool}</span> '
                status_container.markdown(tools_html, unsafe_allow_html=True)
            
            return {
                "tool_calls": tool_calls,
                "text": text,
                "images": [],
                "file_uris": [],
                "artifacts": []
            }
            
        except Exception as e:
            return {
                "tool_calls": [],
                "text": f"Error: {str(e)}",
                "images": [],
                "file_uris": [],
                "artifacts": []
            }
    
    # Original ADK backend code
    try:
        # Send message using /run endpoint (synchronous, reliable)
        payload = {
            "app_name": "data_science",
            "user_id": "user",
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/run",
            json=payload,
            timeout=300  # 5 min timeout for complex operations
        )
        
        if response.status_code != 200:
            return {
                "tool_calls": [],
                "text": f"Error: {response.status_code} - {response.text}",
                "images": [],
                "file_uris": [],
                "artifacts": []
            }
        
        # Now fetch session to get all events including tool calls
        session_response = requests.get(
            f"{BACKEND_URL}/apps/data_science/users/user/sessions/{session_id}",
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            tool_calls = extract_tool_calls(session_data)
            
            # Update status with tool calls
            if tool_calls:
                tools_html = ""
                for tool in tool_calls:
                    tools_html += f'<span class="tool-call complete">✓ {tool}</span> '
                status_container.markdown(tools_html, unsafe_allow_html=True)
        
        # Extract text and images from response
        text, images, file_uris = extract_response_content(response.json())
        
        # Also check session data for images
        if session_response.status_code == 200:
            session_data = session_response.json()
            _, session_images, session_file_uris = extract_response_content(session_data)
            images.extend(session_images)
            file_uris.extend(session_file_uris)
        
        # Fetch only NEW artifacts (not previously shown)
        artifacts = fetch_session_artifacts(session_id, st.session_state.get("shown_artifacts", set()))
        
        return {
            "tool_calls": tool_calls,
            "text": text,
            "images": images,
            "file_uris": file_uris,
            "artifacts": artifacts
        }
        
    except requests.exceptions.Timeout:
        return {
            "tool_calls": tool_calls,
            "text": "⏱️ Request timed out. The agent might be processing a complex query.",
            "images": [],
            "file_uris": [],
            "artifacts": []
        }
    except Exception as e:
        return {
            "tool_calls": [],
            "text": f"❌ Error: {str(e)}",
            "images": [],
            "file_uris": [],
            "artifacts": []
        }

def extract_tool_calls(session_data):
    """Extract tool call names from session events."""
    tool_calls = []
    seen = set()
    
    def find_tool_calls(obj):
        if isinstance(obj, dict):
            # Look for function_call
            if "function_call" in obj:
                fc = obj["function_call"]
                if isinstance(fc, dict) and "name" in fc:
                    name = fc["name"]
                    if name not in seen:
                        seen.add(name)
                        tool_calls.append(name)
            
            # Look for name field with common tool patterns
            if "name" in obj:
                name = obj["name"]
                if isinstance(name, str) and any(x in name.lower() for x in ["agent", "sql", "bigquery", "research", "analytics"]):
                    if name not in seen:
                        seen.add(name)
                        tool_calls.append(name)
            
            for v in obj.values():
                find_tool_calls(v)
        elif isinstance(obj, list):
            for item in obj:
                find_tool_calls(item)
    
    find_tool_calls(session_data)
    return tool_calls

def extract_response_content(data, debug=False):
    """Extract text and images from the response."""
    texts = []
    images = []
    file_uris = []
    
    def find_content(obj, path="root"):
        if isinstance(obj, dict):
            # Extract text
            if "text" in obj and isinstance(obj["text"], str):
                text = obj["text"].strip()
                if text and len(text) > 5:  # Filter tiny fragments
                    texts.append(text)
            
            # Extract inline images (base64 encoded)
            if "inline_data" in obj:
                inline = obj["inline_data"]
                if isinstance(inline, dict) and "data" in inline:
                    if debug:
                        print(f"Found inline_data at {path}")
                    images.append({
                        "data": inline["data"],
                        "mime_type": inline.get("mime_type", "image/png"),
                        "source": "inline"
                    })
            
            # Extract file_data (Code Interpreter generates these)
            if "file_data" in obj:
                file_info = obj["file_data"]
                if isinstance(file_info, dict):
                    if "file_uri" in file_info:
                        if debug:
                            print(f"Found file_uri at {path}: {file_info['file_uri']}")
                        file_uris.append(file_info["file_uri"])
                    if "data" in file_info:
                        if debug:
                            print(f"Found file_data with data at {path}")
                        images.append({
                            "data": file_info["data"],
                            "mime_type": file_info.get("mime_type", "image/png"),
                            "source": "file_data"
                        })
            
            # Extract from code execution output_files
            if "output_files" in obj:
                if debug:
                    print(f"Found output_files at {path}")
                for i, output_file in enumerate(obj.get("output_files", [])):
                    if isinstance(output_file, dict):
                        if "contents" in output_file:
                            images.append({
                                "data": output_file["contents"],
                                "mime_type": output_file.get("mime_type", "image/png"),
                                "source": "output_file"
                            })
                        # Also check for 'data' field
                        if "data" in output_file:
                            images.append({
                                "data": output_file["data"],
                                "mime_type": output_file.get("mime_type", "image/png"),
                                "source": "output_file_data"
                            })
            
            # Extract from code_execution_result
            if "code_execution_result" in obj:
                result = obj["code_execution_result"]
                if debug:
                    print(f"Found code_execution_result at {path}")
                if isinstance(result, dict):
                    if "output_files" in result:
                        for output_file in result.get("output_files", []):
                            if isinstance(output_file, dict):
                                if "contents" in output_file:
                                    images.append({
                                        "data": output_file["contents"],
                                        "mime_type": output_file.get("mime_type", "image/png"),
                                        "source": "code_exec_result"
                                    })
                                if "data" in output_file:
                                    images.append({
                                        "data": output_file["data"],
                                        "mime_type": output_file.get("mime_type", "image/png"),
                                        "source": "code_exec_result_data"
                                    })
            
            # Check for execution_result (Vertex AI Code Interpreter format)
            if "execution_result" in obj:
                exec_result = obj["execution_result"]
                if debug:
                    print(f"Found execution_result at {path}")
                if isinstance(exec_result, dict):
                    if "output_files" in exec_result:
                        for output_file in exec_result.get("output_files", []):
                            if isinstance(output_file, dict):
                                if "contents" in output_file:
                                    images.append({
                                        "data": output_file["contents"],
                                        "mime_type": output_file.get("mime_type", "image/png"),
                                        "source": "exec_result"
                                    })
            
            # Check for generatedFiles (another possible format)
            if "generatedFiles" in obj:
                if debug:
                    print(f"Found generatedFiles at {path}")
                for gen_file in obj.get("generatedFiles", []):
                    if isinstance(gen_file, dict):
                        if "uri" in gen_file:
                            file_uris.append(gen_file["uri"])
                        if "data" in gen_file:
                            images.append({
                                "data": gen_file["data"],
                                "mime_type": gen_file.get("mimeType", "image/png"),
                                "source": "generated_file"
                            })
            
            # Check for Parts with inlineData (Gemini API format)
            if "parts" in obj and isinstance(obj["parts"], list):
                for part in obj["parts"]:
                    if isinstance(part, dict) and "inlineData" in part:
                        inline = part["inlineData"]
                        if debug:
                            print(f"Found inlineData in parts at {path}")
                        if isinstance(inline, dict) and "data" in inline:
                            images.append({
                                "data": inline["data"],
                                "mime_type": inline.get("mimeType", "image/png"),
                                "source": "parts_inline"
                            })
            
            for k, v in obj.items():
                find_content(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_content(item, f"{path}[{i}]")
    
    find_content(data)
    
    # Get the last substantial text (usually the final response)
    final_text = ""
    for t in reversed(texts):
        if len(t) > 20:  # Get a meaningful response
            final_text = t
            break
    
    if not final_text and texts:
        final_text = texts[-1]
    
    return final_text or "Response received.", images, file_uris

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">🤖 Demand Planner Assistant</div>', unsafe_allow_html=True)
with col2:
    if st.session_state.session_id:
        st.markdown(f'<div class="session-badge">SESSION: {st.session_state.session_id[:8]}</div>', 
                   unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Session")
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.session_id = create_session()
        st.session_state.messages = []
        st.session_state.shown_artifacts = set()  # Reset shown artifacts
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📊 Quick Actions")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if st.button("🔮 Predict POS Sales", use_container_width=True):
        st.session_state.quick_action = f"Can you predict POS sales for {tomorrow}?"
    
    if st.button("📈 Show Sales Trend", use_container_width=True):
        st.session_state.quick_action = "Create a chart showing POS sales trend for the last 30 days"
    
    if st.button("🎯 Top Demand Drivers", use_container_width=True):
        st.session_state.quick_action = "What are the top demand drivers affecting POS sales? Show a bar chart."
    
    if st.button("➕ Insert Missing Data", use_container_width=True):
        st.session_state.quick_action = f"Insert demand driver data for {tomorrow}"
    
    st.markdown("---")
    
    st.markdown("### 🤖 ML Operations")
    
    if st.button("🏋️ Train New Model", use_container_width=True):
        st.session_state.quick_action = "Train a new BQML model to predict POS_sales"
    
    if st.button("📋 List Models", use_container_width=True):
        st.session_state.quick_action = "List all BQML models available"
    
    if st.button("📊 Model Metrics", use_container_width=True):
        st.session_state.quick_action = "Show evaluation metrics for pdm_model"
    
    st.markdown("---")
    
    st.markdown("### 📉 Analysis")
    
    if st.button("🔥 Correlation Heatmap", use_container_width=True):
        st.session_state.quick_action = "Create a correlation heatmap of all demand drivers vs POS sales"
    
    if st.button("🌡️ Weather Impact", use_container_width=True):
        st.session_state.quick_action = "Analyze how weather affects POS sales with a chart"

# Create session if none exists
if not st.session_state.session_id:
    st.session_state.session_id = create_session()

# Main chat area
st.markdown("---")

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div style="text-align: right;"><div class="user-message">{msg["content"]}</div></div>', 
                   unsafe_allow_html=True)
    else:
        # Show tool calls if any
        if msg.get("tool_calls"):
            tools_html = ""
            for tool in msg["tool_calls"]:
                tools_html += f'<span class="tool-call complete">✓ {tool}</span> '
            st.markdown(tools_html, unsafe_allow_html=True)
        
        # Show text response
        st.markdown(f'<div class="agent-message">', unsafe_allow_html=True)
        st.markdown(msg["text"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show images if any
        if msg.get("images"):
            for img_data in msg["images"]:
                display_image(img_data)
        
        # Show GCS file URIs if any
        if msg.get("file_uris"):
            for uri in msg["file_uris"]:
                if uri and ("png" in uri.lower() or "jpg" in uri.lower() or "jpeg" in uri.lower() or "image" in uri.lower()):
                    display_gcs_image(uri)
        
        # Show artifacts (charts from Code Interpreter)
        if msg.get("artifacts"):
            for artifact in msg["artifacts"]:
                try:
                    data = artifact.get("data")
                    if data and len(data) > 100:  # Valid image should be > 100 bytes
                        st.image(data, caption=artifact.get("name", "Chart"), use_container_width=True)
                        # Mark artifact as shown
                        if "key" in artifact:
                            st.session_state.shown_artifacts.add(artifact["key"])
                    else:
                        st.warning(f"Chart data too small or empty: {artifact.get('name', 'unknown')}")
                except Exception as e:
                    st.error(f"Could not display chart: {str(e)[:100]}")

# Handle quick actions
if st.session_state.quick_action:
    user_input = st.session_state.quick_action
    st.session_state.quick_action = None
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    st.markdown(f'<div style="text-align: right;"><div class="user-message">{user_input}</div></div>', 
               unsafe_allow_html=True)
    
    # Create status container
    status_container = st.empty()
    
    # Send message and get response
    response = send_message_with_events(st.session_state.session_id, user_input, status_container)
    
    # Add to history
    st.session_state.messages.append({
        "role": "assistant",
        "text": response["text"],
        "tool_calls": response["tool_calls"],
        "images": response["images"],
        "file_uris": response.get("file_uris", []),
        "artifacts": response.get("artifacts", [])
    })
    
    # Clear status and rerun to show full response
    status_container.empty()
    st.rerun()

# Chat input
user_input = st.chat_input("Ask about demand data, predictions, or analysis...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    st.markdown(f'<div style="text-align: right;"><div class="user-message">{user_input}</div></div>', 
               unsafe_allow_html=True)
    
    # Create status container
    status_container = st.empty()
    
    # Send message and get response
    response = send_message_with_events(st.session_state.session_id, user_input, status_container)
    
    # Add to history
    st.session_state.messages.append({
        "role": "assistant",
        "text": response["text"],
        "tool_calls": response["tool_calls"],
        "images": response["images"],
        "file_uris": response.get("file_uris", []),
        "artifacts": response.get("artifacts", [])
    })
    
    # Clear status and rerun to show full response
    status_container.empty()
    st.rerun()
