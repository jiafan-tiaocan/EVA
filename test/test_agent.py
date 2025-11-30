import unittest
from src.memory import MemoryManager
from src.tools import create_calendar_event
import os

class TestAgentComponents(unittest.TestCase):
    
    def setUp(self):
        # 使用测试配置
        self.memory = MemoryManager(config_path="config/settings.yaml")

    def test_memory_add_and_search(self):
        self.memory.add_log("Finished debugging the Transformer attention mask issue.")
        results = self.memory.search_logs("Transformer")
        self.assertTrue(len(results) > 0)
        print("Memory Test Passed")

    def test_calendar_tool(self):
        result = create_calendar_event("Code Review", "2025-12-01T14:00:00")
        self.assertIn("invite_", result)
        self.assertTrue(os.path.exists(result.split(": ")[1].split(".")[0] + ".ics"))
        print("Calendar Tool Test Passed")
        
        # Cleanup
        for f in os.listdir():
            if f.endswith(".ics"):
                os.remove(f)

if __name__ == "__main__":
    unittest.main()