const scaffold = {
  directories: [
    "change_detection",
    "config",
    "continuous",
    "filesystem",
    "g3doc",
    "gemini_cli",
    "index_expert",
    "indexer",
    "mcp",
    "planner",
    "ui",
    "utils",
  ],
  agentDirectories: [
    "agents",
    "rules",
    "skills",
    "mcps",
    "sub_agents",
    "workflows",
    "templates",
  ],
  rootFiles: [
    "README.md",
    "bundle_storage.py",
    "chunker.py",
    "constants.py",
    "context.py",
    "error_prompt_generator.py",
    "file_utils.py",
    "generate_bundles.py",
    "github_cloner.py",
    "llm_indexer.py",
    "multi_bundle_state.py",
    "orchestrator.py",
    "prompt_templates.py",
    "reindexing.py",
    "root_map.py",
    "schema.py",
    "sequential_llm_prompter.py",
    "shared_flags.py",
    "state.py",
    "summary_merger.py",
    "work_unit.py",
  ],
};

const harnessItems = [
  ["AGENT.md", "Root guide for the service, the reduced architecture, and the media-to-file workflow."],
  ["_agents/agents/planner/agent.json", "Formal planner registration modeled after your screenshot pattern with per-agent config."],
  ["_agents/agents/verifier/agent.json", "Final QA agent definition for edge cases, transcript fidelity, and robustness checks."],
  ["AGENT.md", "Shared root agent guide that all role configs should inherit from."],
  ["_agents/skills/repo_migration_planner/SKILL.md", "Skill for staging Python to Kotlin or Java migration work over time."],
  ["_agents/workflows/video_transcriber.md", "Workflow for turning videos into structured repository edits."],
  ["_agents/sub_agents/video_frame_reader.md", "Extracts visible code, filenames, paths, and timestamps from frames."],
  ["_agents/sub_agents/file_populator.md", "Converts structured notes into concrete file drafts inside this repo."],
  ["_agents/skills/transcription_router.md", "Maps transcript and OCR segments to the correct destination files."],
  ["_agents/mcps/registry.md", "Tracks the MCP connectors needed for OCR, speech, file reads, and writes."],
];

const nodes = [
  { id: "generate_bundles", x: 120, y: 390, w: 180, h: 54, label: "generate_bundles.py", sub: "Main Entry" },
  { id: "orchestrator", x: 365, y: 390, w: 180, h: 54, label: "orchestrator.py", sub: "Workflow Mgmt" },
  { id: "bundle_storage", x: 340, y: 475, w: 170, h: 50, label: "bundle_storage.py" },
  { id: "root_map", x: 610, y: 275, w: 150, h: 50, label: "root_map.py" },
  { id: "llm_indexer", x: 700, y: 390, w: 170, h: 56, label: "llm_indexer.py", sub: "Dir Indexing" },
  { id: "summary_merger", x: 930, y: 225, w: 180, h: 56, label: "summary_merger.py", sub: "Chunk Merging" },
  { id: "sequential_llm_prompter", x: 1230, y: 175, w: 210, h: 58, label: "sequential_llm_prompter.py", sub: "LLM API" },
  { id: "prompt_templates", x: 1205, y: 295, w: 180, h: 52, label: "prompt_templates.py" },
  { id: "schema", x: 930, y: 340, w: 150, h: 50, label: "schema.py" },
  { id: "chunker", x: 930, y: 405, w: 150, h: 50, label: "chunker.py", sub: "File Splitting" },
  { id: "state", x: 930, y: 505, w: 150, h: 54, label: "state.py", sub: "Storage I/O" },
  { id: "constants", x: 1225, y: 435, w: 150, h: 50, label: "constants.py" },
  { id: "file_utils", x: 930, y: 585, w: 150, h: 52, label: "file_utils.py" },
  { id: "planner", x: 690, y: 545, w: 130, h: 48, label: "planner/", sub: "Planning" },
  { id: "change_detection", x: 480, y: 640, w: 170, h: 48, label: "change_detection/", sub: "Reindex Triggers" },
  { id: "continuous", x: 555, y: 545, w: 155, h: 50, label: "continuous/", sub: "Auto Updates" },
  { id: "config", x: 815, y: 640, w: 140, h: 48, label: "config/", sub: "Bundle Defs" },
  { id: "filesystem", x: 1215, y: 640, w: 150, h: 56, label: "filesystem/", sub: "File Access" },
  { id: "utils", x: 1195, y: 735, w: 120, h: 46, label: "utils/", sub: "General Utils" },
  { id: "indexer", x: 610, y: 695, w: 130, h: 54, label: "indexer/", sub: "Core Parts" },
  { id: "g3doc", x: 600, y: 620, w: 120, h: 46, label: "g3doc/", sub: "Docs" },
  { id: "gemini_cli", x: 600, y: 765, w: 130, h: 46, label: "gemini_cli/", sub: "CLI Tools" },
  { id: "ui", x: 750, y: 760, w: 100, h: 46, label: "ui/", sub: "Web UI" },
  { id: "mcp", x: 875, y: 757, w: 110, h: 46, label: "mcp/", sub: "Agent Serving" },
  { id: "index_expert", x: 1015, y: 695, w: 150, h: 52, label: "index_expert/", sub: "Query Agent" },
  { id: "agents_workspace", x: 900, y: 95, w: 215, h: 54, label: "_agents/", sub: "Unified Agent Workspace" },
];

const edges = [
  ["generate_bundles", "orchestrator", "Drives"],
  ["generate_bundles", "bundle_storage", "Loads"],
  ["generate_bundles", "continuous", "Triggers"],
  ["generate_bundles", "config", "Uses"],
  ["orchestrator", "root_map", "Generates root map"],
  ["orchestrator", "planner", "Plans work"],
  ["orchestrator", "llm_indexer", "Calls for each dir"],
  ["orchestrator", "state", "Writes index files"],
  ["orchestrator", "bundle_storage", "Uses"],
  ["llm_indexer", "summary_merger", "Uses if chunked"],
  ["llm_indexer", "schema", "Validates output"],
  ["llm_indexer", "chunker", "Uses if needed"],
  ["llm_indexer", "state", "Uses"],
  ["llm_indexer", "constants", "Uses"],
  ["llm_indexer", "prompt_templates", "Gets prompts"],
  ["summary_merger", "sequential_llm_prompter", "Calls LLM"],
  ["summary_merger", "prompt_templates", "Gets prompts"],
  ["state", "constants", "Uses"],
  ["state", "file_utils", "Uses"],
  ["continuous", "change_detection", "Reads changes"],
  ["continuous", "config", "Checks"],
  ["file_utils", "filesystem", "Uses"],
  ["file_utils", "utils", "Uses"],
  ["indexer", "index_expert", "Calls"],
  ["gemini_cli", "index_expert", "Exposes"],
  ["ui", "index_expert", "Exposes"],
  ["mcp", "index_expert", "Exposes"],
  ["index_expert", "filesystem", "Reads files"],
  ["index_expert", "utils", "Uses"],
  ["agents_workspace", "mcp", "Defines workflows"],
  ["agents_workspace", "ui", "Feeds content"],
];

function renderStats() {
  const stats = [
    [String(scaffold.directories.length), "core directories"],
    [String(scaffold.rootFiles.length), "core modules"],
    [String(scaffold.agentDirectories.length), "agent folders"],
    [String(nodes.length), "mapped nodes"],
  ];

  const container = document.getElementById("hero-stats");
  stats.forEach(([value, label]) => {
    const card = document.createElement("div");
    card.className = "stat";
    card.innerHTML = `<span class="stat-value">${value}</span><span class="stat-label">${label}</span>`;
    container.appendChild(card);
  });
}

function renderTree() {
  const root = document.getElementById("tree-root");
  const groups = [
    ["indexing-reference/", scaffold.directories, "dir"],
    ["_agents/", scaffold.agentDirectories, "dir"],
    ["indexing root files", scaffold.rootFiles, "file"],
  ];

  groups.forEach(([title, items, kind]) => {
    const group = document.createElement("section");
    group.className = "tree-group";
    const heading = document.createElement("h3");
    heading.className = "tree-title";
    heading.textContent = title;
    group.appendChild(heading);

    const list = document.createElement("ul");
    list.className = "tree-list";

    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "tree-item";
      li.innerHTML = `<span class="dot ${kind}"></span><code>${item}</code>`;
      list.appendChild(li);
    });

    group.appendChild(list);
    root.appendChild(group);
  });
}

function renderHarness() {
  const root = document.getElementById("module-list");
  harnessItems.forEach(([name, description]) => {
    const item = document.createElement("article");
    item.className = "module-item";
    item.innerHTML = `<h3>${name}</h3><p>${description}</p>`;
    root.appendChild(item);
  });
}

function centerOf(node) {
  return { x: node.x + node.w / 2, y: node.y + node.h / 2 };
}

function roundedRect(x, y, w, h, r = 22) {
  return `M${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} H${x + r} Q${x},${y + h} ${x},${y + h - r} V${y + r} Q${x},${y} ${x + r},${y} Z`;
}

function renderArchitecture() {
  const svg = document.getElementById("architecture-map");
  const ns = "http://www.w3.org/2000/svg";
  const nodeById = Object.fromEntries(nodes.map((node) => [node.id, node]));

  const defs = document.createElementNS(ns, "defs");
  const marker = document.createElementNS(ns, "marker");
  marker.setAttribute("id", "arrow");
  marker.setAttribute("viewBox", "0 0 10 10");
  marker.setAttribute("refX", "9");
  marker.setAttribute("refY", "5");
  marker.setAttribute("markerWidth", "8");
  marker.setAttribute("markerHeight", "8");
  marker.setAttribute("orient", "auto-start-reverse");
  const arrowPath = document.createElementNS(ns, "path");
  arrowPath.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
  arrowPath.setAttribute("fill", "rgba(23, 98, 79, 0.42)");
  marker.appendChild(arrowPath);
  defs.appendChild(marker);
  svg.appendChild(defs);

  const cluster = document.createElementNS(ns, "rect");
  cluster.setAttribute("x", "445");
  cluster.setAttribute("y", "520");
  cluster.setAttribute("width", "915");
  cluster.setAttribute("height", "270");
  cluster.setAttribute("class", "cluster");
  svg.appendChild(cluster);

  edges.forEach(([fromId, toId, label]) => {
    const from = centerOf(nodeById[fromId]);
    const to = centerOf(nodeById[toId]);
    const mx = (from.x + to.x) / 2;
    const my = (from.y + to.y) / 2;
    const curve = `M ${from.x} ${from.y} C ${mx} ${from.y}, ${mx} ${to.y}, ${to.x} ${to.y}`;

    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", curve);
    path.setAttribute("class", "edge");
    path.setAttribute("marker-end", "url(#arrow)");
    svg.appendChild(path);

    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", String(mx));
    text.setAttribute("y", String(my - 6));
    text.setAttribute("class", "edge-label");
    text.textContent = label;
    svg.appendChild(text);
  });

  nodes.forEach((node) => {
    const group = document.createElementNS(ns, "g");
    group.setAttribute("class", "node-group");

    const shape = document.createElementNS(ns, "path");
    shape.setAttribute("d", roundedRect(node.x, node.y, node.w, node.h, 22));
    shape.setAttribute("class", "node");
    group.appendChild(shape);

    const label = document.createElementNS(ns, "text");
    label.setAttribute("x", String(node.x + node.w / 2));
    label.setAttribute("y", String(node.y + (node.sub ? 22 : 30)));
    label.setAttribute("class", "label");
    label.textContent = node.label;
    group.appendChild(label);

    if (node.sub) {
      const sub = document.createElementNS(ns, "text");
      sub.setAttribute("x", String(node.x + node.w / 2));
      sub.setAttribute("y", String(node.y + 40));
      sub.setAttribute("class", "sub");
      sub.textContent = node.sub;
      group.appendChild(sub);
    }

    svg.appendChild(group);
  });
}

renderStats();
renderTree();
renderHarness();
renderArchitecture();
