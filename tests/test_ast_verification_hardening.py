"""Tests for AST extraction and hardened verification."""

import unittest
import json
from pathlib import Path
import tempfile
from indexing import ast_extractor
from indexing import verification
from indexing import schema
from indexing import verification_types

class FakeLlmPrompter:
    def verify_artifact(self, artifact_json: str, source_context: str, directory_files: list[str] | None = None, is_merger_mode: bool = False) -> verification_types.VerificationVerdict:
        return verification_types.VerificationVerdict.success()

class AstVerificationHardeningTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_python_ast_extraction(self):
        code = "def my_func(a: int) -> str: return str(a)\nclass MyClass: pass"
        symbols, _ = ast_extractor.extract_ast_grounding("test.py", code)
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0].name, "my_func")
        self.assertIn("def my_func(a: int) -> str", symbols[0].signature)
        self.assertEqual(symbols[1].name, "MyClass")
        self.assertEqual(symbols[1].signature, "class MyClass")

    def test_typescript_ast_extraction(self):
        code = """
        export class UserService extends BaseService {
            constructor() {}
        }
        export async function getUser(id: string): Promise<User> {
            return null;
        }
        const helper = (x) => x * 2;
        """
        symbols, _ = ast_extractor.extract_ast_grounding("user.ts", code)
        self.assertEqual(len(symbols), 3)
        self.assertEqual(symbols[0].name, "UserService")
        self.assertEqual(symbols[0].signature, "class UserService")
        self.assertEqual(symbols[1].name, "getUser")
        self.assertIn("function getUser(id: string)", symbols[1].signature)
        self.assertEqual(symbols[2].name, "helper")
        self.assertEqual(symbols[2].signature, "const helper = ...")

    def test_go_ast_extraction(self):
        code = """
        package main
        import "sync"
        type Database struct {
            mu sync.Mutex
        }
        func (d *Database) Save(data string) error {
            return nil
        }
        func Load() (string, error) {
            return "", nil
        }
        """
        symbols, invariants = ast_extractor.extract_ast_grounding("db.go", code)
        # Go extraction: Database, Save, Load
        self.assertEqual(len(symbols), 3)
        self.assertEqual(symbols[0].name, "Database")
        self.assertEqual(symbols[0].signature, "type Database struct")
        self.assertEqual(symbols[1].name, "Save")
        self.assertEqual(symbols[1].signature, "func Save(data string)")
        self.assertEqual(symbols[2].name, "Load")
        self.assertEqual(symbols[2].signature, "func Load()")
        
        self.assertEqual(len(invariants), 1)
        self.assertEqual(invariants[0].primitive, "sync.Mutex")

    def test_hardened_verification_signature_mismatch(self):
        prompter = FakeLlmPrompter()
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        source_context = "--- test.py ---\ndef real_func(a: int) -> int: return a"
        
        # LLM returns wrong signature
        artifact = schema.IndexDocument(
            overview=schema.Overview(content="test"),
            key_interfaces=schema.KeyInterfaces(interfaces=[schema.Interface(name="i", description="d")]),
            implementation_invariants=schema.ImplementationInvariants(invariants=[]),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(
                    name="real_func",
                    signature="def real_func(a: string) -> string", # Wrong signature
                    summary="oops",
                    file_path="test.py",
                    line_number=1,
                    end_line_number=1
                )
            ])
        )
        
        verdict = verifier.verify(artifact.model_dump_json(), source_context)
        self.assertFalse(verdict.passed)
        # Match the new more detailed error message (case insensitive)
        self.assertIn("signature mismatch", verdict.issues[0].lower())

    def test_hardened_verification_file_path_mismatch(self):
        prompter = FakeLlmPrompter()
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        source_context = "--- src/test.py ---\ndef real_func(): pass"
        
        # LLM returns wrong file path
        artifact = schema.IndexDocument(
            overview=schema.Overview(content="test"),
            key_interfaces=schema.KeyInterfaces(interfaces=[schema.Interface(name="i", description="d")]),
            implementation_invariants=schema.ImplementationInvariants(invariants=[]),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(
                    name="real_func",
                    signature="def real_func()",
                    summary="oops",
                    file_path="wrong/path.py",
                    line_number=1,
                    end_line_number=1
                )
            ])
        )
        
        verdict = verifier.verify(artifact.model_dump_json(), source_context)
        self.assertFalse(verdict.passed)
        # In the new strict compound key implementation, path mismatch is a "Missing mandatory symbol"
        self.assertIn("Missing mandatory AST symbol", verdict.issues[0])

    def test_hardened_verification_success(self):
        prompter = FakeLlmPrompter()
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        source_context = "--- test.py ---\ndef real_func(a: int) -> int: return a"
        
        artifact = schema.IndexDocument(
            overview=schema.Overview(content="test"),
            key_interfaces=schema.KeyInterfaces(interfaces=[schema.Interface(name="i", description="d")]),
            implementation_invariants=schema.ImplementationInvariants(invariants=[]),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(
                    name="real_func",
                    signature="def real_func(a: int) -> int",
                    summary="correct",
                    file_path="test.py",
                    line_number=1,
                    end_line_number=1
                )
            ])
        )
        
        verdict = verifier.verify(artifact.model_dump_json(), source_context)
        self.assertTrue(verdict.passed)

if __name__ == '__main__':
    unittest.main()
