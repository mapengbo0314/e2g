
import instructor
import google.genai as genai
import pydantic
from pydantic import BaseModel
import gc
import sys

def check_instructor_cache():
    # Instructor might use a cache in `instructor.patch` or in internal schema generation
    # But let's check `pydantic`'s internal schema cache first.
    
    class MyBase(BaseModel): pass
    
    import pydantic._internal._generate_schema
    # Not easily accessible, let's just see if subclasses stay alive when passed to some mock
    
    refs = []
    
    for i in range(10):
        # Create a dynamic model
        DynamicModel = pydantic.create_model(f"DynamicModel{i}", __base__=MyBase)
        # Generate schema (this usually triggers caching in Pydantic V2)
        schema = DynamicModel.model_json_schema()
        # In reality, this is passed to instructor:
        # instructor_client.chat.completions.create(..., response_model=DynamicModel)
    
    gc.collect()
    print(f"Alive subclasses of MyBase: {len(MyBase.__subclasses__())}")

check_instructor_cache()
