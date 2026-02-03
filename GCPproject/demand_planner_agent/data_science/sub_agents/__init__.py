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

# Lazy imports to support Agent Engine deployment
# Individual agents should be imported within functions that use them
# Note: AlloyDB agent removed - not used in this deployment
from .analytics.agent import get_analytics_agent
from .bigquery.agent import get_bigquery_agent
from .bqml.agent import get_bqml_agent
from .research.agent import research_agent

# For backwards compatibility - use get_*_agent() functions instead
bigquery_agent = None
bqml_agent = None  # Use get_bqml_agent() function instead
analytics_agent = None
alloydb_agent = None  # Placeholder - AlloyDB not used
