import re
import json

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

abstract_method = """    @abc.abstractmethod
    def prompt_for_enrichment(
        self,
        file_path: str,
        skeleton: schema.FileSkeleton,
        source_code: str,
    ) -> schema.FileEnrichment:
        \"\"\"Prompts the LLM to enrich a file skeleton.\"\"\"

    @abc.abstractmethod
    def prompt_for_root_map_summary"""

content = content.replace("    @abc.abstractmethod\n    def prompt_for_root_map_summary", abstract_method)

gemini_method = """    def prompt_for_enrichment(
        self,
        file_path: str,
        skeleton: schema.FileSkeleton,
        source_code: str,
    ) -> schema.FileEnrichment:
        \"\"\"Prompts the LLM to enrich a file skeleton. Implements chunking if symbols > 40.\"\"\"
        if len(skeleton.symbols) <= 40:
            return self._execute_enrichment_chunk(file_path, skeleton, source_code)
        
        # Symbol Chunking
        merged_enrichment = schema.FileEnrichment(symbols={}, invariants={})
        
        for i in range(0, len(skeleton.symbols), 40):
            chunk_symbols = skeleton.symbols[i:i+40]
            # Send invariants only in the first chunk to avoid redundant processing
            chunk_skeleton = schema.FileSkeleton(
                symbols=chunk_symbols,
                invariants=skeleton.invariants if i == 0 else []
            )
            chunk_enrichment = self._execute_enrichment_chunk(file_path, chunk_skeleton, source_code)
            merged_enrichment.merge(chunk_enrichment)
            
        return merged_enrichment

    def _execute_enrichment_chunk(
        self,
        file_path: str,
        skeleton: schema.FileSkeleton,
        source_code: str,
    ) -> schema.FileEnrichment:
        system_prompt = (
            f"You are a code enrichment agent. Given a file skeleton containing extracted symbols "
            f"and invariants for '{file_path}', and the corresponding source code, provide a semantic "
            f"summary for each symbol and intent/usage_context for each invariant."
        )
        
        # Pydantic JSON schema string representation
        if pydantic is not None and hasattr(schema.FileEnrichment, "model_json_schema"):
            schema_str = json.dumps(schema.FileEnrichment.model_json_schema(), indent=2)
            system_prompt += f"\\n\\nYour output MUST be a JSON object conforming to this schema:\\n{schema_str}"
        
        skeleton_json = skeleton.model_dump_json(indent=2) if hasattr(skeleton, "model_dump_json") else json.dumps(skeleton, default=str)
        user_prompt = f"File Skeleton:\\n```json\\n{skeleton_json}\\n```\\n\\nSource Code:\\n```\\n{source_code}\\n```"
        
        # We need an error prompt generator instance to pass along
        try:
            error_gen = error_prompt_generator.IndexerErrorPromptGenerator()
        except NameError:
            error_gen = None
            
        return self._execute_single_prompt(
            directory_path=file_path,
            initial_user_prompt=user_prompt,
            agent_name="enrichment_agent",
            error_prompt_generator_instance=error_gen,
            conversation_factory=lambda: self._create_single_conversation(
                system_prompt=system_prompt, agent_name="enrichment_agent",
                output_schema_type=schema.FileEnrichment, model_type="synthesis"
            ),
            stringified_system_prompt=system_prompt,
            output_schema=schema.FileEnrichment,
        )

    def prompt_for_root_map_summary"""

content = content.replace("    def prompt_for_root_map_summary", gemini_method)

with open("indexing/sequential_llm_prompter.py", "w") as f:
    f.write(content)
