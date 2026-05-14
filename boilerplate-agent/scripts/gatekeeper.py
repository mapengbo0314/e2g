import os
import sys
import argparse
import re

def check_phase_4_ready(workspace_path):
    """
    Ensures that Phase 4 (Execution) is authorized by verifying:
    1. A plan exists in artifacts/implementation_plan.md.
    2. A failing test log exists in artifacts/tdd_failing_test.log and contains a valid failure.
    """
    plan_path = os.path.join(workspace_path, "artifacts", "implementation_plan.md")
    test_log_path = os.path.join(workspace_path, "artifacts", "tdd_failing_test.log")

    errors = []

    # 1. Check for Implementation Plan
    if not os.path.exists(plan_path):
        errors.append(f"MISSING ARTIFACT: {plan_path} (Required for Phase 4)")
    else:
        print(f"PASS: Found {plan_path}")

    # 2. Check for TDD Failing Test Log
    if not os.path.exists(test_log_path):
        errors.append(f"MISSING ARTIFACT: {test_log_path} (Required to prove TDD Hard Gate)")
    else:
        with open(test_log_path, 'r') as f:
            content = f.read()
            # Look for common failure indicators in tracebacks
            failure_patterns = [
                r"AssertionError",
                r"FAILED",
                r"E       ", # pytest error indicator
                r"Traceback",
                r"Exception:",
                r"Error:"
            ]
            if not any(re.search(p, content, re.IGNORECASE) for p in failure_patterns):
                errors.append(f"INVALID ARTIFACT: {test_log_path} does not contain a verifiable failure trace. You must run the tests and capture the failure before implementation.")
            else:
                print(f"PASS: Found verifiable failure in {test_log_path}")

    if errors:
        print("\n--- GATEKEEPER FAILURE ---")
        for err in errors:
            print(f"- {err}")
        print("\nACTION: You MUST instruct the sub-agent to produce the missing or corrected artifacts before proceeding.")
        sys.exit(1)

    print("\nSUCCESS: Phase 4 Hard Gate passed. Implementation is authorized.")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Harness Protocol Gatekeeper")
    parser.add_argument("--phase", type=int, choices=[4], required=True, help="The phase to authorize")
    parser.add_argument("--workspace", type=str, default=".", help="Path to the workspace root")
    
    args = parser.parse_args()
    
    if args.phase == 4:
        check_phase_4_ready(args.workspace)

if __name__ == "__main__":
    main()
