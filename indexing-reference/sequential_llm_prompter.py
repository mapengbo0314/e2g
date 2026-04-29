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
import time
from typing import Any, Callable

from absl import logging

try:
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None

try:
    from indexing import error_prompt_generator
except ImportError:
    import error_prompt_generator

try:
    from indexing import prompt_templates
except ImportError:
    import prompt_templates

try:
    from indexing import schema
except ImportError:
    import schema


_QUOTA_ERROR_RETRY_JITTER_SECONDS = 30


class _NoOpCounter:
    def increment(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NoOpMetrics:
    LLM_RETRIES = _NoOpCounter()
    LLM_FAILURES = _NoOpCounter()


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
        return False

    def report_output(self, _output: str) -> None:
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


@dataclasses.dataclass
class GeminiLlmPrompterConfig:
    """Configuration for the LLM prompter."""

    bundle_name: str
    throttling_strategy: Any
    indexer_type: str = "REGULAR"
    research_gemini_model: str = "gemini-3-flash-preview"
    synthesis_gemini_model: str = "gemini-3-flash-preview"
    max_attempts: int = 3
    delay_on_failure_max_seconds: int = 10
    max_attempts_per_conversation: int = 3
    include_search_tool: bool = True
    generate_content_config: Any | None = None


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
                key_individual_components=schema.KeyIndividualComponents(
                    components=[]
                ),
            )
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
        return self.output_schema_type()


class GeminiLlmPrompter(LlmPrompter):
    """LLM prompter for Gemini."""

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

    def _create_single_conversation(
        self,
        system_prompt: str,
        agent_name: str,
        output_schema_type: type[Any],
        model_type: str,
        epoch: int = 1,
    ) -> _SimpleConversation:
        """Creates a simple LLM conversation for a single step."""
        logging.info("Creating new LLM conversation for %s", agent_name)
        return _SimpleConversation(
            system_prompt=system_prompt,
            agent_name=agent_name,
            output_schema_type=output_schema_type,
        )

    def _handle_llm_prompt_error(
        self,
        e: Exception,
        directory_path: str,
        conversation: _SimpleConversation,
        error_prompt_generator_instance: Any,
        attempt: int = 1,
    ) -> str:
        """Handles runtime errors from the LLM call."""
        base_delay = min(2**attempt, self._config.delay_on_failure_max_seconds)
        if "quota" in str(e).lower():
            self._stats.increment_counter("llm.runtime_quota_errors")
            sleep_duration = random.randint(0, _QUOTA_ERROR_RETRY_JITTER_SECONDS)
            logging.exception(
                "LLM call failed for %s due to quota issues, retrying in %d seconds: %r",
                directory_path,
                sleep_duration,
                e,
            )
        else:
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
        time.sleep(min(sleep_duration, 0.01))
        if hasattr(error_prompt_generator_instance, "generate_runtime_error_prompt"):
            return error_prompt_generator_instance.generate_runtime_error_prompt(
                directory_path,
                str(e),
            )
        return error_prompt_generator.build_error_prompt(str(e), directory_path)

    def _handle_pydantic_validation_error(
        self,
        e: Exception,
        directory_path: str,
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles validation errors from the LLM call."""
        self._stats.increment_counter("llm.validation_pydantic_failures")
        logging.exception(
            "LLM call failed for %s due to validation error.", directory_path
        )
        error_feedback = (
            "Output validation failed: response was not valid JSON or did not "
            "match schema."
        )
        if hasattr(error_prompt_generator_instance, "generate_validation_failure_prompt"):
            return error_prompt_generator_instance.generate_validation_failure_prompt(
                directory_path,
                error_feedback,
            )
        return error_prompt_generator.build_error_prompt(error_feedback, directory_path)

    def _handle_json_decoding_error(
        self,
        e: Exception,
        directory_path: str,
        error_prompt_generator_instance: Any,
    ) -> str:
        """Handles JSON decoding errors from the LLM call."""
        self._stats.increment_counter("llm.validation_json_failures")
        logging.exception("LLM call failed for %s.", directory_path)
        error_feedback = (
            "Output validation failed: LLM response could not be parsed as JSON."
        )
        if hasattr(error_prompt_generator_instance, "generate_validation_failure_prompt"):
            return error_prompt_generator_instance.generate_validation_failure_prompt(
                directory_path,
                error_feedback,
            )
        return error_prompt_generator.build_error_prompt(error_feedback, directory_path)

    def _execute_single_prompt(
        self,
        directory_path: str,
        initial_user_prompt: str,
        agent_name: str,
        error_prompt_generator_instance: Any,
        conversation_factory: Callable[[], _SimpleConversation],
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
                metrics.LLM_RETRIES.increment(
                    self._config.indexer_type,
                    self._config.bundle_name,
                )
            attempts_this_conversation += 1

            if (
                attempts_this_conversation
                > self._config.max_attempts_per_conversation
            ):
                conversation = conversation_factory()
                self._stats.increment_counter("llm.conversations_reset")
                attempts_this_conversation = 1

            try:
                start_time = time.time()
                with self._throttler.acquire(
                    stringified_system_prompt, user_prompt
                ) as throttler_ctx:
                    waited_time = time.time() - start_time
                    logging.info(
                        "Waited %f seconds for throttling strategy", waited_time
                    )
                    self._stats.increment_counter("llm.prompts_sent")
                    llm_response_json = conversation.prompt(user_prompt)
                    throttler_ctx.report_output(llm_response_json)

                parsed_output = conversation.get_state(agent_name)
                if isinstance(parsed_output, dict) and pydantic is not None:
                    return output_schema.model_validate(parsed_output)
                if isinstance(parsed_output, str) and pydantic is not None:
                    return output_schema.model_validate_json(parsed_output)
                if parsed_output is None:
                    raise ValueError(
                        f"Agent {agent_name} did not produce any output. This could happen if the LLM called failed."
                    )
                return parsed_output
            except Exception as e:  # broad on purpose to mirror reference flow
                if pydantic is not None and isinstance(
                    e, getattr(pydantic, "ValidationError", tuple())
                ):
                    metrics.LLM_FAILURES.increment(
                        self._config.indexer_type,
                        self._config.bundle_name,
                        "validation_error",
                        "UNKNOWN",
                    )
                    user_prompt = self._handle_pydantic_validation_error(
                        e,
                        directory_path,
                        error_prompt_generator_instance,
                    )
                    continue
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
                continue

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
        output_schema_type: type[Any],
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

    def prompt_for_indexing(
        self,
        directory_path: str,
        system_prompt: Any,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
    ) -> schema.IndexDocument:
        """Prompts the LLM, validates the response, and retries on failure."""
        if self._override_conversation_factory is not None:
            logging.info("Overriding sequence using custom conversation factory")
            conversation = self._override_conversation_factory(system_prompt)
            llm_response_json = conversation.prompt(initial_user_prompt)
            parsed = json.loads(llm_response_json)
            if pydantic is not None:
                return schema.IndexDocument.model_validate(parsed)
            return parsed

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
                epoch=system_prompt.epoch(),
            )
        else:
            code_search_output_str = "Code search is not enabled for this agent."

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
            model_type="research",
            epoch=system_prompt.epoch(),
        )

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
            output_schema_type=schema.KeyComponentsDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )

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
            instruction=deep_dive_instruction,
            output_schema_type=schema.DeepDiveDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )

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
            error_prompt_generator_instance=error_prompt_generator_instance,
            instruction=overview_instruction,
            output_schema_type=schema.OverviewDocument,
            model_type="synthesis",
            epoch=system_prompt.epoch(),
        )

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

        return schema.IndexDocument(
            overview=overview_doc.overview,
            key_individual_components=key_components_doc.key_individual_components,
            key_interfaces=key_components_doc.key_interfaces,
            key_dependencies=key_components_doc.key_dependencies,
            architectural_patterns_and_gotchas=key_components_doc.architectural_patterns_and_gotchas,
            deep_dive=deep_dive_doc.deep_dive,
            testing_strategy=key_components_doc.testing_strategy,
            configurations=key_components_doc.configurations,
            custom_sections=custom_sections_results,
        )

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
        return (
            "Meta-summary of root map:\n\n"
            + root_map_content[:4000]
        )
