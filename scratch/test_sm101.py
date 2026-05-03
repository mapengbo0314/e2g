
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from indexing import schema
import pydantic

def test_synthetic_stub():
    print("Testing synthetic_stub...")
    try:
        stub = schema.IndexDocument.synthetic_stub("test_path.py", "test content", "test summary")
        print("Stub created successfully.")
        
        # Verify it passes model_validate
        schema.IndexDocument.model_validate(stub.model_dump())
        print("model_validate PASSED.")
        
        # Verify fields
        assert stub.overview.content == "test summary"
        assert len(stub.verification_notes) == 1
        assert stub.generation_metadata is not None
        print("Fields verified.")
        
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_synthetic_stub()
    sys.exit(0 if success else 1)
