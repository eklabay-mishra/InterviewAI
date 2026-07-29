import sys
from datetime import datetime, timedelta
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.interview import JobPosting, InterviewSession, InterviewResponse
from models.mcq import Question, McqTest, TestSession
from models.notification import Notification
from models.activity_log import ActivityLog

def run_seed_content():
    print("[Seed] Populating database tables for 100 Indian Candidates...")

    # 1. Create Default Recruiter (Eklabay Mishra - Senior Technical Recruiter)
    recruiter = User(
        name="Eklabay Mishra",
        email="recruiter@interviewai.com",
        role=Role.RECRUITER,
        status="active",
        company="InterviewAI",
        target_role="Senior Technical Recruiter"
    )
    recruiter.set_password("recruiter123")
    db.session.add(recruiter)
    db.session.commit()

    # 2. List of 100 Authentic Indian Candidate Names
    indian_names = [
        "XYZ", "Priya Sharma", "Aarav Mehta", "Ananya Verma", "Rohan Gupta",
        "Neha Patel", "Vikram Singh", "Pooja Iyer", "Aditya Kumar", "Sneha Rao",
        "Rahul Nair", "Kavya Joshi", "Siddharth Malhotra", "Ishita Deshmukh", "Arjun Banerji",
        "Riya Sen", "Karan Kapoor", "Divya Nambiar", "Varun Saxena", "Meera Pillai",
        "Abhinav Reddy", "Shreya Kulkarni", "Tanmay Bhatt", "Alok Mishra", "Swati Choudhury",
        "Manish Agarwal", "Deepika Thakur", "Nikhil Ghosh", "Richa Pandey", "Harsh Vardhan",
        "Tarun Batra", "Sonam Kapoor", "Gaurav Solanki", "Anusha Sundaram", "Pranav Chatterjee",
        "Bhavna Mittal", "Rajeshwari Bhat", "Karthik Subramanian", "Simran Kaur", "Yashwant Soni",
        "Pankaj Tripathi", "Ritu Raj", "Akash Deep", "Preeti Jain", "Mohit Chauhan",
        "Nandini Shah", "Vikas Khanna", "Tanya Bajaj", "Saurabh Sharma", "Monika Rawat",
        "Devendra Prasad", "Charu Sen", "Ramesh Iyer", "Bhumika Chawla", "Girish Hegde",
        "Lata Nair", "Naveen Chandra", "Poonam Bhasin", "Sachin Tendulkar", "Radhika Merchant",
        "Hemant Kumar", "Juhi Parmar", "Lokesh Rahul", "Pallavi Dey", "Ramanujan Pillai",
        "Sarita Saxena", "Umesh Yadav", "Vidya Balan", "Yuvraj Singh", "Zeenat Aman",
        "Ashwin Sundaram", "Bipasha Basu", "Chirag Paswan", "Drashti Dhami", "Esha Gupta",
        "Farhan Akhtar", "Gauahar Khan", "Hiten Tejwani", "Ileana D'Cruz", "Javed Ali",
        "Kriti Sanon", "Lucky Ali", "Mridul Agarwal", "Niti Taylor", "Omkar Kapoor",
        "Prachi Desai", "Raghav Juyal", "Sananya Malhotra", "Tusshar Kapoor", "Urfi Javed",
        "Varun Sharma", "Wamiqa Gabbi", "Yami Gautam", "Zubin Mehta", "Abhay Deol",
        "Bhumi Pednekar", "Chetan Bhagat", "Dia Mirza", "Ekta Kapoor", "Fatima Sana Shaikh"
    ]

    roles_pool = [
        "Python Full Stack Developer",
        "Data Scientist & AI Engineer",
        "SQL & Database Systems Engineer",
        "Software Engineer (OOP & System Design)",
        "HR Specialist & Behavioral Lead",
        "Machine Learning Engineer",
        "Backend Systems Engineer",
        "React & Python Developer"
    ]

    universities_pool = [
        "IIT Bombay", "IIT Delhi", "IIT Madras", "BITS Pilani", "IIIT Hyderabad",
        "Stanford University", "NYU", "UC Berkeley", "Delhi University", "Anna University"
    ]

    created_candidates = []
    for i, name in enumerate(indian_names):
        clean_name = name.lower().replace(' ', '.').replace("'", "")
        email = "candidate@interviewai.com" if name == "XYZ" else f"{clean_name}@example.com"
        target_role = roles_pool[i % len(roles_pool)]
        base_score = 92.0 if name == "XYZ" else round(68.0 + ((i * 7) % 28) + (i % 3) * 0.5, 1)
        exp_years = round(2.0 + (i % 8) * 0.8, 1)
        edu_uni = universities_pool[i % len(universities_pool)]

        user = User(
            name=name,
            email=email,
            role=Role.CANDIDATE,
            status="active",
            target_role=target_role
        )
        user.set_password("candidate123")
        db.session.add(user)
        db.session.commit()

        profile = CandidateProfile(
            user_id=user.id,
            resume_filename=f"{name.lower().replace(' ', '_')}_resume.pdf",
            resume_score=base_score,
            experience_years=exp_years,
            education=f"B.Tech / M.S. in CS - {edu_uni}",
            summary=f"Professional software developer specializing in {target_role} with expertise in Python, SQL, and System Design."
        )
        profile.parsed_skills = ["Python", "SQL", "Flask", "JavaScript", "REST API"]
        profile.missing_skills = ["Docker", "Kubernetes"]
        profile.projects = [
            {"title": "Enterprise Cloud System", "tech": "Python, Flask, MySQL", "url": "https://github.com/example/project"}
        ]
        profile.certificates = ["Certified Python Developer", "AWS Cloud Practitioner"]
        profile.analysis_data = {
            "resume_score": base_score,
            "parsed_skills": ["Python", "SQL", "Flask"],
            "missing_skills": ["Docker"],
            "recommendations": ["Gain experience with cloud container deployment."]
        }
        db.session.add(profile)
        db.session.commit()
        created_candidates.append(user)

    # 3. Create Job Postings by Recruiter Eklabay Mishra
    job1 = JobPosting(
        recruiter_id=recruiter.id,
        title="Senior Python Full Stack Engineer",
        role_type="Python Developer",
        description="Looking for an exceptional Senior Engineer experienced in Python, Flask, SQL, REST APIs, and modern frontend frameworks.",
        experience_level="Senior",
        difficulty="Hard",
        pass_score=75
    )
    job1.skills_required = ["Python", "Flask", "SQL", "MySQL", "JavaScript", "REST API"]

    job2 = JobPosting(
        recruiter_id=recruiter.id,
        title="AI & Data Science Engineer",
        role_type="Data Science",
        description="Seeking a Data Scientist / Machine Learning Engineer to build predictive AI pipelines using Python, Pandas, and SQL.",
        experience_level="Mid Level",
        difficulty="Medium",
        pass_score=70
    )
    job2.skills_required = ["Python", "Machine Learning", "Data Science", "SQL", "Pandas"]

    job3 = JobPosting(
        recruiter_id=recruiter.id,
        title="Backend Systems & Database Engineer",
        role_type="Backend Engineer",
        description="Responsible for relational database schema design, SQL query tuning, and microservices architecture.",
        experience_level="Mid Level",
        difficulty="Medium",
        pass_score=70
    )
    job3.skills_required = ["Python", "SQL", "MySQL", "SQLAlchemy"]

    db.session.add_all([job1, job2, job3])
    db.session.commit()

    # 4. Seed Distinct Role-Specific MCQ Question Bank
    raw_questions = []

    # Category A: Python (30 Questions across Easy, Medium, Hard)
    for i in range(1, 31):
        diff = "Easy" if i <= 10 else ("Medium" if i <= 20 else "Hard")
        raw_questions.append((
            "Python", diff,
            f"Python Question #{i}: What is the output/behavior of Python concept related to question {i} ({diff} level)?",
            f"Option A for Q{i}", f"Option B for Q{i} (Correct)", f"Option C for Q{i}", f"Option D for Q{i}",
            "B", f"Explanation for Python Q{i} ({diff} level)."
        ))

    # Category B: SQL (30 Questions across Easy, Medium, Hard)
    for i in range(1, 31):
        diff = "Easy" if i <= 10 else ("Medium" if i <= 20 else "Hard")
        raw_questions.append((
            "SQL", diff,
            f"SQL Question #{i}: Which query strategy or index handles database requirement #{i} ({diff} level)?",
            f"Option A for Q{i}", f"Option B for Q{i} (Correct)", f"Option C for Q{i}", f"Option D for Q{i}",
            "B", f"Explanation for SQL Q{i} ({diff} level)."
        ))

    # Category C: OOP (30 Questions across Easy, Medium, Hard)
    for i in range(1, 31):
        diff = "Easy" if i <= 10 else ("Medium" if i <= 20 else "Hard")
        raw_questions.append((
            "OOP", diff,
            f"OOP Question #{i}: Which Object-Oriented design principle applies to scenario #{i} ({diff} level)?",
            f"Option A for Q{i}", f"Option B for Q{i} (Correct)", f"Option C for Q{i}", f"Option D for Q{i}",
            "B", f"Explanation for OOP Q{i} ({diff} level)."
        ))

    # Category D: ML (30 Questions across Easy, Medium, Hard)
    for i in range(1, 31):
        diff = "Easy" if i <= 10 else ("Medium" if i <= 20 else "Hard")
        raw_questions.append((
            "ML", diff,
            f"ML Question #{i}: How does Machine Learning algorithm #{i} evaluate performance ({diff} level)?",
            f"Option A for Q{i}", f"Option B for Q{i} (Correct)", f"Option C for Q{i}", f"Option D for Q{i}",
            "B", f"Explanation for ML Q{i} ({diff} level)."
        ))

    # Category E: HR (30 Questions across Easy, Medium, Hard)
    for i in range(1, 31):
        diff = "Easy" if i <= 10 else ("Medium" if i <= 20 else "Hard")
        raw_questions.append((
            "HR", diff,
            f"HR Leadership Question #{i}: How should a lead handle behavioral situation #{i} ({diff} level)?",
            f"Option A for Q{i}", f"Option B for Q{i} (Correct)", f"Option C for Q{i}", f"Option D for Q{i}",
            "B", f"Explanation for HR Q{i} ({diff} level)."
        ))

    questions = []
    for q in raw_questions:
        q_obj = Question(
            category=q[0],
            difficulty=q[1],
            question_text=q[2],
            option_a=q[3],
            option_b=q[4],
            option_c=q[5],
            option_d=q[6],
            correct_option=q[7],
            explanation=q[8],
            created_by=recruiter.id
        )
        questions.append(q_obj)

    db.session.add_all(questions)
    db.session.commit()

    # 5. Create MCQ Tests with Role & Difficulty Standards:
    # Easy: 15 Questions / 20 Mins | Medium: 25 Questions / 30 Mins | Hard: 30 Questions / 45 Mins
    mcq_tests_seed = [
        ("Python Foundational Basics Test", "Python", "Easy", 15, 20),
        ("Python & Web Architecture Assessment", "Python", "Medium", 25, 30),
        ("Advanced CPython & GIL Hard Test", "Python", "Hard", 30, 45),
        ("SQL Fundamentals Quiz", "SQL", "Easy", 15, 20),
        ("SQL & Database Tuning Master Test", "SQL", "Hard", 30, 45),
        ("Object-Oriented Programming (OOP) Assessment", "OOP", "Medium", 25, 30),
        ("Machine Learning & AI Assessment", "ML", "Medium", 25, 30),
        ("HR & Behavioral Leadership Assessment", "HR", "Easy", 15, 20)
    ]

    created_mcq_tests = []
    for title, cat, diff, num_q, dur in mcq_tests_seed:
        test = McqTest(
            title=title,
            category=cat,
            total_questions=num_q,
            duration_minutes=dur,
            created_by=recruiter.id
        )
        db.session.add(test)
        created_mcq_tests.append(test)
    
    db.session.commit()

    # 6. Create Active (In Progress) and Completed Interview Sessions across Candidates
    now = datetime.utcnow()

    # A) 5 ACTIVE Ongoing Interviews
    active_candidates = created_candidates[1:6]
    for idx, cand in enumerate(active_candidates):
        active_sess = InterviewSession(
            candidate_id=cand.id,
            job_id=job1.id if idx % 2 == 0 else job2.id,
            role_title=cand.target_role,
            overall_score=0.0,
            total_questions=25,
            status="in_progress",
            created_at=now - timedelta(minutes=15 + idx * 5)
        )
        db.session.add(active_sess)
        db.session.commit()

    # B) 25 COMPLETED Interviews
    completed_candidates_sample = created_candidates[0:25]
    score_samples = [94.0, 91.5, 88.5, 86.0, 84.5, 82.0, 80.0, 78.5, 76.0, 75.0,
                     74.0, 72.5, 71.0, 69.5, 68.0, 95.0, 90.0, 87.0, 85.0, 83.0,
                     81.0, 79.0, 77.0, 73.0, 71.5]

    for idx, cand in enumerate(completed_candidates_sample):
        score_val = score_samples[idx % len(score_samples)]
        days_ago = (idx % 14) + 1
        comp_sess = InterviewSession(
            candidate_id=cand.id,
            job_id=job1.id if idx % 3 == 0 else (job2.id if idx % 3 == 1 else job3.id),
            role_title=cand.target_role,
            overall_score=score_val,
            total_questions=25,
            status="completed",
            created_at=now - timedelta(days=days_ago, minutes=30),
            completed_at=now - timedelta(days=days_ago)
        )
        db.session.add(comp_sess)
        db.session.commit()

        resp = InterviewResponse(
            session_id=comp_sess.id,
            question_number=1,
            question_text=f"Explain core principles of {cand.target_role}.",
            category="Technical Architecture",
            user_answer="Candidate provided a well-structured technical response with clean explanations.",
            score=score_val,
            feedback="Strong technical clarity and structured communication demonstrated.",
            model_answer="Model senior response detailing architecture patterns and performance optimization.",
            missing_concepts_json='["Advanced Edge Case Handling"]'
        )
        db.session.add(resp)

        # Also add completed MCQ test session
        ts = TestSession(
            candidate_id=cand.id,
            test_id=created_mcq_tests[idx % len(created_mcq_tests)].id,
            score=score_val,
            total_questions=25,
            correct_answers=int(25 * (score_val / 100)),
            completed_at=now - timedelta(days=days_ago)
        )
        db.session.add(ts)

    # 7. Activity Logs & Notifications
    notif = Notification(user_id=recruiter.id, message="Recruiter dashboard loaded with 100 Indian Candidates, 5 Live Active Interviews, and 25 Completed Assessment Scorecards.", type="success")
    log = ActivityLog(user_id=recruiter.id, action="Dashboard Initialized", details="Seeded 100 Indian Candidates, 5 Active Interviews, 25 Completed Interviews")
    db.session.add_all([notif, log])
    db.session.commit()

    print("[Seed] Successfully populated database with 100 Indian Candidates, distinct role MCQ banks, 5 Active Interviews, and 25 Completed Scorecards!")

def seed_database():
    try:
        import pymysql
        conn = pymysql.connect(host='localhost', user='root', password='', port=3306)
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE IF NOT EXISTS interview_ai;')
        conn.commit()
        conn.close()
    except Exception:
        pass

    from app import create_app
    app = create_app()
    with app.app_context():
        print("[Seed] Resetting and initializing database tables for 100 Indian Candidates...")
        db.drop_all()
        db.create_all()
        run_seed_content()

if __name__ == "__main__":
    seed_database()
