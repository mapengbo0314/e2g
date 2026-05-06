import unittest
from indexing.ast_extractor import generate_deterministic_id, extract_skeleton
from indexing.schema import FileSkeleton, SkeletonSymbol, SkeletonInvariant

class TestIdCollision(unittest.TestCase):
    def test_cross_file_collision(self):
        id1 = generate_deterministic_id("file1.py", "my_func", "def my_func()")
        id2 = generate_deterministic_id("file2.py", "my_func", "def my_func()")
        self.assertNotEqual(id1, id2, "Cross-file symbols with the same signature should have different IDs")

    def test_invariant_collision_in_same_file(self):
        source = """
import threading
lock1 = threading.Lock()
lock2 = threading.Lock()
"""
        skeleton = extract_skeleton("test.py", source)
        ids = [inv.id for inv in skeleton.invariants]
        print(f"Invariant IDs: {ids}")
        self.assertEqual(len(ids), 2)
        self.assertNotEqual(ids[0], ids[1], "Invariants of same type in same file should have different IDs")

if __name__ == "__main__":
    unittest.main()
