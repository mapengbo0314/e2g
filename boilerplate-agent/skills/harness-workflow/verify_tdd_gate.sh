#!/usr/bin/env bash
# Hard Gate: Ensure TDD was actually used by the Implementer
# The Implementer must produce an artifact showing a failing test run BEFORE code was written.

ARTIFACT_DIR="workspace/artifacts"
TDD_EVIDENCE="$ARTIFACT_DIR/tdd_failing_test.log"
PLAN_DOC="$ARTIFACT_DIR/plan.md"

echo "=== TDD Hard Gate Verification ==="

# 1. Existence Check
if [ ! -f "$TDD_EVIDENCE" ]; then
    echo "ERROR [Hard Gate Failed]: TDD evidence not found."
    echo "The Implementer failed to produce '$TDD_EVIDENCE'."
    echo "You must prove that a failing test was written and executed before implementation."
    exit 1
fi

# 2. Recency Check
# Ensure the TDD log was created AFTER the plan.md was written.
# This prevents stale logs from previous runs from bypassing the gate.
if [ -f "$PLAN_DOC" ]; then
    if [ "$PLAN_DOC" -nt "$TDD_EVIDENCE" ]; then
        echo "ERROR [Hard Gate Failed]: Stale TDD evidence detected."
        echo "'$TDD_EVIDENCE' is older than the current '$PLAN_DOC'."
        echo "You must run the tests NOW and produce a fresh failure log for this specific task."
        exit 1
    fi
fi

# 3. Content Check
# Ensure the log actually contains signs of a failing test, not just an empty file or "hello world"
if ! grep -qiE "FAILED|AssertionError|Error:|Exception:|Traceback" "$TDD_EVIDENCE"; then
    echo "ERROR [Hard Gate Failed]: Invalid TDD evidence."
    echo "'$TDD_EVIDENCE' does not appear to contain a failing test output (Missing keywords: FAILED, AssertionError, etc.)."
    echo "Please provide a genuine failing test log."
    exit 1
fi

echo "SUCCESS: Fresh TDD evidence found."
exit 0
