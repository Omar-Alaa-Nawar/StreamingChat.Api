"""
LLM Planner Service for StreamForge.

This service uses AWS Bedrock (Anthropic Claude 3.5 Haiku) to dynamically
plan and generate dashboard components based on natural language queries.

Phase 6: LLM-Driven Dynamic Component Generation
"""

import asyncio
import json
import logging
import hashlib
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    import aioboto3
    import botocore.exceptions
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

from utils.id_generator import generate_uuid7

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_planner")


class LLMPlannerService:
    """
    Service that uses an LLM to dynamically plan and generate StreamForge components.

    Features:
    - AWS Bedrock integration (Anthropic Claude 3.5 Haiku)
    - Intelligent component selection based on user intent
    - Caching for performance optimization
    - Retry logic with exponential backoff
    - Schema validation and error recovery
    - Fallback to default components on failure

    Usage:
        service = LLMPlannerService()
        layout = await service.generate_layout("show me sales trends")
        # Returns: {"components": [...], "from_cache": False, ...}
    """

    # Configuration constants
    BEDROCK_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    ANTHROPIC_VERSION = "bedrock-2023-05-31"
    APPLICATION_JSON = "application/json"
    MAX_RETRIES = 3
    CACHE_TTL_SECONDS = 3600
    AWS_REGION = "us-east-1"

    # Component validation rules
    REQUIRED_FIELDS = {
        "SimpleComponent": ["title"],
        "TableA": ["columns", "rows"],
        "ChartComponent": ["chart_type", "title", "x_axis", "series"]
    }

    VALID_CHART_TYPES = ["line", "bar", "area", "pie", "scatter"]
    MAX_COMPONENTS = 5
    MAX_TABLE_ROWS = 20
    MAX_CHART_POINTS = 50

    def __init__(self):
        """Initialize the LLM Planner Service."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._session = None

        if not BEDROCK_AVAILABLE:
            logger.warning(
                "AWS Bedrock dependencies not installed. "
                "Install with: pip install aioboto3 boto3 botocore"
            )

    def _calculate_backoff_time(self, attempt: int) -> float:
        """
        Calculate exponential backoff time for retry attempts.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            float: Wait time in seconds (2^attempt)

        Example:
            >>> service._calculate_backoff_time(0)  # 1 second
            >>> service._calculate_backoff_time(1)  # 2 seconds
            >>> service._calculate_backoff_time(2)  # 4 seconds
        """
        return 2 ** attempt

    async def generate_layout(self, user_message: str) -> Dict[str, Any]:
        """
        Interpret natural language and produce component layout plan.

        Args:
            user_message: User's natural language request

        Returns:
            Dict containing:
            - components: List of component dictionaries with type, id, data
            - from_cache: Whether result came from cache
            - processing_time_ms: Time taken to generate
            - model_id: Model used for generation

        Example:
            >>> result = await service.generate_layout("show me sales data")
            >>> print(result["components"])
            [
                {
                    "type": "SimpleComponent",
                    "id": "01932e4f-a4c2-7890-b123-456789abcdef",
                    "data": {"title": "Sales Summary", "description": "..."}
                },
                {
                    "type": "TableA",
                    "id": "01932e4f-a4c3-7890-b123-456789abcdef",
                    "data": {"columns": ["Region", "Revenue"], "rows": [...]}
                }
            ]
        """
        start_time = time.time()

        # Validate input
        if not user_message or not user_message.strip():
            logger.warning("Empty user message, returning fallback components")
            return self._create_fallback_response(start_time)

        # Check cache
        cache_key = self._generate_cache_key(user_message)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for message: {user_message[:50]}...")
            processing_time = (time.time() - start_time) * 1000
            return {
                **cached_result,
                "from_cache": True,
                "processing_time_ms": processing_time
            }

        # Check if Bedrock is available
        if not BEDROCK_AVAILABLE:
            logger.warning("Bedrock not available, using fallback components")
            return self._create_fallback_response(start_time)

        try:
            # Build planning prompt
            prompt = self._create_planning_prompt(user_message)

            # Call Bedrock API
            llm_response = await self._call_bedrock_api(prompt)

            # Parse and validate response
            components = self._parse_llm_response(llm_response)

            # Assign UUIDs and validate schemas
            validated_components = []
            for component in components[:self.MAX_COMPONENTS]:
                if self._validate_component_schema(component):
                    component["id"] = generate_uuid7()
                    validated_components.append(component)

            if not validated_components:
                logger.warning("No valid components after validation, using fallback")
                return self._create_fallback_response(start_time)

            # Build result
            processing_time = (time.time() - start_time) * 1000
            result = {
                "components": validated_components,
                "from_cache": False,
                "processing_time_ms": processing_time,
                "model_id": self.BEDROCK_MODEL_ID
            }

            # Store in cache
            self._store_in_cache(cache_key, result)

            logger.info(
                f"Generated {len(validated_components)} components "
                f"in {processing_time:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Error generating layout: {e}", exc_info=True)
            return self._create_fallback_response(start_time)

    def _create_planning_prompt(self, user_message: str) -> str:
        """
        Build the planning prompt for the LLM.

        Args:
            user_message: User's natural language request

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are StreamForge Planner, an AI agent that decides which dashboard components to create.

<task>
Given the user's request, determine which components (SimpleComponent, TableA, ChartComponent) best visualize it.
Return a JSON array inside $$$...$$$ where each object is a component plan.
</task>

<component_types>
1. SimpleComponent: Card/summary with title, description, optional value
   Example: {{"type":"SimpleComponent","data":{{"title":"Sales Summary","description":"Total revenue increased 12%","value":15000}}}}

2. TableA: Tabular data with columns and rows
   Example: {{"type":"TableA","data":{{"columns":["Region","Revenue"],"rows":[["US",12000],["EU",10000]]}}}}

3. ChartComponent: Line/bar/area/pie/scatter charts
   Example: {{"type":"ChartComponent","data":{{"chart_type":"line","title":"Revenue Over Time","x_axis":["Jan","Feb","Mar"],"series":[{{"label":"Sales","values":[100,120,150]}}]}}}}
</component_types>

<rules>
- Return 1-5 components maximum
- Choose component types based on data visualization needs
- For trends/time-series: use ChartComponent (line)
- For comparisons: use ChartComponent (bar)
- For lists/detailed data: use TableA
- For summaries/KPIs: use SimpleComponent
- Provide realistic sample data
- Ensure proper JSON structure
</rules>

<required_format>
$$$[
  {{"type":"SimpleComponent","data":{{"title":"Sales Summary","description":"Total revenue increased 12%"}}}},
  {{"type":"TableA","data":{{"columns":["Region","Revenue"],"rows":[["US",12000],["EU",10000]]}}}},
  {{"type":"ChartComponent","data":{{"chart_type":"line","title":"Revenue Over Time","x_axis":["Jan","Feb"],"series":[{{"label":"Sales","values":[100,120]}}]}}}}
]$$$
</required_format>

Output only the $$$ JSON array $$$ with no extra text.

<user_request>
{user_message}
</user_request>"""

        return prompt

    async def _call_bedrock_api(self, prompt: str) -> str:
        """
        Call AWS Bedrock API with retries and exponential backoff.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            LLM response text

        Raises:
            Exception: If all retries fail
        """
        if self._session is None:
            self._session = aioboto3.Session()

        for attempt in range(self.MAX_RETRIES):
            try:
                async with self._session.client(
                    service_name='bedrock-runtime',
                    region_name=self.AWS_REGION
                ) as bedrock_client:

                    # Prepare request body for Claude
                    request_body = {
                        "anthropic_version": self.ANTHROPIC_VERSION,
                        "max_tokens": 4096,
                        "temperature": 0.3,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }

                    logger.info(
                        f"Calling Bedrock API (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )

                    # Invoke model
                    response = await bedrock_client.invoke_model(
                        modelId=self.BEDROCK_MODEL_ID,
                        contentType=self.APPLICATION_JSON,
                        accept=self.APPLICATION_JSON,
                        body=json.dumps(request_body)
                    )

                    # Parse response
                    response_body = json.loads(await response['body'].read())

                    if 'content' in response_body and len(response_body['content']) > 0:
                        llm_text = response_body['content'][0]['text']
                        logger.info(f"Received response from Bedrock: {len(llm_text)} chars")
                        return llm_text
                    else:
                        raise ValueError("Invalid response format from Bedrock")

            except botocore.exceptions.ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                logger.warning(
                    f"Bedrock API error (attempt {attempt + 1}): {error_code}"
                )

                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self._calculate_backoff_time(attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise

            except Exception as e:
                logger.error(f"Unexpected error calling Bedrock: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self._calculate_backoff_time(attempt))
                else:
                    raise

        raise Exception(f"Failed to call Bedrock after {self.MAX_RETRIES} attempts")

    def _parse_llm_response(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response and extract component JSON.

        Handles:
        - Extracting JSON from $$$ delimiters
        - Removing markdown code blocks
        - Fixing common JSON errors
        - Validating array structure

        Args:
            llm_response: Raw LLM response text

        Returns:
            List of component dictionaries

        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Extract content between $$$ delimiters
        match = re.search(r'\$\$\$(.*?)\$\$\$', llm_response, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
        else:
            # Try to find JSON array without delimiters
            json_text = llm_response.strip()

        # Remove markdown code blocks
        json_text = re.sub(r'^```json\s*', '', json_text)
        json_text = re.sub(r'^```\s*', '', json_text)
        json_text = re.sub(r'\s*```$', '', json_text)
        json_text = json_text.strip()

        # Fix common JSON errors
        # Replace single quotes with double quotes
        json_text = json_text.replace("'", '"')

        # Parse JSON
        try:
            components = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Failed JSON text: {json_text[:500]}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

        # Validate it's a list
        if not isinstance(components, list):
            logger.warning("LLM response is not a list, wrapping in array")
            components = [components]

        logger.info(f"Parsed {len(components)} components from LLM response")
        return components

    def _validate_component_schema(self, component: Dict[str, Any]) -> bool:
        """
        Validate component structure and required fields.

        Args:
            component: Component dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check basic structure
        if not isinstance(component, dict):
            logger.warning("Component is not a dictionary")
            return False

        if "type" not in component:
            logger.warning("Component missing 'type' field")
            return False

        if "data" not in component:
            logger.warning(f"Component missing 'data' field: {component['type']}")
            return False

        component_type = component["type"]
        component_data = component["data"]

        # Validate component type
        if component_type not in self.REQUIRED_FIELDS:
            logger.warning(f"Unknown component type: {component_type}")
            return False

        # Check required fields for type
        required = self.REQUIRED_FIELDS[component_type]
        for field in required:
            if field not in component_data:
                logger.warning(
                    f"{component_type} missing required field: {field}"
                )
                return False

        # Type-specific validation
        if component_type == "TableA":
            columns = component_data.get("columns", [])
            rows = component_data.get("rows", [])

            if not isinstance(columns, list) or not columns:
                logger.warning("TableA columns must be non-empty list")
                return False

            if not isinstance(rows, list):
                logger.warning("TableA rows must be a list")
                return False

            # Limit rows
            if len(rows) > self.MAX_TABLE_ROWS:
                logger.info(f"Truncating table rows from {len(rows)} to {self.MAX_TABLE_ROWS}")
                component_data["rows"] = rows[:self.MAX_TABLE_ROWS]

            # Validate row structure
            for row in component_data["rows"]:
                if not isinstance(row, list):
                    logger.warning("TableA row is not a list")
                    return False

        elif component_type == "ChartComponent":
            chart_type = component_data.get("chart_type")
            if chart_type not in self.VALID_CHART_TYPES:
                logger.warning(f"Invalid chart_type: {chart_type}")
                return False

            x_axis = component_data.get("x_axis", [])
            series = component_data.get("series", [])

            if not isinstance(x_axis, list):
                logger.warning("ChartComponent x_axis must be a list")
                return False

            if not isinstance(series, list) or not series:
                logger.warning("ChartComponent series must be non-empty list")
                return False

            # Validate series structure
            for s in series:
                if not isinstance(s, dict):
                    logger.warning("ChartComponent series item must be dict")
                    return False
                if "label" not in s or "values" not in s:
                    logger.warning("ChartComponent series missing label or values")
                    return False
                if not isinstance(s["values"], list):
                    logger.warning("ChartComponent series values must be list")
                    return False

                # Limit data points
                if len(s["values"]) > self.MAX_CHART_POINTS:
                    logger.info(f"Truncating chart points from {len(s['values'])} to {self.MAX_CHART_POINTS}")
                    s["values"] = s["values"][:self.MAX_CHART_POINTS]

        return True

    def _generate_cache_key(self, user_message: str) -> str:
        """Generate cache key from user message using SHA-256 hash."""
        normalized = user_message.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if not expired."""
        if cache_key not in self._cache:
            return None

        cached_entry = self._cache[cache_key]
        expiry_time = cached_entry.get("expiry")

        if expiry_time and datetime.now() > expiry_time:
            # Cache expired
            del self._cache[cache_key]
            logger.info("Cache entry expired and removed")
            return None

        logger.info("Cache hit")
        return cached_entry.get("result")

    def _store_in_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in cache with TTL."""
        expiry = datetime.now() + timedelta(seconds=self.CACHE_TTL_SECONDS)
        self._cache[cache_key] = {
            "result": result,
            "expiry": expiry
        }
        logger.info(f"Stored result in cache (TTL: {self.CACHE_TTL_SECONDS}s)")

    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Cache cleared")

    def _create_fallback_response(self, start_time: float) -> Dict[str, Any]:
        """
        Create fallback response with default components.

        Args:
            start_time: Request start time for metrics

        Returns:
            Fallback response dictionary
        """
        components = self._create_fallback_components()
        processing_time = (time.time() - start_time) * 1000

        return {
            "components": components,
            "from_cache": False,
            "processing_time_ms": processing_time,
            "model_id": "fallback",
            "fallback": True
        }

    def _create_fallback_components(self) -> List[Dict[str, Any]]:
        """
        Create default fallback components when LLM fails.

        Returns:
            List of default components
        """
        return [
            {
                "type": "SimpleComponent",
                "id": generate_uuid7(),
                "data": {
                    "title": "Dashboard Summary",
                    "description": "Welcome to StreamForge. Your data will appear here.",
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "type": "TableA",
                "id": generate_uuid7(),
                "data": {
                    "columns": ["Metric", "Value", "Status"],
                    "rows": [
                        ["Total Users", "1,234", "Active"],
                        ["Revenue", "$45,678", "Up 12%"],
                        ["Conversion Rate", "3.2%", "Stable"]
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "type": "ChartComponent",
                "id": generate_uuid7(),
                "data": {
                    "chart_type": "line",
                    "title": "Sample Trend",
                    "x_axis": ["Jan", "Feb", "Mar", "Apr", "May"],
                    "series": [
                        {
                            "label": "Metric",
                            "values": [100, 120, 150, 140, 180]
                        }
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]
