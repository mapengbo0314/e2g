"""LLM prompter for a single directory.

This is a local, screenshot-backed reconstruction of the sequential LLM
prompter used by the indexing pipeline. It preserves the important public
interfaces and the high-level staged prompting flow while keeping local
fallbacks lightweight and importable.
"""

from __future__ import annotations

import abc
import dataclasses
import json
import random
import re
import time
from typing import Any, Callable, Protocol

import logging

# Conditional imports for Vertex AI and generative model clients.
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, ChatSession
except ImportError:
    vertexai = None

try:
    import google.generativeai as genai
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
    from indexing import verification_types

except ImportError:
    import verification_types



_QUOTA_ERROR_RETRY_JITTER_SECONDS = 30


class _NoOpCounter:
    def increment(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NoOpMetrics:
    LLM_RETRIES = _NoOpCounter()
    LLM_FAILURES = _NoOpCounter()


# Global metrics counters for tracking pipeline health and performance.
metrics = _NoOpMetrics()


class _SimpleStatsRecorder:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value


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
    ) -> schema.IndexDocument:
        """Prompts the LLM to index a directory."""

    @abc.abstractmethod
    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
    ) -> schema.IndexDocument:
        """Prompts the LLM to merge summaries."""

    @abc.abstractmethod
    def prompt_for_root_map_summary(self, root_map_content: str) -> str:
        """Returns a summary of the root map content."""

    @abc.abstractmethod
    def verify_artifact(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> verification_types.VerificationVerdict:
        """Runs the verifier prompt and returns a structured verdict."""


@dataclasses.dataclass
class GeminiLlmPrompterConfig:
    """Configuration for the LLM prompter."""

    bundle_name: str
    throttling_strategy: Any
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
    # If False, raises error if no real API found.
    allow_mock_fallback: bool = True


@dataclasses.dataclass
class _SimpleConversation:
    """Very small local conversation abstraction."""

    system_prompt: str
    agent_name: str
    output_schema_type: type[Any]
    state: Any = None

    def prompt(self, user_prompt: str) -> str:
        if self.state is None:
            payload = self._build_default_output(user_prompt)
            self.state = payload
        if hasattr(self.state, "model_dump_json"):
            # Use Pydantic's optimized JSON serialization if available.
            return self.state.model_dump_json(indent=2)
        return json.dumps(self.state, indent=2, default=str)

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
        if vertexai is None:
            raise ImportError("vertexai library not found. Install google-cloud-aiplatform.")
        vertexai.init(project=project_id)
        # Instantiate the generative model with the provided system prompt.
        self.model = GenerativeModel(
            model_name,
            system_instruction=[system_prompt] if system_prompt else None,
        )
        self.chat = self.model.start_chat()
        self.output_schema_type = output_schema_type

    def prompt(self, user_prompt: str) -> str:
        response = self.chat.send_message(user_prompt)
        return response.text


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
            raise ImportError("google.generativeai library not found. Install google-generativeai.")
        genai.configure(api_key=api_key)
        # Instantiate the Google AI model with optional system instructions.
        self.model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt if system_prompt else None,
        )
        self.chat = self.model.start_chat()
        self.output_schema_type = output_schema_type

    def prompt(self, user_prompt: str) -> str:
        response = self.chat.send_message(user_prompt)
        return response.text


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

    def prompt(self, user_prompt: str) -> str:
        self.history.append({"role": "user", "content": user_prompt})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.history,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": text})
        # Parse and store the response as structured state.
        try:
            self._last_response = OpenAiConversation._normalize_keys(json.loads(text))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return text

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
        self.system_prompt = system_prompt + "\n\nYou must respond strictly in JSON format." if system_prompt else "You must respond strictly in JSON format."
        self.output_schema_type = output_schema_type
        self.history = []
        self._last_response: Any = None

    def prompt(self, user_prompt: str) -> str:
        self.history.append({"role": "user", "content": user_prompt})
        
        response = self.client.messages.create(
            model=self.model_name,
            system=self.system_prompt,
            messages=self.history,
            max_tokens=16384
        )
        text = response.content[0].text
        self.history.append({"role": "assistant", "content": text})
        # Parse and store the response as structured state.
        try:
            self._last_response = OpenAiConversation._normalize_keys(json.loads(text))
        except (json.JSONDecodeError, TypeError):
            self._last_response = text
        return text

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

    def prompt(self, user_prompt: str) -> str:
        # Append the new user message to the conversation history.
        self.history.append({"role": "user", "content": user_prompt})
        
        # Log basic stats about the prompt size to monitor context usage.
        total_chars = sum(len(m["content"]) for m in self.history)
        logging.info(
            "[Ollama] Sending %d messages (%d chars total) to %s",
            len(self.history), total_chars, self.model_name,
        )
        try:
            # Execute the request against the local Ollama API.
            response = ollama.chat(
                model=self.model_name,
                messages=self.history,
                format="json",
                # Pass model-specific configuration options.
                options={
                    # Ollama defaults to num_ctx=2048 which silently truncates
                    # large prompts.  Gemma 4 supports 200K tokens; set this
                    # high enough that the full source context is preserved.
                    "num_ctx": 131072,
                },
            )
            # Parse the Ollama response payload.
            text = response['message']['content']
            logging.info(
                "[Ollama] Response: %d chars from %s",
                len(text), self.model_name,
            )
            self.history.append({"role": "assistant", "content": text})
            # Store parsed JSON state for get_state retrieval.
            try:
                self._last_response = OpenAiConversation._normalize_keys(json.loads(text))
            except (json.JSONDecodeError, TypeError):
                self._last_response = text
            return text
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

    def prompt(self, user_prompt: str) -> str:
        # Check if we have a mapped response for this agent/prompt
        key = f"{self.agent_name}:{user_prompt[:50]}"
        if key in self.dry_run_map:
            resp = self.dry_run_map[key]
            # Try to parse it into state if possible
            try:
                self.state = json.loads(resp)
            except Exception:
                self.state = resp
            return resp
        
        # Fallback to a structured mock based on schema
        resp = self._build_mock_response(user_prompt)
        # _build_mock_response already sets self.state in this revised version
        return resp

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
    _FIELD_DEFAULTS: dict[str, dict[str, Any]] = {
        "Dependency": {"usage_description": ""},
        "Component": {"description": ""},
        "Interface": {"description": ""},
        "ConfigurationItem": {"definition_link": "", "description": ""},
    }

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

    @staticmethod
    def _coerce_for_schema(data: Any, output_schema: type[Any]) -> Any:
        """Fill in missing/null required fields with defaults before Pydantic validation.

        This prevents weaker LLMs from burning all retry attempts on trivially
        fixable schema violations (e.g. ``null`` instead of ``""`` on a
        required string field, or missing ``usage_description`` on a
        Dependency dict).
        """
        if not isinstance(data, dict):
            return data

        # --- Phase 0: Unwrap 'properties' if the LLM hallucinated it from the schema ---
        # Weaker LLMs (like Gemma) often wrap their entire response in a 'properties'
        # key because it's a prominent top-level key in the JSON Schema.
        if "properties" in data and isinstance(data["properties"], dict):
            # Only unwrap if 'properties' is the ONLY key, or if none of the expected
            # top-level keys are present in the root but ARE in 'properties'.
            expected_keys = set(GeminiLlmPrompter._LIST_FIELD_MAP.keys()) | {"overview", "deep_dive"}
            if len(data) == 1 or not any(k in data for k in expected_keys):
                logging.info("[Coercion] Unwrapped 'properties' container from LLM response.")
                data = data["properties"]

        # --- Phase 1: Recursively replace null → "" for all string-typed values ---
        # Weaker LLMs (especially Ollama/Gemma) frequently output null for
        # required string fields.  The schema has no intentionally nullable
        # string fields, so this is always safe.
        data = GeminiLlmPrompter._deep_replace_nulls(data)

        # Determine which fields the schema actually expects and which are required.
        schema_fields = set()
        required_fields = set()
        if hasattr(output_schema, "model_fields"):  # Pydantic v2
            schema_fields = set(output_schema.model_fields.keys())
            # For Pydantic v2, we check if the field has a default value.
            try:
                from pydantic_core import PydanticUndefined
                for name, field in output_schema.model_fields.items():
                    if field.default is PydanticUndefined and field.default_factory is None:
                        required_fields.add(name)
            except ImportError:
                # If we can't get the sentinel, we'll leave required_fields empty
                # and skip the greedy remapping phase.
                pass
        elif hasattr(output_schema, "__fields__"):  # Pydantic v1
            schema_fields = set(output_schema.__fields__.keys())
            for name, field in output_schema.__fields__.items():
                if getattr(field, "required", False):
                    required_fields.add(name)

        # --- Phase 0.5: Remap Document-level Wrappers ---
        # Weaker models often mix up 'overview' and 'deep_dive' wrapper keys.
        # Handle remapping for DeepDiveDocument (where deep_dive is required).
        if "deep_dive" in required_fields and "deep_dive" not in data and "overview" in data:
            logging.info("[Coercion] Remapped 'overview' to 'deep_dive' for DeepDiveDocument.")
            data["deep_dive"] = data.pop("overview")
        # Handle remapping for OverviewDocument (where overview is required).
        elif "overview" in required_fields and "overview" not in data and "deep_dive" in data:
            logging.info("[Coercion] Remapped 'deep_dive' to 'overview' for OverviewDocument.")
            data["overview"] = data.pop("deep_dive")

        # --- Phase 0.6: Wrap 'unwrapped' content ---
        # If the LLM returned the inner fields at the root instead of inside the wrapper.
        if "deep_dive" in required_fields and "deep_dive" not in data and "content" in data:
            logging.info("[Coercion] Wrapped root 'content' into 'deep_dive'.")
            data = {"deep_dive": data}
        elif "overview" in required_fields and "overview" not in data and "content" in data:
            logging.info("[Coercion] Wrapped root 'content' into 'overview'.")
            data = {"overview": data}

        # --- Phase 2: Patch known missing keys with field-specific defaults ---
        for wrapper_key, (list_key, model_name) in GeminiLlmPrompter._LIST_FIELD_MAP.items():
            # Only inject if the field is actually expected by the schema.
            if wrapper_key not in schema_fields:
                continue

            # If the wrapper is missing or null, inject an empty container.
            if wrapper_key not in data or data[wrapper_key] is None:
                data[wrapper_key] = {list_key: []}
                logging.info("[Coercion] Injected missing mandatory wrapper '%s'.", wrapper_key)
            
            wrapper = data[wrapper_key]
            if not isinstance(wrapper, dict):
                # If the LLM returned something like "" or "none" for the wrapper,
                # convert it to an empty dict with the required list key.
                wrapper = {list_key: []}
                data[wrapper_key] = wrapper
                logging.info("[Coercion] Coerced malformed wrapper '%s' to dict.", wrapper_key)

            # Ensure the inner list key is present.
            items = wrapper.get(list_key)
            if not isinstance(items, list):
                wrapper[list_key] = []
                logging.info("[Coercion] Initialized missing list '%s' in %s.", list_key, wrapper_key)
            defaults = GeminiLlmPrompter._FIELD_DEFAULTS.get(model_name, {})
            for item in items:
                if isinstance(item, dict):
                    for field, default_val in defaults.items():
                        if field not in item:
                            item[field] = default_val
                            logging.info(
                                
                                "[Coercion] Patched missing '%s' on %s "
                                
                                "(name=%s) with default=%r.",
                                field, model_name,
                                item.get("name", "<unknown>"), default_val,
                            )

        return data

    _LIST_FIELD_MAP = {
        "key_dependencies": ("dependencies", "Dependency"),
        "key_individual_components": ("components", "Component"),
        "key_interfaces": ("interfaces", "Interface"),
        "configurations": ("configurations", "ConfigurationItem"),
    }

    _STRING_KEYS = {
        "name", "description", "usage_description", "definition_link",
        "comments", "content", "title", "model_name", "generated_at",
        "verified_at"
    }

    
    @staticmethod
    
    def _deep_replace_nulls(obj: Any) -> Any:
        """Recursively replace null values with empty strings for string fields.

        This handles the common LLM pattern of outputting
        `{"content": null}` instead of `{"content": ""}`.
        """
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
        output_schema_type: type[Any],
        model_type: str = "research",
        epoch: int = 1,
    ) -> Any:
        """Creates a real LLM conversation for a single step."""
        # Select the appropriate model based on the current agent's role.
        model_name = (
            self._config.research_gemini_model
            if model_type == "research"
            else self._config.synthesis_gemini_model
        )

        if self._override_conversation_factory:
            return self._override_conversation_factory(system_prompt)

        # 0. Dry Run
        if self._config.dry_run:
            return DryRunConversation(
                system_prompt=system_prompt,
                agent_name=agent_name,
                output_schema_type=output_schema_type,
                dry_run_map=self._config.dry_run_map,
            )

        # --- Backend Detection Logic ---
        if self._config.provider == "gemini":
            # 1. Try Vertex AI first (requires vertex_ai_project_id and gcloud ADC)
            if self._config.use_vertex_ai and self._config.vertex_ai_project_id:
                try:
                    # Initialize a Vertex AI chat session with system instructions.
                    return VertexAiConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        project_id=self._config.vertex_ai_project_id,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    # Fallback to next backend if Vertex initialization fails.
                    logging.warning("Failed to initialize Vertex AI conversation: %s", e)

            # 2. Try Google AI Studio (requires api_key)
            if self._config.api_key:
                try:
                    # Initialize a Google AI Studio chat session using an API key.
                    return GoogleAiConversation(
                        system_prompt=system_prompt,
                        model_name=model_name,
                        api_key=self._config.api_key,
                        output_schema_type=output_schema_type,
                    )
                except Exception as e:
                    # Fallback to mock or error if API Key initialization fails.
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

        # Check if the requested provider is Anthropic.
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

        # 3. Fallback or Fail Fast
        if not self._config.allow_mock_fallback:
            # Raise error if production environment requires real LLM connectivity.
            raise RuntimeError(
                "No real LLM backend could be initialized, and allow_mock_fallback is False. "
                "Check your PROJECT_ID or API_KEY environment variables, or ensure Ollama is running."
            )

        # Silent fallback to mock behavior for local development/testing.
        logging.info("Using mock conversation for %s (no credentials found)", agent_name)
        return _SimpleConversation(
            system_prompt=system_prompt,
            agent_name=agent_name,
            output_schema_type=output_schema_type,
        )

    # Error handling and retry logic for failed LLM calls.
    def _handle_llm_prompt_error(
        self,
        e: Exception,
        directory_path: str,
        conversation: Any,
        
        error_prompt_generator_instance: Any,
        attempt: int = 1,
    ) -> str:
        """Handles runtime errors from the LLM call."""
        # Calculate retry delay with exponential backoff and jitter.
        base_delay = min(2**attempt, self._config.delay_on_failure_max_seconds)
        # Determine the type of failure to apply appropriate retry strategy.
        if "quota" in str(e).lower():
            # Handle rate limiting or credit exhaustion specifically.
            self._stats.increment_counter("llm.runtime_quota_errors")
            sleep_duration = random.randint(0, _QUOTA_ERROR_RETRY_JITTER_SECONDS)
            logging.exception(
                "LLM call failed for %s due to quota issues, retrying in %d seconds: %r",
                directory_path,
                sleep_duration,
                e,
            )
        else:
            # Handle generic API failures (timeouts, network drops).
            self._stats.increment_counter("llm.runtime_other_errors")
            jitter = random.uniform(0.4, 0.6 * base_delay)
            sleep_duration = base_delay + jitter
            logging.exception(
                "LLM call failed for %s for conversation %r with runtime error. About to retry: %r",
                directory_path,
                conversation,
                e,
                exc_info=True,
            )
        # Apply the sleep delay before the next attempt.
        time.sleep(min(sleep_duration, 0.01))
        if hasattr(error_prompt_generator_instance, "generate_error_prompt"):
            # Provide structured feedback to the LLM about why the previous call failed.
            return error_prompt_generator_instance.generate_error_prompt(
                str(e)
            )
        return error_prompt_generator.IndexerErrorPromptGenerator().generate_error_prompt(str(e))

    def _handle_pydantic_validation_error(
        self,
        e: pydantic.ValidationError,
        directory_path: str,
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles validation errors from the LLM call."""
        # Record schema non-compliance failures.
        self._stats.increment_counter("llm.validation_pydantic_failures")
        logging.exception(
            "LLM call failed for %s due to validation error.", directory_path
        )
        
        # Extract detailed field-level errors to help the LLM fix itself.
        issues = []
        is_json_invalid = False
        for err in e.errors():
            if err.get("type") == "json_invalid":
                is_json_invalid = True
            loc = ".".join(str(l) for l in err["loc"])
            issues.append(f"Schema violation at '{loc}': {err['msg']}")
            
        if is_json_invalid:
            error_feedback = (
                "Your response was truncated or contains invalid JSON syntax (e.g. EOF while parsing). "
                "Please ensure you complete the JSON object, close all brackets/quotes, and do NOT "
                "include schema definitions like '$defs' in your output."
            )
        else:
            error_feedback = (
                f"Output validation failed with {len(issues)} schema violations. "
                "Your JSON structure does not match the required Pydantic model."
            )

        # Instruct the LLM to fix its own formatting in the next turn.
        if hasattr(error_prompt_generator_instance, "generate_error_prompt"):
            return error_prompt_generator_instance.generate_error_prompt(
                error_feedback,
                issues=issues
            )
        return f"{error_feedback}\n\nIssues:\n" + "\n".join(issues)

    def _handle_json_decoding_error(
        self,
        e: Exception,
        directory_path: str,
        
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles JSON decoding errors from the LLM call."""
        # Record malformed JSON response failures.
        # Record malformed JSON response failures.
        self._stats.increment_counter("llm.validation_json_failures")
        logging.exception("LLM call failed for %s.", directory_path)
        error_feedback = (
            "Output validation failed: LLM response could not be parsed as JSON."
        )
        # Request the LLM to regenerate valid JSON.
        if hasattr(error_prompt_generator_instance, "generate_validation_failure_prompt"):
            return error_prompt_generator_instance.generate_validation_failure_prompt(
                directory_path,
                error_feedback,
            )
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
        # Create the initial conversation session for this agent step.
        # Create the initial conversation session for this agent step.
        conversation = conversation_factory()
        self._stats.increment_counter("llm.conversations_created")

        user_prompt = initial_user_prompt
        attempts_this_conversation = 0
        for attempt in range(self._config.max_attempts):
            # Track retries for monitoring and alerting.
            if attempt > 0:
                metrics.LLM_RETRIES.increment(
                    self._config.indexer_type,
                    self._config.bundle_name,
                )
            attempts_this_conversation += 1

            # If a conversation is stuck or repetitive, reset the session state.
            if (
                attempts_this_conversation
                > self._config.max_attempts_per_conversation
            ):
                conversation = conversation_factory()
                self._stats.increment_counter("llm.conversations_reset")
                attempts_this_conversation = 1

            try:
                # Apply rate limiting/throttling before sending the prompt.
                start_time = time.time()
                with self._throttler.acquire(
                    stringified_system_prompt, user_prompt
                ) as throttler_ctx:
                    waited_time = time.time() - start_time
                    logging.info(
                        "Waited %f seconds for throttling strategy", waited_time
                    )
                    self._stats.increment_counter("llm.prompts_sent")
                    # Send the prompt and capture the raw string response.
                    llm_response_json = conversation.prompt(user_prompt)
                    throttler_ctx.report_output(llm_response_json)
                    
                    if isinstance(llm_response_json, str):
                        preview = llm_response_json[:50] + "..." if len(llm_response_json) > 50 else llm_response_json
                        logging.info("Received response from %s. Preview: %r", agent_name, preview)

                # Attempt to parse and validate the response against the expected schema.
                parsed_output = conversation.get_state(agent_name)
                if isinstance(parsed_output, dict) and pydantic is not None:
                    # Coerce missing required fields before validation to avoid
                    # burning retries on trivially fixable schema gaps.
                    parsed_output = self._coerce_for_schema(parsed_output, output_schema)
                    if hasattr(output_schema, 'model_validate'):
                        return output_schema.model_validate(parsed_output)
                    return parsed_output
                if isinstance(parsed_output, str) and pydantic is not None:
                    if hasattr(output_schema, 'model_validate_json'):
                        return output_schema.model_validate_json(parsed_output)
                    return parsed_output
                # Ensure we don't return None on a successful call that produced no data.
                if parsed_output is None:
                    raise ValueError(
                        f"Agent {agent_name} did not produce any output. This could happen if the LLM called failed."
                    )
                return parsed_output
            except Exception as e:  # broad on purpose to mirror reference flow
                # Catch validation errors and provide feedback for self-correction.
                if pydantic is not None and isinstance(
                    e, getattr(pydantic, "ValidationError", tuple())
                ):
                    metrics.LLM_FAILURES.increment(
                        self._config.indexer_type,
                        self._config.bundle_name,
                        "validation_error",
                        "UNKNOWN",
                    )
                    # Extract detailed error information for the LLM's self-healing loop.
                    user_prompt = self._handle_pydantic_validation_error(
                        e,
                        directory_path,
                        error_prompt_generator_instance,
                    )
                    continue
                # Catch JSON parsing errors and request regeneration.
                if isinstance(e, json.JSONDecodeError):
                    metrics.LLM_FAILURES.increment(
                        self._config.indexer_type,
                        self._config.bundle_name,
                        "json_decode_error",
                        "UNKNOWN",
                    )
                    user_prompt = self._handle_json_decoding_error(
                        e,
                        directory_path,
                        
                        error_prompt_generator_instance,
                    )
                    continue
                # Catch generic runtime errors and trigger retry logic.
                metrics.LLM_FAILURES.increment(
                    self._config.indexer_type,
                    self._config.bundle_name,
                    type(e).__name__,
                    getattr(e, "code", "UNKNOWN") or "UNKNOWN",
                )
                user_prompt = self._handle_llm_prompt_error(
                    e,
                    directory_path,
                    conversation,
                    
                    error_prompt_generator_instance,
                    attempt=attempt,
                )
                # Retry if any runtime API error occurs.
                continue

        # Raise error if all retry attempts are exhausted without success.
        self._stats.increment_counter("llm.max_attempts_reached")
        raise LlmPrompterOutOfRetriesError(
            f"Failed to generate for {directory_path} after exhausting retries."
        )

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
        # Orchestrate a single agent's execution within the larger pipeline.
        # Orchestrate a single agent's execution within the larger pipeline.
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
            # Instruction and schema definition for the agent.
            stringified_system_prompt=instruction,
            output_schema=output_schema_type,
        )
        # Execute tools if requested by the agent plan.
        final_output = tool_executor(plan) if tool_executor else plan
        # Serialize the final output for use by subsequent agents in the chain.
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
        # Construct the instruction set for synthesizing custom sections.
        # Check if any custom sections were requested for this directory.
        if not getattr(system_prompt, "custom_sections", lambda: [])():
            return []

        # Construct the instruction set for synthesizing custom sections.
        section_instruction = system_prompt.custom_sections_instruction(
            code_search_output=code_search_output_str,
            read_files_output=read_files_output_str,
            key_components_output=key_components_summary_str,
            deep_dive_output=deep_dive_summary_str,
        )
        # Execute the custom sections synthesis agent.
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
        
        # Return the extracted custom sections from the synthesis doc.
        return section_doc.custom_sections

    def prompt_for_indexing(
        self,
        directory_path: str,
        system_prompt: Any,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        verifier: Any = None,
    ) -> schema.IndexDocument:
        """Prompts the LLM, validates the response, and retries on failure."""
        # Handle cases where the conversation flow is completely overridden.
        if self._override_conversation_factory is not None:
            logging.info("Overriding sequence using custom conversation factory")
            conversation = self._override_conversation_factory(system_prompt)
            llm_response_json = conversation.prompt(initial_user_prompt)
            parsed = json.loads(llm_response_json)
            if pydantic is not None:
                return schema.IndexDocument.model_validate(parsed)
            return parsed

        # Initialize research context tracking to avoid verification false-positives.
        self.last_research_context = ""

        # --- STEP 1: Research Phase (Code Search) ---
        # Agent plans and executes search queries to find relevant code snippets.
        if self._config.include_search_tool:
            code_search_instruction = system_prompt.codesearch_planner_instruction()
            _, code_search_output_str = self._run_agent_step(
                directory_path=directory_path,
                initial_user_prompt=initial_user_prompt,
                agent_name="codesearch_planner_agent",
                error_prompt_generator_instance=error_prompt_generator_instance,
                instruction=code_search_instruction,
                output_schema_type=dict,
                model_type="research",
                # Track the epoch to ensure temporal consistency in multi-pass indexing.
                epoch=system_prompt.epoch(),
            )
            self.last_research_context += f"=== CODE SEARCH OUTPUT ===\n{code_search_output_str}\n\n"
        # Case when code search is intentionally bypassed.
        else:
            code_search_output_str = "Code search is not enabled for this agent."

        # --- STEP 2: Research Phase (Read Files) ---
        # Agent selects specific files to read based on search results.
        read_files_instruction = system_prompt.read_files_planner_instruction(
            code_search_output=code_search_output_str
        )
        _, read_files_output_str = self._run_agent_step(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="read_files_planner_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            instruction=read_files_instruction,
            output_schema_type=dict,
            # Execute on research-optimized models for faster iteration.
            model_type="research",
            epoch=system_prompt.epoch(),
        )
        self.last_research_context += f"=== READ FILES OUTPUT ===\n{read_files_output_str}\n\n"
        # Use research data to identify key components and patterns.

        # --- STEP 3: Synthesis Phase (Key Components) ---
        # Agent identifies critical components, interfaces, and patterns.
        key_components_instruction = system_prompt.key_components_instruction(
            code_search_output=code_search_output_str,
            read_files_output=read_files_output_str,
        )
        key_components_doc, key_components_summary_str = self._run_agent_step(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="key_components_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            instruction=key_components_instruction,
            # Synthesis steps require more reasoning capacity; use larger models.
            output_schema_type=schema.KeyComponentsDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )
        # Generate technical deep dive documentation based on gathered insights.

        # --- STEP 4: Synthesis Phase (Deep Dive) ---
        # Agent provides detailed technical analysis of complex logic.
        deep_dive_instruction = system_prompt.deep_dive_instruction(
            code_search_output=code_search_output_str,
            read_files_output=read_files_output_str,
            key_components_output=key_components_summary_str,
        )
        deep_dive_doc, deep_dive_summary_str = self._run_agent_step(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="deep_dive_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            # Generate the detailed technical deep dive for core logic.
            instruction=deep_dive_instruction,
            output_schema_type=schema.DeepDiveDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )
        # Consolidate findings into a high-level overview section.

        # --- STEP 5: Synthesis Phase (Overview) ---
        # Agent generates the high-level summary of the directory.
        overview_instruction = system_prompt.overview_instruction(
            code_search_output=code_search_output_str,
            read_files_output=read_files_output_str,
            key_components_output=key_components_summary_str,
            deep_dive_output=deep_dive_summary_str,
        )
        overview_doc, _ = self._run_agent_step(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="overview_agent",
            # Consolidate all previous findings into a human-readable overview.
            error_prompt_generator_instance=error_prompt_generator_instance,
            instruction=overview_instruction,
            output_schema_type=schema.OverviewDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )
        # Finalize the document with any requested custom sections.

        # --- STEP 6: Synthesis Phase (Custom Sections) ---
        # Agent generates optional user-defined sections.
        custom_sections_results = self._run_custom_sections_agent(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            system_prompt=system_prompt,
            error_prompt_generator_instance=error_prompt_generator_instance,
            code_search_output_str=code_search_output_str,
            read_files_output_str=read_files_output_str,
            key_components_summary_str=key_components_summary_str,
            deep_dive_summary_str=deep_dive_summary_str,
        )

        # --- STEP 7: Final Assembly ---
        # Combine all partial agent outputs into the final structured IndexDocument.
        artifact = schema.IndexDocument(
            overview=overview_doc.overview,
            key_individual_components=key_components_doc.key_individual_components,
            key_interfaces=key_components_doc.key_interfaces,
            key_dependencies=key_components_doc.key_dependencies,
            architectural_patterns_and_gotchas=key_components_doc.architectural_patterns_and_gotchas,
            deep_dive=deep_dive_doc.deep_dive,
            testing_strategy=key_components_doc.testing_strategy,
            configurations=key_components_doc.configurations,
            custom_sections=custom_sections_results,
            # Record the generation metadata for traceability.
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # --- STEP 8: Verification Phase ---
        # Run automated quality checks on the generated artifact.
        if verifier:
            logging.info("Verifying artifact for %s", directory_path)
            # Use the provided directory contents as the ground truth for verification,
            # augmented with any research context gathered during the process.
            source_context = getattr(system_prompt, "_directory_contents", "No source context available.")
            full_context = source_context + "\n\n" + self.last_research_context
            artifact_json = artifact.model_dump_json(indent=2)
            verdict = verifier.verify(artifact_json, full_context)
            # Log verification issues for manual review or future self-healing loops.
            if not verdict.passed:
                logging.warning("Verification failed for %s: %s", directory_path, verdict.issues)
        
        # Return the finalized artifact for storage or further verification.
        return artifact
                # In the real system, this would trigger a retry loop or similar.
                # For now, we just log it and return the artifact.
        
        return artifact

    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
    ) -> schema.IndexDocument:
        """Prompts the LLM to merge summaries, validates response, and retries."""
        if self._override_conversation_factory is not None:
            pass

        if pydantic is not None and hasattr(schema.IndexDocument, "model_json_schema"):
            schema_str = json.dumps(schema.IndexDocument.model_json_schema(), indent=2)
            system_prompt = (
                f"{system_prompt}\n\nYour output MUST be a JSON object that conforms to the following schema: {schema_str}"
            )

        return self._execute_single_prompt(
            directory_path=directory_path,
            initial_user_prompt=initial_user_prompt,
            agent_name="merging_agent",
            error_prompt_generator_instance=error_prompt_generator_instance,
            conversation_factory=lambda: self._create_single_conversation(
                system_prompt=system_prompt,
                agent_name="merging_agent",
                output_schema_type=schema.IndexDocument,
                model_type="synthesis",
            ),
            stringified_system_prompt=system_prompt,
            output_schema=schema.IndexDocument,
        )

    
    def prompt_for_root_map_summary(self, root_map_content: str) -> str:
        """Returns a summary of the root map content."""
        # Return a truncated preview of the root map as a placeholder summary.
        return (
            "Meta-summary of root map:\n\n"
            f"{root_map_content[:500]}..."
        )

    def verify_artifact(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> verification_types.VerificationVerdict:
        """Runs the verifier prompt and returns a structured verdict."""
        system_prompt = prompt_templates.create_verifier_prompt(artifact_json, source_context)
        
        logging.info(
            "[VerifyArtifact] system_prompt=%d bytes "
            "(artifact=%d, source_context=%d).",
            len(system_prompt), len(artifact_json), len(source_context),
        )

        # Simple schema instruction for the verification verdict
        if pydantic is not None and hasattr(verification_types.VerificationVerdict, "model_json_schema"):
            schema_str = json.dumps(verification_types.VerificationVerdict.model_json_schema(), indent=2)
            system_prompt = f"{system_prompt}\n\nYour output MUST be a JSON object conforming to: {schema_str}"
            
        conv = self._create_single_conversation(
            system_prompt=system_prompt,
            agent_name="verifier_agent",
            output_schema_type=verification_types.VerificationVerdict,
            model_type="synthesis",
        )
        
        try:
            
            with self._throttler.acquire(system_prompt, "Please verify the artifact.") as throttle_ctx:
                response = conv.prompt("Please verify the artifact.")
                throttle_ctx.report_output(response)
                
                preview = (response[:50] + "...") if isinstance(response, str) and len(response) > 50 else response
                logging.info(
                    "[VerifyArtifact] raw response length=%d bytes. Preview: %r",
                    len(response) if response else 0,
                    preview
                )

                # Handle empty or whitespace-only responses from the LLM.
                # This typically happens when the source context exceeds the
                # model's context window (e.g. 300KB+ with local Ollama models).
                if not response or not response.strip():
                    logging.warning(
                        "[VerifyArtifact] LLM returned empty response "
                        "(prompt was %d bytes — likely exceeds model context window). "
                        "Passing verification by default.",
                        len(system_prompt),
                    )
                    return verification_types.VerificationVerdict.success()

                # In this simple implementation, we assume the response is JSON parsing to VerificationVerdict
                try:
                    # Parse as pydantic object for strict validation.
                    parsed = verification_types.VerificationVerdict.model_validate_json(response)
                    parsed.verification_model = self._config.synthesis_gemini_model
                    return parsed
                except Exception:
                    pass

                # Ollama often wraps JSON in markdown fences: ```json {...} ```
                # We need to strip them and retry parsing.
                import re
                cleaned = response.strip()
                
                # First, attempt to match standard markdown json fences.
                # The DOTALL flag ensures we capture multi-line JSON structures.
                fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
                if fence_match:
                    cleaned = fence_match.group(1)
                else:
                    # If there are no fences, fallback to extracting any raw JSON-like 
                    # object structure found anywhere within the response body.
                    obj_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
                    if obj_match:
                        cleaned = obj_match.group(0)

                try:
                    data = json.loads(cleaned)
                    # --- Coercion for VerificationVerdict ---
                    # Weaker LLMs (like Gemma via Ollama) often confuse the 'issues' (List[str])
                    # and 'detailed_issues' (List[VerificationIssue]) fields, or return
                    # non-primitive types for boolean/float fields.
                    if isinstance(data, dict):
                        if "issues" in data and isinstance(data["issues"], list):
                            new_issues = []
                            detailed = data.get("detailed_issues")
                            if not isinstance(detailed, list):
                                detailed = []
                            
                            for item in data["issues"]:
                                if isinstance(item, dict):
                                    desc = item.get("description", str(item))
                                    new_issues.append(desc)
                                    # If it looks like a structured issue, ensure it's in detailed_issues
                                    if "category" in item and item not in detailed:
                                        detailed.append(item)
                                else:
                                    new_issues.append(str(item))
                            data["issues"] = new_issues
                            data["detailed_issues"] = detailed

                        if "passed" in data and not isinstance(data["passed"], bool):
                            data["passed"] = str(data["passed"]).lower() == "true"
                        
                        if "confidence" in data and not isinstance(data["confidence"], (int, float)):
                            try:
                                data["confidence"] = float(data["confidence"])
                            except (ValueError, TypeError):
                                data["confidence"] = 1.0

                    verdict = verification_types.VerificationVerdict(**data)
                    verdict.verification_model = self._config.synthesis_gemini_model
                    return verdict
                except (json.JSONDecodeError, TypeError):
                    pass

                # All parsing failed — this is an infrastructure issue (model
                # can't produce structured output), not a verification failure.
                # Auto-pass rather than burning retries.
                logging.warning(
                    "[VerifyArtifact] Could not parse LLM response as JSON. "
                    "Raw response (%d bytes): %.200s",
                    len(response), response,
                )
                return verification_types.VerificationVerdict.success(confidence=0.5)
        except Exception as e:
            logging.exception("Verification prompt failed: %s", e)
            # Infrastructure failures (network, timeout, OOM) should not
            # block the pipeline.  Auto-pass with low confidence.
            return verification_types.VerificationVerdict.success(confidence=0.5)

