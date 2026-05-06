import dataclasses

@dataclasses.dataclass
class Config:
    research_model: str = "foo"
    
    @property
    def research_gemini_model(self) -> str:
        return self.research_model
        
    @research_gemini_model.setter
    def research_gemini_model(self, value: str):
        self.research_model = value

try:
    c = Config(research_gemini_model="bar")
except Exception as e:
    print(f"Error: {e}")
