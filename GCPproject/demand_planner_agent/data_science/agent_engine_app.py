"""Agent Engine App configuration.

Tracing is enabled via environment variables (recommended approach):
- GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
- OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true

These are set in .agent_engine_env and passed during deployment.
"""
from vertexai.preview.reasoning_engines import AdkApp
from data_science.agent import root_agent

# Create AdkApp - tracing controlled by env vars, not the deprecated enable_tracing flag
adk_app = AdkApp(
    agent=root_agent,
    # Note: enable_tracing is deprecated, use GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY env var instead
)

