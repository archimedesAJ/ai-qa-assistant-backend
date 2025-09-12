# ai_core/mock_provider.py

class MockProvider:
    def __init__(self):
        pass

    def generate_test_cases(self, prompt: str, meta: dict = None) -> str:
        
        # Mocked artifacts
        test_cases = [
            "Verify valid login with correct username and password",
            "Verify error message for incorrect password",
            "Verify account is locked after 3 failed attempts"
        ]
        test_plan = {
            "scope": "Login functionality",
            "risks": "Weak passwords, brute force attempts",
            "assumptions": "User already registered"
        }

        raw_text = f"""
        MOCKED TEST ARTIFACTS
        =====================
        Prompt received:
        {prompt}

        Generated Test Cases:
        {chr(10).join([f"{i+1}. {tc}" for i, tc in enumerate(test_cases)])}

        Test Plan:
        - Scope: {test_plan['scope']}
        - Risks: {test_plan['risks']}
        - Assumptions: {test_plan['assumptions']}

        (This is a mocked response)
        """

        return {
            "test_cases": test_cases,
            "test_plan": test_plan,
            "raw": raw_text.strip()
        }
