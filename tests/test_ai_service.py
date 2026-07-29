import pytest
from services.ai_service import AIService

def test_ai_resume_analysis_heuristic():
    ai = AIService(api_key="")
    sample_resume = "Experienced Python developer skilled in Flask, MySQL, SQLAlchemy, JavaScript, and Git. 5 years experience."
    res = ai.analyze_resume(sample_resume, target_role="Python Developer")
    
    assert "resume_score" in res
    assert res["resume_score"] > 50
    assert "Python" in res["parsed_skills"]
    assert "Flask" in res["parsed_skills"]

def test_ai_question_generation():
    ai = AIService(api_key="")
    qs = ai.generate_interview_questions("Python Developer", ["Python", "Flask"], count=3)
    assert len(qs) == 3
    assert "question_text" in qs[0]

def test_ai_answer_evaluation():
    ai = AIService(api_key="")
    eval_res = ai.evaluate_answer("How does Python memory management work?", "Python uses reference counting and generational garbage collection for cyclic references.")
    assert eval_res["score"] > 60
    assert "feedback" in eval_res

def test_ai_skill_gap_analysis():
    ai = AIService(api_key="")
    gap = ai.analyze_skill_gap(["Python", "Flask"], ["Python", "Flask", "Docker", "Kubernetes"])
    assert gap["match_percentage"] == 50.0
    assert "Docker" in gap["missing_skills"]
