# Wiki-First Indexer Integration

You MUST adopt a **Wiki-First Discovery** approach using the `indxr` MCP tools:
- **Search Knowledge**: `mcp_indxr_wiki_search`, `mcp_indxr_wiki_read`, `mcp_indxr_wiki_status`. Gather knowledge before deep analysis.
- **Structural Tools**: `mcp_indxr_find`, `mcp_indxr_summarize`, `mcp_indxr_explain_symbol`, `mcp_indxr_get_public_api`, `mcp_indxr_get_callers`, `mcp_indxr_get_dependency_graph`, `mcp_indxr_get_tree`.
- **Context Budgeting (MANDATORY)**:
  - **Level 1 (Discovery)**: Use `mcp_indxr_find`, `mcp_indxr_wiki_search`, `mcp_indxr_get_tree`.
  - **Level 2 (Understanding)**: Use `mcp_indxr_summarize`, `mcp_indxr_explain_symbol`, `mcp_indxr_get_public_api`.
  - **Level 3 (Targeted Reading)**: Use `mcp_indxr_read` or `mcp_indxr_read_source` for specific symbols.
  - **Level 4 (Raw Read)**: Use `read_file` ONLY when you are modifying the file or need to see logic that is not exposed via structural tools.
- **NEVER** iterate through files manually or use `read_file` on many files at once if a structural summary can suffice.
