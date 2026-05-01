import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from indexing.scripts import bundle_verifier
from indexing.config import bundle_pb2

def test_parse():
    config_path = "indexing/config/aadc.textproto"
    try:
        bundle = bundle_verifier.parse_config(config_path)
        print(f"Successfully parsed bundle: {bundle.bundle_name}")
        print(f"Number of input directories: {len(bundle.input)}")
        for inp in bundle.input:
            print(f"  - {inp.directory}")
        
        errors = bundle_verifier.validate_bundle(bundle)
        if errors:
            print("Validation errors:")
            for err in errors:
                print(f"  [!] {err}")
        else:
            print("Bundle is valid!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parse()
