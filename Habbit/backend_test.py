import requests
import unittest
import json
import os
import sys
from datetime import datetime

class HabitVerseAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HabitVerseAPITester, self).__init__(*args, **kwargs)
        # Use the public endpoint from frontend/.env
        self.base_url = "https://1b093a12-9288-41b4-82c6-d5fb102a8023.preview.emergentagent.com"
        self.user_id = "demo-user-123"
        self.test_habit_id = None

    def test_01_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health check passed")

    def test_02_get_user(self):
        """Test getting user profile"""
        print("\n🔍 Testing get user endpoint...")
        response = requests.get(f"{self.base_url}/api/users/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.user_id)
        self.assertIn("current_level", data)
        self.assertIn("avatar_evolution", data)
        print(f"✅ Get user passed - User: {data['username']}, Level: {data['current_level']}")
        return data

    def test_03_create_habit(self):
        """Test creating a new habit"""
        print("\n🔍 Testing create habit endpoint...")
        test_habit = {
            "name": f"Test Habit {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test habit created by the API tester",
            "category": "productivity",
            "difficulty": 2,
            "user_id": self.user_id
        }
        
        response = requests.post(f"{self.base_url}/api/habits", json=test_habit)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], test_habit["name"])
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["xp_reward"], test_habit["difficulty"] * 10)
        
        # Save habit ID for later tests
        self.test_habit_id = data["id"]
        print(f"✅ Create habit passed - Habit: {data['name']}, XP: {data['xp_reward']}")
        return data

    def test_04_get_habits(self):
        """Test getting user habits"""
        print("\n🔍 Testing get habits endpoint...")
        response = requests.get(f"{self.base_url}/api/habits/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Check if our test habit is in the list
        if self.test_habit_id:
            found = False
            for habit in data:
                if habit["id"] == self.test_habit_id:
                    found = True
                    break
            self.assertTrue(found, "Test habit not found in habits list")
        
        print(f"✅ Get habits passed - Found {len(data)} habits")
        return data

    def test_05_complete_habit(self):
        """Test completing a habit"""
        print("\n🔍 Testing complete habit endpoint...")
        if not self.test_habit_id:
            self.skipTest("No test habit ID available")
        
        completion_data = {
            "user_id": self.user_id,
            "habit_id": self.test_habit_id,
            "mood_rating": 4,
            "energy_level": 4
        }
        
        response = requests.post(f"{self.base_url}/api/habits/{self.test_habit_id}/complete", json=completion_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("xp_earned", data)
        self.assertIn("message", data)
        
        print(f"✅ Complete habit passed - XP earned: {data.get('xp_earned', 0)}")
        return data

    def test_06_log_mood(self):
        """Test logging mood"""
        print("\n🔍 Testing log mood endpoint...")
        mood_data = {
            "user_id": self.user_id,
            "mood_rating": 5,
            "energy_level": 4,
            "notes": "Feeling great today! API test."
        }
        
        response = requests.post(f"{self.base_url}/api/mood", json=mood_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["mood_rating"], mood_data["mood_rating"])
        
        print(f"✅ Log mood passed - Mood: {data['mood_rating']}/5, Energy: {data['energy_level']}/5")
        return data

    def test_07_get_dashboard(self):
        """Test getting dashboard data"""
        print("\n🔍 Testing dashboard endpoint...")
        response = requests.get(f"{self.base_url}/api/dashboard/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check dashboard structure
        self.assertIn("user", data)
        self.assertIn("habits", data)
        self.assertIn("ai_message", data)
        
        print(f"✅ Dashboard passed - User level: {data['user']['current_level']}, XP: {data['user']['total_xp']}")
        
        # Check if AI message is present
        if data["ai_message"]:
            print(f"🤖 AI Message: {data['ai_message']}")
        
        # Check if daily quest is present
        if data.get("daily_quest"):
            print(f"⚡ Daily Quest: {data['daily_quest']['title']}")
        
        return data

    def test_08_get_suggestions(self):
        """Test getting AI habit suggestions"""
        print("\n🔍 Testing habit suggestions endpoint...")
        response = requests.get(f"{self.base_url}/api/suggestions/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        self.assertIsInstance(data["suggestions"], list)
        
        print(f"✅ Suggestions passed - Found {len(data['suggestions'])} suggestions")
        
        # Print a sample suggestion if available
        if data["suggestions"]:
            suggestion = data["suggestions"][0]
            print(f"📝 Sample suggestion: {suggestion['name']} - {suggestion['description']} ({suggestion['category']})")
        
        return data

    def test_09_get_stats(self):
        """Test getting user stats"""
        print("\n🔍 Testing user stats endpoint...")
        response = requests.get(f"{self.base_url}/api/stats/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check stats structure
        self.assertIn("total_habits_completed", data)
        self.assertIn("current_level", data)
        self.assertIn("avatar_evolution", data)
        
        print(f"✅ Stats passed - Level: {data['current_level']}, Habits completed: {data['total_habits_completed']}")
        return data

def run_tests():
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests in order
    test_cases = [
        'test_01_health_check',
        'test_02_get_user',
        'test_03_create_habit',
        'test_04_get_habits',
        'test_05_complete_habit',
        'test_06_log_mood',
        'test_07_get_dashboard',
        'test_08_get_suggestions',
        'test_09_get_stats'
    ]
    
    # Create an instance of the test class
    test_instance = HabitVerseAPITester()
    
    # Add each test to the suite
    for test_name in test_cases:
        suite.addTest(HabitVerseAPITester(test_name))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    print("🚀 Starting HabitVerse API Tests")
    sys.exit(run_tests())