# 🧪 HabitVerse API Tester

This project is a Python-based unit testing suite for the **HabitVerse** backend API. It uses Python's `unittest` framework to verify the availability and behavior of key endpoints of a habit tracking service.

---

## 🚀 Project Overview

The HabitVerse API Tester checks critical API functionalities including:

- ✅ Server health status
- 👤 User profile retrieval
- 📈 Habit operations (create, update, delete - inferred from test structure)

The test suite is designed to ensure backend reliability and is easily extendable for CI/CD pipelines.

---

## 📁 Project Structure

```
app/
├── backend_test.py     # Main test suite for API
├── .git/               # Git version history and hooks
└── .gitignore          # Standard ignore rules
```

---

## 🧰 Dependencies

- Python 3.7+
- `requests`
- `unittest` (Python built-in)

Install dependencies:

```bash
pip install requests
```

---

## 🔧 Configuration

The test suite uses a hardcoded API base URL and demo user ID:

```python
self.base_url = "https://<your-api-endpoint>.preview.emergentagent.com"
self.user_id = "demo-user-123"
```

To customize:

1. Open `backend_test.py`
2. Replace the `self.base_url` with your own API endpoint.
3. Replace the user ID if needed.

---

## ▶️ Running Tests

```bash
cd app
python backend_test.py
```

Each test outputs status to the console, such as:

```
🔍 Testing health check endpoint...
✅ Health check passed

🔍 Testing get user endpoint...
✅ User data retrieved
```

---

## 🧪 Test Coverage

| Test Name             | Purpose                        |
|----------------------|--------------------------------|
| `test_01_health_check` | Verifies API is running        |
| `test_02_get_user`     | Fetches user profile info      |
| *(More in progress)*   | Extend with habit CRUD tests   |

---

## 🌐 Live Endpoint Example

The project was tested using:

```
https://1b093a12-9288-41b4-82c6-d5fb102a8023.preview.emergentagent.com
```

Update the domain in `backend_test.py` as needed.

---





## 📬 Contact

For feedback, suggestions, or collaborations, feel free to open an issue or pull request.
