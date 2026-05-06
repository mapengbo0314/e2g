import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

# Add import instructor
if "import instructor" not in content:
    content = content.replace("import logging\n", "import logging\nimport instructor\n")

# Patch VertexAiConversation
vertex_old = """        # Initialize the GenAI client with Vertex AI enabled.
        self.client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        # Create chat session with system instruction in the config.
        self.chat = self.client.chats.create(
            model=model_name,
            config={"system_instruction": system_prompt} if system_prompt else None,
        )"""

vertex_new = """        # Initialize the GenAI client with Vertex AI enabled.
        self.client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        self.instructor_client = instructor.from_genai(self.client, mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS)
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []"""

content = content.replace(vertex_old, vertex_new)

# Patch GoogleAiConversation
google_old = """        self.client = genai.Client(api_key=api_key)
        # Create chat session with system instruction in the config.
        self.chat = self.client.chats.create(
            model=model_name,
            config={"system_instruction": system_prompt} if system_prompt else None,
        )"""

google_new = """        self.client = genai.Client(api_key=api_key)
        self.instructor_client = instructor.from_genai(self.client, mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS)
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []"""

content = content.replace(google_old, google_new)

with open("indexing/sequential_llm_prompter.py", "w") as f:
    f.write(content)
