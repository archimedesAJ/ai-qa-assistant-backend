TEST_CASE_SCHEMA = """Return JSON with this exact shape:
{
  "test_cases": [
    {
      "id": "string",
      "title": "string",
      "priority": "P0|P1|P2",
      "type": "Functional|Regression|Negative|Boundary|Security|API|Performance|Usability",
      "preconditions": "string",
      "steps": [
        "Given ...",
        "When ...",
        "Then ..."
      ],
      "expected_result": "string",
      "tags": ["string"],
      "automation_candidate": "Yes|No|Needs Analysis"
    }
  ]
}
"""

TEST_PLAN_SCHEMA = """Return JSON with this exact shape:
{
  "feature":"string",
  "objectives":["string"],
  "scope":{"in_scope":["string"], "out_of_scope":["string"]},
  "approach":"string",
  "test_types":["Functional","Regression","API","Security","Performance","Usability"],
  "environments":["string"],
  "data_and_tools":{"test_data":["string"], "tools":["string"]},
  "roles_and_responsibilities":["string"],
  "risks_and_mitigations":[{"risk":"string","mitigation":"string"}],
  "entry_criteria":["string"],
  "exit_criteria":["string"]
}
"""

def build_requirement_text(
    user_story: str = "",
    acceptance_criteria: str = "",
    feature_description: str = "",
    doc_text: str = "",
    app_context: str = ""
) -> str:
    """
    Combine all requirement inputs into a single context block for the LLM.
    """
    parts = []
    if app_context:
        parts.append(f"Application Context:\n{app_context.strip()}")
    if feature_description:
        parts.append(f"Feature Description:\n{feature_description.strip()}")
    if user_story:
        parts.append(f"User Story:\n{user_story.strip()}")
    if acceptance_criteria:
        parts.append(f"Acceptance Criteria:\n{acceptance_criteria.strip()}")
    if doc_text:
        # avoid sending overly large text blocks
        parts.append(f"Document Extracts:\n{doc_text.strip()[:50000]}")

    return "\n\n".join(parts)

def test_case_prompt(app_context: str, requirement_text: str, max_cases: int = 10) -> str:
    """
    Build a prompt for generating structured test cases in Gherkin style.
    """
    return f"""
You are a senior QA engineer. Use the application context and requirements 
to produce high-quality, de-duplicated test cases with good coverage.


{requirement_text}

Instructions:
- Generate up to {max_cases} test cases.
- Include negative and boundary tests where applicable.
- Write steps in **Gherkin style** (Given/When/Then).
- Keep steps concise, actionable, and readable.
- Strictly follow this JSON schema:
{TEST_CASE_SCHEMA}
"""

def test_plan_prompt(app_context: str, requirement_text: str) -> str:
    """
    Build a prompt for generating a structured test plan.
    """
    return f"""
You are a QA lead. Create a pragmatic test plan for the feature below.

{requirement_text}

Instructions:
- Keep it practical and sprint-sized.
- Include environments, entry/exit criteria, risks and mitigations.
- Strictly follow this JSON schema:
{TEST_PLAN_SCHEMA}
"""