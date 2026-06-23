# TestMu: Pytest & Automated Testing Skill

## 🎯 Goal
Ensure the codebase remains inherently testable and that AI-generated logic is structured to support CI/CD pipelines and Unit Testing out-of-the-box.

## 📋 Core Directives
- **Testability First:** Design core logic as pure functions without side-effects whenever possible. Decouple business logic from I/O (File System, GUI, Network).
- **Dependency Injection:** Pass heavy instances (Database clients, OpenAI clients, UI widgets) into logic functions as arguments to allow seamless mocking during tests.
- **Mocking Strategy:** Use `unittest.mock.patch` or `pytest-mock` to intercept network calls. Never make live API calls inside unit tests.
- **Edge Case Documentation:** When writing regex parsers or string manipulators, immediately document boundary cases (empty strings, None, malformed JSON) to remind the tester what needs coverage.
- **Fixture Readiness:** Group repeatable test data setup into logic that can easily be mapped to `@pytest.fixture`.
