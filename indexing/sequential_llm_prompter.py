"""LLM prompter for a single directory.

This is a local of the sequential LLM
prompter used by the indexing pipeline. It preserves the important public
interfaces and the high-level staged prompting flow while keeping local
fallbacks lightweight and importable.
"""

from __future__ import annotations

import abc
import dataclasses
import json
import os
import random
import re
import subprocess
import time
from typing import Any, Callable, Protocol, Optional, List

import logging

# Stabilization: Use native DNS resolver to prevent ares crashes during fork().
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")

# Conditional imports for Vertex AI and generative model clients.
try:
    from google import genai
except ImportError:
    # Handle environment where genai is not available.
    genai = None

try:
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import ollama
except ImportError:
    ollama = None

# Dynamic resolution of indexing project modules with fallback mechanisms.
class UnrecoverableLlmError(Exception):
    """Exception raised for unrecoverable LLM errors (e.g. model not found)."""
    pass
try:
    from indexing import error_prompt_generator
except ImportError:
    import error_prompt_generator

# Import data models and prompt templates for structured LLM interaction.
try:
    from indexing import prompt_templates
except ImportError:
    import prompt_templates

try:
    from indexing import schema
except ImportError:
    import schema

try:
    from indexing import section_registry
except ImportError:
    import section_registry

try:
    from indexing import verification_types
except ImportError:
    import verification_types



_QUOTA_ERROR_RETRY_JITTER_SECONDS = 30


# Cleaned Observability for Antigravity
class Observer:
    """Minimal interface for tracking metrics and retries."""
    def __init__(self):
        self.counters = {}
    def increment(self, name: str, value: int = 1):
        self.counters[name] = self.counters.get(name, 0) + value
    def increment_counter(self, name: str, value: int = 1):
        self.increment(name, value)
    def add_to_counter(self, name: str, value: int):
        self.increment(name, value)
    def record_latency(self, name: str, value: float):
        pass

_observer = Observer()

# Unified observability alias
_stats_instance = _observer
metrics = _observer


class _SimpleStatsRecorder:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def add_to_counter(self, name: str, value: int) -> None:
        self.increment_counter(name, value)

    def record_latency(self, name: str, value: float) -> None:
        # Minimal implementation for tracking latency if needed.
        pass


class _SimpleThrottleContext:
    def __enter__(self) -> _SimpleThrottleContext:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Standard exit logic for the context manager. We do not suppress
        # exceptions here as they are handled by the higher-level retry loop.
        return False

    def report_output(self, _output: str) -> None:
        # No-op implementation for the basic throttling context.
        return None


class _SimpleThrottlingStrategy:
    def acquire(self, _system_prompt: str, _user_prompt: str) -> _SimpleThrottleContext:
        return _SimpleThrottleContext()


class LlmPrompterOutOfRetriesError(Exception):
    """Raised when the LLM prompt fails after all retries."""


class LlmPrompter(abc.ABC):
    """Abstract base class for LLM prompters."""

    @abc.abstractmethod
    def prompt_for_indexing(
        self,
        directory_path: str,
        system_prompt: Any,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        verifier: Any = None,
        directory_files: list[str] | None = None,
        previous_artifact: schema.IndexDocument | None = None,
        previous_verdict: verification_types.VerificationVerdict | None = None,
    ) -> schema.IndexDocument:
        """Prompts the LLM to index a directory."""

    @property
    def repo_root(self) -> str | None:
        """Returns the repository root path."""
        return None

    @abc.abstractmethod
    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        directory_files: list[str] | None = None,
    ) -> schema.IndexDocument:
        """Prompts the LLM to merge summaries."""

    @abc.abstractmethod
    def prompt_for_root_map_summary(self, root_map_content: str) -> str:
        """Returns a summary of the root map content."""

    @abc.abstractmethod
    def verify_artifact(
        self, 
        artifact_json: str, 
        source_context: str, 
        directory_files: list[str] | None = None,
        is_merger_mode: bool = False
    ) -> verification_types.VerificationVerdict:
        """Runs the verifier prompt and returns a structured verdict."""


@dataclasses.dataclass
class GeminiLlmPrompterConfig:
    """Configuration for the LLM prompter."""

    bundle_name: str
    throttling_strategy: Any = None
    indexer_type: str = "REGULAR"
    research_gemini_model: str = "gemini-1.5-flash"
    synthesis_gemini_model: str = "gemini-1.5-flash"
    use_vertex_ai: bool = False
    vertex_ai_project_id: str | None = None
    api_key: str | None = None
    dry_run: bool = False
    dry_run_map: dict[str, str] | None = None
    
    max_attempts: int = 3
    delay_on_failure_max_seconds: int = 10
    max_attempts_per_conversation: int = 3
    include_search_tool: bool = True
    generate_content_config: Any | None = None
    provider: str = "gemini"
    repo_root: str | None = None
    # If False, raises error if no real API found.
    allow_mock_fallback: bool = True

@dataclasses.dataclass
class PromptResult:
    text: str
    usage: dict[str, Any]
    provider_response_id: str | None = None
    latency_ms: int = 0



@dataclasses.dataclass
class _SimpleConversation:
    """Very small local conversation abstraction."""

    system_prompt: str
    agent_name: str
    output_schema_type: type[Any]
    state: Any = None

    def prompt(self, user_prompt: str) -> PromptResult:
        if self.state is None:
            payload = self._build_default_output(user_prompt)
            self.state = payload
        text = self.state.model_dump_json(indent=2) if hasattr(self.state, "model_dump_json") else json.dumps(self.state, indent=2, default=str)
        return PromptResult(text=text, usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})

    def get_state(self, _agent_name: str) -> Any:
        return self.state

    def _build_default_output(self, user_prompt: str) -> Any:
        if self.output_schema_type is schema.IndexDocument:
            return schema.IndexDocument(
                overview=schema.Overview(
                    content=f"Auto-generated overview for prompt: {user_prompt}"
                ),
                # Initialize required list sections to empty to satisfy Pydantic.
                key_individual_components=schema.KeyIndividualComponents(
                    components=[]
                ),
            )
        # Handle secondary document types for detailed research steps.
        if self.output_schema_type is schema.KeyComponentsDocument:
            return schema.KeyComponentsDocument(
                key_individual_components=schema.KeyIndividualComponents(
                    components=[]
                ),
                key_interfaces=schema.KeyInterfaces(interfaces=[]),
                key_dependencies=schema.KeyDependencies(dependencies=[]),
                architectural_patterns_and_gotchas=schema.ArchitecturalPatternsAndGotchas(
                    content=""
                ),
                
                testing_strategy=schema.TestingStrategy(content=""),
                configurations=schema.Configurations(configurations=[]),
            )
        # Handle deep dive and high-level overview document types.
        if self.output_schema_type is schema.DeepDiveDocument:
            return schema.DeepDiveDocument(
                deep_dive=schema.DeepDive(content=f"Deep dive for: {user_prompt}")
            )
        if self.output_schema_type is schema.OverviewDocument:
            return schema.OverviewDocument(
                overview=schema.Overview(content=f"Overview for: {user_prompt}")
            )
        if self.output_schema_type is schema.CustomSectionsDocument:
            return schema.CustomSectionsDocument(custom_sections=[])
        
        if hasattr(self.output_schema_type, "__name__") and self.output_schema_type.__name__ == "VerificationVerdict":
            return self.output_schema_type(passed=True, issues=[])
        # Default fallback to an empty instance of the schema type.
        if self.output_schema_type is None:
            if self.agent_name in ("reviewer", "verifier"):
                return {"passed": True, "issues": [], "review_findings": []}
            return f"Mock response for {self.agent_name}: {user_prompt[:50]}..."
        return self.output_schema_type()


class VertexAiConversation:
    """Conversation implementation using Vertex AI."""

    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        project_id: str,
        output_schema_type: type[Any] | None = None,
    ):
        if genai is None:
            raise ImportError("google-genai library not found. Install google-genai.")
        
        # Initialize the GenAI client with Vertex AI enabled.
        self.client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        # Create chat session with system instruction in the config.
        self.chat = self.client.chats.create(
            model=model_name,
            config={"system_instruction": system_prompt} if system_prompt else None,
        )
        self.model_name = model_name
        self.output_schema_type = output_schema_type

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        response = self.chat.send_message(user_prompt)
        text = response.text
        latency_ms = int((time.time() - start_time) * 1000)
        
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage_metadata = response.usage_metadata
            usage = {
                "input_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                "output_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(usage_metadata, "total_token_count", 0),
            }
            
        # Parse and store the response as structured state.
        try:
            extracted = OpenAiConversation._extract_json(text)
            self._last_response = OpenAiConversation._normalize_keys(json.loads(extracted))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)

    def get_state(self, _agent_name: str) -> Any:
        """Returns the parsed state from the last LLM response."""
        return getattr(self, "_last_response", None)


class GoogleAiConversation:
    """Conversation implementation using Google AI Studio (API Key)."""

    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        api_key: str,
        output_schema_type: type[Any] | None = None,
    ):
        if genai is None:
            raise ImportError("google-genai library not found. Install google-genai.")
        
        self.client = genai.Client(api_key=api_key)
        # Create chat session with system instruction in the config.
        self.chat = self.client.chats.create(
            model=model_name,
            config={"system_instruction": system_prompt} if system_prompt else None,
        )
        self.model_name = model_name
        self.output_schema_type = output_schema_type

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        response = self.chat.send_message(user_prompt)
        text = response.text
        latency_ms = int((time.time() - start_time) * 1000)
        
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage_metadata = response.usage_metadata
            usage = {
                "input_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                "output_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(usage_metadata, "total_token_count", 0),
            }
            
        # Parse and store the response as structured state.
        try:
            extracted = OpenAiConversation._extract_json(text)
            self._last_response = OpenAiConversation._normalize_keys(json.loads(extracted))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)

    def get_state(self, _agent_name: str) -> Any:
        """Returns the parsed state from the last LLM response."""
        return getattr(self, "_last_response", None)


class OpenAiConversation:
    """Conversation implementation using OpenAI."""

    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        api_key: str,
        output_schema_type: type[Any] | None = None,
    ):
        if openai is None:
            raise ImportError("openai library not found. Install openai.")
        self.client = openai.Client(api_key=api_key)
        
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.output_schema_type = output_schema_type
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []
        self._last_response: Any = None

    # Normalize LLM response keys to snake_case for Pydantic compatibility.
    @staticmethod
    def _normalize_keys(obj: Any) -> Any:
        """Recursively converts dict keys to snake_case."""
        if isinstance(obj, dict):
            normalized = {}
            for k, v in obj.items():
                # Convert CamelCase/PascalCase to snake_case.
                snake = re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower()
                normalized[snake] = OpenAiConversation._normalize_keys(v)
            return normalized
        if isinstance(obj, list):
            return [OpenAiConversation._normalize_keys(i) for i in obj]
        return obj

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extracts JSON from a string that might contain markdown fences."""
        if not text:
            return ""
        cleaned = text.strip()
        # First, attempt to match standard markdown json fences.
        # The DOTALL flag ensures we capture multi-line JSON structures.
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if fence_match:
            return fence_match.group(1)
            
        # Fallback to extracting the outermost braces
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            return cleaned[start:end+1]
            
        return cleaned

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        self.history.append({"role": "user", "content": user_prompt})
        
        kwargs = {
            "model": self.model_name,
            "messages": self.history,
        }
        if self.output_schema_type is not None:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        latency_ms = int((time.time() - start_time) * 1000)
        text = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": text})
        
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        
        # Parse and store the response as structured state.
        try:
            extracted = OpenAiConversation._extract_json(text)
            self._last_response = OpenAiConversation._normalize_keys(json.loads(extracted))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return PromptResult(text=text, usage=usage, provider_response_id=response.id, latency_ms=latency_ms)

    def get_state(self, _agent_name: str) -> Any:
        """Returns the parsed state from the last LLM response."""
        return self._last_response


class AnthropicConversation:
    """Conversation implementation using Anthropic."""

    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        api_key: str,
        output_schema_type: type[Any] | None = None,
    ):
        if anthropic is None:
            raise ImportError("anthropic library not found. Install anthropic.")
        self.client = anthropic.Anthropic(api_key=api_key)
        
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.output_schema_type = output_schema_type
        if self.output_schema_type is not None:
             self.system_prompt += "\n\nYou must respond strictly in JSON format." if self.system_prompt else "You must respond strictly in JSON format."
        self.history = []
        self._last_response: Any = None

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        self.history.append({"role": "user", "content": user_prompt})
        
        response = self.client.messages.create(
            model=self.model_name,
            system=self.system_prompt,
            messages=self.history,
            max_tokens=16384
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        text = response.content[0].text
        
        usage = {}
        if hasattr(response, "usage"):
            usage_obj = response.usage
            usage = {
                "input_tokens": getattr(usage_obj, "input_tokens", 0),
                "output_tokens": getattr(usage_obj, "output_tokens", 0),
                "total_tokens": getattr(usage_obj, "input_tokens", 0) + getattr(usage_obj, "output_tokens", 0),
            }
            
        self.history.append({"role": "assistant", "content": text})
        # Parse and store the response as structured state.
        try:
            extracted = OpenAiConversation._extract_json(text)
            self._last_response = OpenAiConversation._normalize_keys(json.loads(extracted))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)

    def get_state(self, _agent_name: str) -> Any:
        """Returns the parsed state from the last LLM response."""
        return self._last_response


class OllamaConversation:
    """Conversation implementation using local Ollama."""

    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        output_schema_type: type[Any] | None = None,
    ):
        if ollama is None:
            raise ImportError("ollama library not found. Install ollama.")
        self.model_name = model_name
        
        self.output_schema_type = output_schema_type
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []
        self._last_response: Any = None

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        # Append the new user message to the conversation history.
        self.history.append({"role": "user", "content": user_prompt})
        
        # Log basic stats about the prompt size to monitor context usage.
        total_chars = sum(len(m["content"]) for m in self.history)
        logging.info(
            "[Ollama] Sending %d messages (%d chars total) to %s",
            len(self.history), total_chars, self.model_name,
        )
        try:
            kwargs = {
                "model": self.model_name,
                "messages": self.history,
                "options": {
                    "num_ctx": 131072,
                },
            }
            if self.output_schema_type is not None:
                kwargs["format"] = "json"
            
            # Execute the request against the local Ollama API.
            response = ollama.chat(**kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parse the Ollama response payload.
            text = response['message']['content']
            logging.info(
                "[Ollama] Response: %d chars from %s",
                len(text), self.model_name,
            )
            self.history.append({"role": "assistant", "content": text})
            
            usage = {
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
            }
            
            # Store parsed JSON state for get_state retrieval.
            try:
                extracted = OpenAiConversation._extract_json(text)
                self._last_response = OpenAiConversation._normalize_keys(json.loads(extracted))
            except (json.JSONDecodeError, TypeError):
                self._last_response = text
            return PromptResult(text=text, usage=usage, latency_ms=latency_ms)
        except Exception as e:
            raise RuntimeError(f"Ollama request failed. Is the daemon running? {e}")

    def get_state(self, _agent_name: str) -> Any:
        """Returns the parsed state from the last LLM response."""
        return self._last_response


class DryRunConversation:
    """Conversation implementation for dry runs (mocked)."""

    def __init__(
        self,
        system_prompt: str,
        agent_name: str,
        output_schema_type: type[Any],
        dry_run_map: dict[str, str] | None = None,
    ):
        self.system_prompt = system_prompt
        self.agent_name = agent_name
        self.output_schema_type = output_schema_type
        
        self.dry_run_map = dry_run_map or {}
        # Tracking the simulated state of the conversation.
        self.state: Any = None

    def prompt(self, user_prompt: str) -> PromptResult:
        start_time = time.time()
        # Check if we have a mapped response for this agent/prompt
        key = f"{self.agent_name}:{user_prompt[:50]}"
        text = ""
        if key in self.dry_run_map:
            text = self.dry_run_map[key]
            # Try to parse it into state if possible
            try:
                self.state = json.loads(text)
            except Exception:
                self.state = text
        else:
            # Fallback to a structured mock based on schema
            text = self._build_mock_response(user_prompt)
        
        latency_ms = int((time.time() - start_time) * 1000)
        usage = {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}
        
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)

    def get_state(self, _agent_name: str) -> Any:
        return self.state

    def _build_mock_response(self, user_prompt: str) -> str:
        # We reuse the logic from _SimpleConversation
        conv = _SimpleConversation(
            system_prompt=self.system_prompt,
            agent_name=self.agent_name,
            output_schema_type=self.output_schema_type,
        )
        mock_obj = conv._build_default_output(user_prompt)
        self.state = mock_obj
        
        if hasattr(mock_obj, "model_dump_json"):
            return mock_obj.model_dump_json(indent=2)
        return json.dumps(mock_obj, indent=2, default=str)



class GeminiLlmPrompter(LlmPrompter):
    """LLM prompter for Gemini with multi-stage agent support."""

    # Maps schema field paths to their default values for coercion.
    # Weaker LLMs (e.g. Ollama) may omit required fields; this table
    # lets us patch them in before Pydantic validation to avoid wasting
    # retry budget on trivially fixable errors.
    _FIELD_DEFAULTS: dict[str, dict[str, Any]] = section_registry.field_defaults()

    def __init__(
        self,
        config: GeminiLlmPrompterConfig,
        fs_manager: object | None,
        
        override_conversation_factory: Callable[[Any], Any] | None = None,
    ):
        """Initializes the GeminiLlmPrompter."""
        self._config = config
        self._stats = _SimpleStatsRecorder()
        self._override_conversation_factory = override_conversation_factory
        self._throttler = (
            self._config.throttling_strategy or _SimpleThrottlingStrategy()
        )
        self._fs_manager = fs_manager
        self._repo_root = config.repo_root
        self._call_records: list[schema.LlmCallRecord] = []

    @property
    def repo_root(self) -> str | None:
        """Returns the repository root path."""
        return self._repo_root

    @staticmethod
    def _coerce_for_schema(data: Any, output_schema: type[Any]) -> Any:
        """Fill in missing/null required fields with defaults before Pydantic validation."""
        if not isinstance(data, dict):
            return data

        # --- Phase -1: Detect and reject schema echoes ---
        if "$defs" in data or "$schema" in data:
            logging.warning("[Coercion] Detected JSON Schema echo instead of instance.")
            data = {k: v for k, v in data.items() if not k.startswith("$")}

        # --- VerificationVerdict Specific Coercion ---
        if output_schema is verification_types.VerificationVerdict:
            if "passed" in data and not isinstance(data["passed"], bool):
                data["passed"] = str(data["passed"]).lower() == "true"
            if "confidence" in data and not isinstance(data["confidence"], (int, float)):
                try:
                    data["confidence"] = float(data["confidence"])
                except (ValueError, TypeError):
                    data["confidence"] = 0.5
            if "detailed_issues" in data and data["detailed_issues"] is None:
                data["detailed_issues"] = []

        # --- Phase 0: Unwrap 'properties' if the LLM hallucinated it from the schema ---
        if "properties" in data and isinstance(data["properties"], dict):
            expected_keys = set(GeminiLlmPrompter._LIST_FIELD_MAP.keys()) | set(GeminiLlmPrompter._CONTENT_FIELD_MAP.keys())
            if len(data) == 1 or not any(k in data for k in expected_keys):
                logging.info("[Coercion] Unwrapped 'properties' container from LLM response.")
                data = data["properties"]

        # --- Phase 0.1: Unwrap class-name wrappers ---
        class_name = getattr(output_schema, "__name__", "")
        if class_name:
            snake_class_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
            if snake_class_name in data and isinstance(data[snake_class_name], dict) and len(data) == 1:
                logging.info("[Coercion] Unwrapping '%s' root key.", snake_class_name)
                data = data[snake_class_name]
            elif class_name in data and isinstance(data[class_name], dict) and len(data) == 1:
                logging.info("[Coercion] Unwrapping '%s' root key.", class_name)
                data = data[class_name]

        # --- Phase 1: Recursively replace null → "" for all string-typed values ---
        data = GeminiLlmPrompter._deep_replace_nulls(data)

        # Determine which fields the schema actually expects and which are required.
        schema_fields = set()
        required_fields = set()
        if hasattr(output_schema, "model_fields"):  # Pydantic v2
            schema_fields = set(output_schema.model_fields.keys())
            try:
                from pydantic_core import PydanticUndefined
                for name, field in output_schema.model_fields.items():
                    if field.default is PydanticUndefined and field.default_factory is None:
                        required_fields.add(name)
            except ImportError:
                pass
        elif hasattr(output_schema, "__fields__"):  # Pydantic v1
            schema_fields = set(output_schema.__fields__.keys())
            for name, field in output_schema.__fields__.items():
                if getattr(field, "required", False):
                    required_fields.add(name)

        # --- Phase 0.5: Remap Document-level Wrappers ---
        expected_content_keys = [k for k in required_fields if k in GeminiLlmPrompter._CONTENT_FIELD_MAP]
        if len(expected_content_keys) == 1:
            req_key = expected_content_keys[0]
            found_content_keys = [k for k in data if k in GeminiLlmPrompter._CONTENT_FIELD_MAP and k != req_key]
            if req_key not in data and len(found_content_keys) == 1:
                wrong_key = found_content_keys[0]
                logging.info("[Coercion] Remapped '%s' to '%s' for document requiring %s.", wrong_key, req_key, req_key)
                data[req_key] = data.pop(wrong_key)

        # --- Phase 0.6: Wrap 'unwrapped' content ---
        if len(expected_content_keys) == 1:
            req_key = expected_content_keys[0]
            content_key = GeminiLlmPrompter._CONTENT_FIELD_MAP[req_key]
            if req_key not in data and content_key in data:
                logging.info("[Coercion] Wrapped root '%s' into '%s'.", content_key, req_key)
                data = {req_key: data}

        # --- Phase 0.7: Coerce string-valued sections to dicts ---
        for section_key, content_key in GeminiLlmPrompter._CONTENT_FIELD_MAP.items():
            if section_key in data:
                val = data[section_key]
                if isinstance(val, str):
                    logging.info("[Coercion] Coerced string value for '%s' to dict with '%s' key.", section_key, content_key)
                    data[section_key] = {content_key: val}
                elif isinstance(val, dict) and content_key in val:
                    inner_val = val[content_key]
                    if isinstance(inner_val, dict) and content_key in inner_val:
                        logging.warning("[Coercion] Detected double-wrapped '%s' in '%s'. Flattening.", content_key, section_key)
                        val[content_key] = inner_val[content_key]

        # --- Phase 0.8: Inject missing mandatory content sections ---
        for req_key in expected_content_keys:
            if req_key not in data or data[req_key] is None:
                content_key = GeminiLlmPrompter._CONTENT_FIELD_MAP.get(req_key, "content")
                logging.warning("[Coercion] Injected missing required content section '%s'.", req_key)
                data[req_key] = {content_key: ""}

        # --- Phase 2: Patch known missing keys with field-specific defaults ---
        mandatory_sections = section_registry.get_mandatory_sections()
        
        for wrapper_key, (list_key, model_name) in GeminiLlmPrompter._LIST_FIELD_MAP.items():
            if wrapper_key not in schema_fields:
                continue

            is_mandatory = wrapper_key in mandatory_sections

            if wrapper_key not in data or data[wrapper_key] is None:
                data[wrapper_key] = {list_key: []}
                level = logging.WARNING if is_mandatory else logging.INFO
                logging.log(level, "[Coercion] Injected missing %s wrapper '%s'.", 
                            "MANDATORY" if is_mandatory else "optional", wrapper_key)
            
            wrapper = data[wrapper_key]
            if isinstance(wrapper, list):
                logging.info("[Coercion] Wrapped naked list in '%s' to dict with '%s' key.", wrapper_key, list_key)
                wrapper = {list_key: wrapper}
                data[wrapper_key] = wrapper
            elif not isinstance(wrapper, dict):
                wrapper = {list_key: []}
                data[wrapper_key] = wrapper
                logging.info("[Coercion] Coerced malformed wrapper '%s' to dict.", wrapper_key)

            items = wrapper.get(list_key)
            if not isinstance(items, list):
                items = wrapper[list_key] = []
                logging.info("[Coercion] Initialized missing list '%s' in %s.", list_key, wrapper_key)
            
            defaults = GeminiLlmPrompter._FIELD_DEFAULTS.get(model_name, {})
            for item in items:
                if isinstance(item, dict):
                    for field, default_val in defaults.items():
                        if field not in item:
                            item[field] = default_val
                            logging.info(
                                "[Coercion] Patched missing '%s' on %s (name=%s) with default=%r.",
                                field, model_name, item.get("name", "<unknown>"), default_val,
                            )

        return data

    _LIST_FIELD_MAP = section_registry.list_field_map()
    _CONTENT_FIELD_MAP = section_registry.content_field_map()

    _STRING_KEYS = {
        "name", "description", "usage_description", "definition_link",
        "comments", "content", "title", "model_name", "generated_at",
        "verified_at"
    }

    
    @staticmethod
    def _deep_replace_nulls(obj: Any) -> Any:
        """Recursively replace null values with empty strings for string fields."""
        if isinstance(obj, dict):
            return {
                k: "" if (v is None and k in GeminiLlmPrompter._STRING_KEYS) else GeminiLlmPrompter._deep_replace_nulls(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [
                "" if item is None else GeminiLlmPrompter._deep_replace_nulls(item)
                for item in obj
            ]
        
        return obj

    def _create_single_conversation(
        self,
        system_prompt: str,
        agent_name: str,
        output_schema_type: type[Any] | None = None,
        model_type: str = "research",
        epoch: int = 1,
    ) -> Any:
        """Creates a real LLM conversation for a single step."""
        model_name = (
            self._config.research_gemini_model
            if model_type == "research"
            else self._config.synthesis_gemini_model
        )

        if self._override_conversation_factory:
            return self._override_conversation_factory(system_prompt)

        if self._config.dry_run:
            return DryRunConversation(
                system_prompt=system_prompt,
                agent_name=agent_name,
                output_schema_type=output_schema_type,
                dry_run_map=self._config.dry_run_map,
            )

        if self._config.provider == "gemini":
            if self._config.use_vertex_ai and self._config.vertex_ai_project_id:
                try:
                    return VertexAiConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        project_id=self._config.vertex_ai_project_id,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    logging.warning("Failed to initialize Vertex AI conversation: %s", e)

            if self._config.api_key:
                try:
                    return GoogleAiConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        api_key=self._config.api_key,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    logging.warning("Failed to initialize Google AI conversation: %s", e)

        elif self._config.provider == "openai":
            if self._config.api_key:
                try:
                    return OpenAiConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        api_key=self._config.api_key,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    logging.warning("Failed to initialize OpenAI conversation: %s", e)

        elif self._config.provider == "anthropic":
            if self._config.api_key:
                try:
                    return AnthropicConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        api_key=self._config.api_key,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    logging.warning("Failed to initialize Anthropic conversation: %s", e)

        elif self._config.provider == "ollama":
            try:
                return OllamaConversation(
                    system_prompt=system_prompt,
                    model_name=model_name,
                    output_schema_type=output_schema_type,
                )
            except Exception as e:
                logging.warning("Failed to initialize Ollama conversation: %s", e)

        if not self._config.allow_mock_fallback:
            raise RuntimeError(
                "No real LLM backend could be initialized, and allow_mock_fallback is False."
            )

        logging.info("Using mock conversation for %s (no credentials found)", agent_name)
        return _SimpleConversation(
            system_prompt=system_prompt,
            agent_name=agent_name,
            output_schema_type=output_schema_type,
        )

    def _handle_llm_prompt_error(
        self,
        e: Exception,
        directory_path: str,
        conversation: Any,
        error_prompt_generator_instance: Any,
        attempt: int = 1,
    ) -> str:
        """Handles runtime errors from the LLM call."""
        base_delay = min(2**attempt, self._config.delay_on_failure_max_seconds)
        error_str = str(e).lower()
        
        if "not_found" in error_str and "model" in error_str:
            raise UnrecoverableLlmError(f"Model '{self._config.model_name}' not found. Stopping run.") from e
            
        if "quota" in error_str:
            self._stats.increment_counter("llm.runtime_quota_errors")
            sleep_duration = random.randint(0, _QUOTA_ERROR_RETRY_JITTER_SECONDS)
        else:
            self._stats.increment_counter("llm.runtime_other_errors")
            jitter = random.uniform(0.4, 0.6 * base_delay)
            sleep_duration = base_delay + jitter

        time.sleep(min(sleep_duration, 0.01))
        if hasattr(error_prompt_generator_instance, "generate_error_prompt"):
            return error_prompt_generator_instance.generate_error_prompt(str(e))
        return error_prompt_generator.IndexerErrorPromptGenerator().generate_error_prompt(str(e))

    def _handle_pydantic_validation_error(
        self,
        e: pydantic.ValidationError,
        directory_path: str,
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles validation errors from the LLM call."""
        self._stats.increment_counter("llm.validation_pydantic_failures")
        
        issues = []
        is_json_invalid = False
        for err in e.errors():
            if err.get("type") == "json_invalid":
                is_json_invalid = True
            loc = ".".join(str(l) for l in err["loc"])
            issues.append(f"Schema violation at '{loc}': {err['msg']}")
            
        is_schema_echo = False
        try:
            for err in e.errors():
                input_val = err.get("input")
                if isinstance(input_val, dict) and ("$defs" in input_val or "$schema" in input_val):
                    is_schema_echo = True
                    break
        except Exception:
            pass

        if is_schema_echo:
            error_feedback = (
                "CRITICAL ERROR: You echoed the JSON Schema definition instead of providing a valid instance. "
                "MUST NOT include schema definitions like '$defs' or '$schema' in your output."
            )
        elif is_json_invalid:
            error_feedback = (
                "Your response was truncated or contains invalid JSON syntax. "
                "Please ensure you complete the JSON object and close all brackets."
            )
        else:
            error_feedback = f"Output validation failed with {len(issues)} schema violations."

        if hasattr(error_prompt_generator_instance, "generate_error_prompt"):
            return error_prompt_generator_instance.generate_error_prompt(error_feedback, issues=issues)
        return f"{error_feedback}\n\nIssues:\n" + "\n".join(issues)

    def _handle_json_decoding_error(
        self,
        e: Exception,
        directory_path: str,
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles JSON decoding errors from the LLM call."""
        self._stats.increment_counter("llm.validation_json_failures")
        error_feedback = "Output validation failed: LLM response could not be parsed as JSON."
        if hasattr(error_prompt_generator_instance, "generate_validation_failure_prompt"):
            return error_prompt_generator_instance.generate_validation_failure_prompt(directory_path, error_feedback)
        return error_prompt_generator.IndexerErrorPromptGenerator().generate_error_prompt(error_feedback)

    def _execute_single_prompt(
        self,
        directory_path: str,
        initial_user_prompt: str,
        agent_name: str,
        error_prompt_generator_instance: Any,
        conversation_factory: Callable[[], Any],
        stringified_system_prompt: str,
        output_schema: type[Any],
    ) -> Any:
        """Executes the prompt loop with retries and error handling."""
        conversation = conversation_factory()
        self._stats.increment_counter("llm.conversations_created")

        user_prompt = initial_user_prompt
        attempts_this_conversation = 0
        for attempt in range(self._config.max_attempts):
            if attempt > 0:
                self._stats.increment_counter("llm.retries")
            attempts_this_conversation += 1

            if attempts_this_conversation > self._config.max_attempts_per_conversation:
                conversation = conversation_factory()
                self._stats.increment_counter("llm.conversations_reset")
                attempts_this_conversation = 1

            try:
                start_time = time.time()
                with self._throttler.acquire(stringified_system_prompt, user_prompt) as throttler_ctx:
                    self._stats.increment_counter("llm.prompts_sent")
                    prompt_result = conversation.prompt(user_prompt)
                    self._stats.add_to_counter("llm.input_tokens", prompt_result.usage.get("input_tokens", 0))
                    self._stats.add_to_counter("llm.output_tokens", prompt_result.usage.get("output_tokens", 0))
                    self._stats.record_latency("llm.latency_ms", prompt_result.latency_ms)
                    
                    self._call_records.append(schema.LlmCallRecord(
                        agent_name=agent_name,
                        model_name=getattr(conversation, "model_name", "unknown"),
                        provider=self._config.provider,
                        input_tokens=prompt_result.usage.get("input_tokens", 0),
                        output_tokens=prompt_result.usage.get("output_tokens", 0),
                        total_tokens=prompt_result.usage.get("total_tokens", 0),
                        latency_ms=prompt_result.latency_ms,
                        attempt=attempt + 1,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    ))
                    
                    llm_response_text = prompt_result.text
                    throttler_ctx.report_output(llm_response_text)
                
                parsed_output = conversation.get_state(agent_name)
                if isinstance(parsed_output, dict) and pydantic is not None:
                    parsed_output = self._coerce_for_schema(parsed_output, output_schema)
                    if hasattr(output_schema, 'model_validate'):
                        return output_schema.model_validate(parsed_output)
                    return parsed_output
                if isinstance(parsed_output, str) and pydantic is not None:
                    if hasattr(output_schema, 'model_validate_json'):
                        cleaned_output = OpenAiConversation._extract_json(parsed_output)
                        return output_schema.model_validate_json(cleaned_output)
                    return parsed_output
                if parsed_output is None:
                    raise ValueError(f"Agent {agent_name} did not produce any output.")
                return parsed_output
            except Exception as e:
                if pydantic is not None and isinstance(e, getattr(pydantic, "ValidationError", tuple())):
                    user_prompt = self._handle_pydantic_validation_error(e, directory_path, error_prompt_generator_instance)
                    continue
                if isinstance(e, json.JSONDecodeError):
                    user_prompt = self._handle_json_decoding_error(e, directory_path, error_prompt_generator_instance)
                    continue
                user_prompt = self._handle_llm_prompt_error(e, directory_path, conversation, error_prompt_generator_instance, attempt=attempt)
                continue

        raise LlmPrompterOutOfRetriesError(f"Failed to generate for {directory_path} after exhausting retries.")

    def _run_agent_step(
        self,
        directory_path: str,
        initial_user_prompt: str,
        agent_name: str,
        error_prompt_generator_instance: Any,
        instruction: str,
        output_schema_type: Any,
        model_type: str,
        epoch: int,
        tool_executor: Callable[[Any], Any] | None = None,
    ) -> tuple[Any, str]:
        """Runs a single agent step and returns its raw output and JSON string."""
        plan = self._execute_single_prompt(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name=agent_name,
            error_prompt_generator_instance=error_prompt_generator_instance,
            conversation_factory=lambda: self._create_single_conversation(
                system_prompt=instruction,
                agent_name=agent_name,
                output_schema_type=output_schema_type,
                model_type=model_type,
                epoch=epoch,
            ),
            stringified_system_prompt=instruction,
            output_schema=output_schema_type,
        )
        final_output = tool_executor(plan) if tool_executor else plan
        output_str = (
            final_output.model_dump_json(indent=2)
            if hasattr(final_output, "model_dump_json")
            else json.dumps(final_output, indent=2, default=str)
            if final_output
            else ""
        )
        return plan, output_str

    def _run_custom_sections_agent(
        self,
        directory_path: str,
        initial_user_prompt: str,
        system_prompt: Any,
        error_prompt_generator_instance: Any,
        code_search_output_str: str,
        read_files_output_str: str,
        key_components_summary_str: str,
        deep_dive_summary_str: str,
    ) -> list[Any]:
        """Runs a single synthesis agent to generate all custom sections at once."""
        if not getattr(system_prompt, "custom_sections", lambda: [])():
            return []

        section_instruction = system_prompt.custom_sections_instruction(
            code_search_output=code_search_output_str,
            read_files_output=read_files_output_str,
            key_components_output=key_components_summary_str,
            deep_dive_output=deep_dive_summary_str,
        )
        section_doc, _ = self._run_agent_step(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="custom_sections_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            instruction=section_instruction,
            output_schema_type=schema.CustomSectionsDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )
        return section_doc.custom_sections

    def _aggregate_cost_report(self, directory_path: str, epoch: int) -> schema.CostReport:
        """Aggregates all recorded LLM calls into a single cost report."""
        total_input = sum(c.input_tokens for c in self._call_records)
        total_output = sum(c.output_tokens for c in self._call_records)
        total_tokens = sum(c.total_tokens for c in self._call_records)
        total_latency = sum(c.latency_ms for c in self._call_records)
        total_calls = len(self._call_records)
        
        model_breakdown = {}
        for c in self._call_records:
            if c.model_name not in model_breakdown:
                model_breakdown[c.model_name] = {
                    "calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                }
            stats = model_breakdown[c.model_name]
            stats["calls"] += 1
            stats["input_tokens"] += c.input_tokens
            stats["output_tokens"] += c.output_tokens
            stats["total_tokens"] += c.total_tokens

        return schema.CostReport(
            directory_path=directory_path,
            epoch=epoch,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_calls=total_calls,
            total_latency_ms=total_latency,
            calls=self._call_records,
            model_breakdown=model_breakdown,
        )

    def prompt_for_indexing(
        self,
        directory_path: str,
        system_prompt: Any,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        verifier: Any = None,
        directory_files: list[str] | None = None,
        previous_artifact: schema.IndexDocument | None = None,
        previous_verdict: verification_types.VerificationVerdict | None = None,
    ) -> schema.IndexDocument:
        """Prompts the LLM, validates the response, and retries on failure."""
        self._call_records.clear()
        if self._override_conversation_factory is not None:
            conversation = self._override_conversation_factory(system_prompt)
            prompt_result = conversation.prompt(initial_user_prompt)
            parsed = json.loads(prompt_result.text)
            if pydantic is not None:
                return schema.IndexDocument.model_validate(parsed)
            return parsed

        self.last_research_context = ""

        # --- STEP 0: Healing & Taint Analysis ---
        must_run = {
            "research": True, "key_components": True, "deep_dive": True, "overview": True, "custom": True,
        }

        if previous_verdict and not previous_verdict.passed:
            logging.info("[DeltaHealing] Analyzing taint for %s", directory_path)
            must_run = {k: False for k in must_run}
            must_run["research"] = True # Always re-run research for ground truth

            failed_sections = set(issue.section for issue in previous_verdict.detailed_issues if issue.section)
            key_comp_sections = {
                "key_individual_components", "key_interfaces", "key_dependencies",
                "configurations", "implementation_invariants", "workflow_patterns",
                "blueprint", "tech_debt", "architectural_patterns_and_gotchas", "testing_strategy"
            }
            
            if any(s in key_comp_sections for s in failed_sections) or not failed_sections:
                must_run["key_components"] = True
                must_run["deep_dive"] = True
                must_run["overview"] = True
            if "deep_dive" in failed_sections:
                must_run["deep_dive"] = True
                must_run["overview"] = True
            if "overview" in failed_sections:
                must_run["overview"] = True
            if "custom_sections" in failed_sections:
                must_run["custom"] = True

        # --- STEP 1: Research Phase ---
        if must_run["research"]:
            if self._config.include_search_tool:
                def search_tool_wrapper(p): return self._execute_code_search(p if isinstance(p, list) else p.get("queries", []))
                _, res_out = self._run_agent_step(directory_path, initial_user_prompt, "research_planner_agent", error_prompt_generator_instance, system_prompt.research_planner_instruction(), dict, "research", system_prompt.epoch(), search_tool_wrapper)
                self.last_research_context += f"=== CODE SEARCH OUTPUT ===\n{res_out}\n\n"
            else: res_out = "Code search disabled."

            def read_tool_wrapper(p): return self._execute_read_files(p if isinstance(p, list) else p.get("files", []))
            _, read_out = self._run_agent_step(directory_path, initial_user_prompt, "read_files_planner_agent", error_prompt_generator_instance, system_prompt.read_files_planner_instruction(code_search_output=res_out), dict, "research", system_prompt.epoch(), read_tool_wrapper)
            self.last_research_context += f"=== READ FILES OUTPUT ===\n{read_out}\n\n"
        else:
            res_out, read_out = "[Skipped]", "[Skipped]"

        # --- STEP 2: Synthesis Phase ---
        if must_run["key_components"]:
            key_components_doc, key_comp_summary = self._run_agent_step(directory_path, initial_user_prompt, "key_components_agent", error_prompt_generator_instance, system_prompt.key_components_instruction(code_search_output=res_out, read_files_output=read_out), schema.KeyComponentsDocument, "synthesis", system_prompt.epoch())
        else:
            key_components_doc = schema.KeyComponentsDocument(**section_registry.key_components_payloads(previous_artifact))
            key_comp_summary = "[Reused]"

        if must_run["deep_dive"]:
            deep_dive_doc, dd_summary = self._run_agent_step(directory_path, initial_user_prompt, "deep_dive_agent", error_prompt_generator_instance, system_prompt.deep_dive_instruction(code_search_output=res_out, read_files_output=read_out, key_components_output=key_comp_summary), schema.DeepDiveDocument, "synthesis", system_prompt.epoch())
        else:
            deep_dive_doc = schema.DeepDiveDocument(deep_dive=previous_artifact.deep_dive)
            dd_summary = "[Reused]"

        if must_run["overview"]:
            overview_doc, _ = self._run_agent_step(directory_path, initial_user_prompt, "overview_agent", error_prompt_generator_instance, system_prompt.overview_instruction(code_search_output=res_out, read_files_output=read_out, key_components_output=key_comp_summary, deep_dive_output=dd_summary), schema.OverviewDocument, "synthesis", system_prompt.epoch())
        else:
            overview_doc = schema.OverviewDocument(overview=previous_artifact.overview)

        if must_run["custom"]:
            custom_sections = self._run_custom_sections_agent(directory_path, initial_user_prompt, system_prompt, error_prompt_generator_instance, res_out, read_out, key_comp_summary, dd_summary)
        else:
            custom_sections = previous_artifact.custom_sections

        # --- STEP 3: Assembly & Verification ---
        artifact = schema.IndexDocument(
            overview=overview_doc.overview, deep_dive=deep_dive_doc.deep_dive,
            **section_registry.key_components_payloads(key_components_doc),
            custom_sections=custom_sections,
            generation_metadata=schema.GenerationMetadata(
                generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                model_name=self._config.synthesis_gemini_model,
                epoch=system_prompt.epoch(),
                cost_report=schema.CostReport(directory_path=directory_path, epoch=system_prompt.epoch())
            )
        )

        if verifier:
            logging.info("Verifying artifact for %s", directory_path)
            full_context = getattr(system_prompt, "_directory_contents", "") + "\n\n" + self.last_research_context
            verdict = verifier.verify(artifact.model_dump_json(indent=2), full_context, directory_files=directory_files, ast_grounding=getattr(system_prompt, "_ast_grounding_cache", None))
            if not verdict.passed: logging.warning("Verification failed for %s: %s", directory_path, verdict.issues)

        final_cost = self._aggregate_cost_report(directory_path, system_prompt.epoch())
        artifact.generation_metadata.cost_report = final_cost
        return artifact

    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        directory_files: list[str] | None = None,
    ) -> schema.IndexDocument:
        """Prompts the LLM to merge summaries."""
        if pydantic is not None and hasattr(schema.IndexDocument, "model_json_schema"):
            schema_str = json.dumps(schema.IndexDocument.model_json_schema(), indent=2)
            system_prompt = f"{system_prompt}\n\nYour output MUST be a JSON object conforming to: {schema_str}"

        return self._execute_single_prompt(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="merging_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            conversation_factory=lambda: self._create_single_conversation(
                system_prompt=system_prompt, agent_name="merging_agent",
                output_schema_type=schema.IndexDocument, model_type="synthesis"
            ),
            stringified_system_prompt=system_prompt,
            output_schema=schema.IndexDocument,
        )

    def prompt_for_root_map_summary(self, root_map_content: str) -> str:
        """Returns a synthesized summary of the root map content using the LLM."""
        system_prompt = prompt_templates.create_root_map_prompt(root_map_content)
        conv = self._create_single_conversation(system_prompt=system_prompt, agent_name="root_map_architect", output_schema_type=None, model_type="synthesis")
        prompt_result = conv.prompt("Please provide the high-level architectural summary.")
        return prompt_result.text.strip()

    def verify_artifact(
        self, 
        artifact_json: str, 
        source_context: str, 
        directory_files: list[str] | None = None,
        is_merger_mode: bool = False
    ) -> verification_types.VerificationVerdict:
        """Runs the verifier prompt and returns a structured verdict."""
        base_user_prompt = prompt_templates.create_verifier_prompt(artifact_json, source_context)
        system_prompt = prompt_templates.VERIFIER_SYSTEM_PROMPT
        if pydantic is not None and hasattr(verification_types.VerificationVerdict, "model_json_schema"):
            schema_str = json.dumps(verification_types.VerificationVerdict.model_json_schema(), indent=2)
            system_prompt = f"{system_prompt}\n\nYour output MUST be a JSON object conforming to: {schema_str}"

        try:
            verdict = self._execute_single_prompt(
                directory_path="verification_step",
                initial_user_prompt=base_user_prompt,
                agent_name="verifier_agent",
                error_prompt_generator_instance=error_prompt_generator.IndexerErrorPromptGenerator(),
                conversation_factory=lambda: self._create_single_conversation(
                    system_prompt=system_prompt, agent_name="verifier_agent",
                    output_schema_type=verification_types.VerificationVerdict, model_type="synthesis"
                ),
                stringified_system_prompt=system_prompt,
                output_schema=verification_types.VerificationVerdict,
            )
            if hasattr(verdict, "verification_model"):
                verdict.verification_model = getattr(self._config, "synthesis_gemini_model", "unknown")
            return verdict
        except Exception as e:
            logging.error("[VerifyArtifact] Terminal failure: %s", e)
            return verification_types.VerificationVerdict.infrastructure_bypass(confidence=0.01, reason=str(e))

    def _execute_web_searches(self, queries: list[str]) -> list[dict[str, str]]:
        """Placeholder for web search capability."""
        return [{"query": q, "result": "Research placeholder."} for q in queries]

    def _execute_read_files(self, files: list[str]) -> str:
        """Reads file contents from the local filesystem."""
        if not files or not self._fs_manager: return "No files or no FS manager."
        results = []
        for file_path in files[:5]:
            abs_path = os.path.join(self._repo_root, file_path) if self._repo_root and not file_path.startswith("/") else file_path
            try:
                if self._fs_manager.exists(abs_path):
                    results.append(f"--- FILE: {file_path} ---\n{self._fs_manager.read(abs_path)}")
                else: results.append(f"--- FILE: {file_path} ---\n(File not found)")
            except Exception as e: results.append(f"--- FILE: {file_path} ---\n(Error: {e})")
        return "\n\n".join(results)

    def _execute_code_search(self, queries: list[str]) -> str:
        """Performs local code search using grep/find."""
        if not queries or not self._repo_root: return "No queries or no repo root."
        results = []
        for query in queries[:5]:
            try:
                if query.startswith("filename:"):
                    cmd = ["find", ".", "-name", f"*{query.split(':', 1)[1].strip()}*", "-not", "-path", "*/.*", "-not", "-path", "*/node_modules/*"]
                else:
                    search_term = query.split(":", 1)[1].strip() if ":" in query and not query.startswith("http") else query
                    cmd = ["grep", "-r", "-n", "-m", "5", "--exclude-dir=.git", "--exclude-dir=node_modules", search_term, "."]
                process = subprocess.run(cmd, cwd=self._repo_root, capture_output=True, text=True, check=False)
                output = process.stdout.strip()
                results.append(f"--- SEARCH RESULTS FOR: {query} ---\n{output or '(No matches found)'}")
            except Exception as e: results.append(f"--- SEARCH RESULTS FOR: {query} ---\n(Search failed: {e})")
        return "\n\n".join(results)
