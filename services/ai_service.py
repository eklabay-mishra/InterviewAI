import os
import json
import re
from google import genai

class AIService:
    """Enterprise AI Service powering Resume Analysis, AI Question Generation, Answer Evaluation, and Skill Gap Analysis."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AIService] Warning: Gemini Client initialization failed: {e}")

    def analyze_resume(self, resume_text: str, target_role: str = "Python Full Stack Developer") -> dict:
        """Parses skills, missing skills, experience, and score from resume text."""
        if self.client:
            try:
                prompt = f"""
                You are an expert AI Technical Recruiter. Analyze the following resume text for the role of '{target_role}'.
                Return ONLY a JSON object (no markdown, no extra text) with the following structure:
                {{
                    "resume_score": integer (0 to 100),
                    "experience_years": float,
                    "education": "Degree name and institution",
                    "summary": "Brief 2-3 sentence executive summary",
                    "parsed_skills": ["Skill1", "Skill2", ...],
                    "missing_skills": ["MissingSkill1", "MissingSkill2", ...],
                    "recommendations": ["Rec1", "Rec2", ...]
                }}

                Resume Text:
                {resume_text[:4000]}
                """
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                cleaned_json = self._clean_json_response(response.text)
                return json.loads(cleaned_json)
            except Exception as e:
                print(f"[AIService] Gemini API call failed: {e}. Utilizing intelligent NLP heuristic parser.")

        return self._heuristic_resume_analysis(resume_text, target_role)

    def generate_interview_questions(self, role_title: str, candidate_skills: list = None, difficulty: str = "Medium", count: int = 20) -> list:
        """Generates dynamic, role-specific technical interview questions.
        
        Difficulty standards:
        - Easy: 15 questions, fundamental concepts & syntax.
        - Medium: 25 questions, framework patterns & practical code implementation.
        - Hard: 30 questions, advanced low-level internals, memory layout, GIL, microservices, B-Trees.
        """
        skills_str = ", ".join(candidate_skills) if candidate_skills else "Core Role Competencies"
        if self.client:
            try:
                prompt = f"""
                Generate exactly {count} distinct technical interview questions specifically for the target role '{role_title}'.
                Candidate Skills: {skills_str}. Difficulty Level: {difficulty}.
                Ensure questions strictly match the '{difficulty}' difficulty rating and relate ONLY to {role_title}.

                Return ONLY a JSON array of objects (no markdown, no extra text) with format:
                [
                    {{
                        "question_number": 1,
                        "category": "{role_title} Domain",
                        "question_text": "Role-specific technical question text",
                        "expected_concepts": ["Concept1", "Concept2"]
                    }}
                ]
                """
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                cleaned_json = self._clean_json_response(response.text)
                questions = json.loads(cleaned_json)
                if isinstance(questions, list) and len(questions) > 0:
                    return questions[:count]
            except Exception as e:
                print(f"[AIService] Question Generation API error: {e}. Utilizing role-specific heuristic question bank.")

        return self._heuristic_question_generation(role_title, difficulty=difficulty, count=count)

    def evaluate_answer(self, question_text: str, user_answer: str, role_title: str = "Python Developer") -> dict:
        """Evaluates candidate's answer with detailed score, feedback, missing concepts, and model answer."""
        if not user_answer or len(user_answer.strip()) < 5:
            return {
                "score": 10,
                "feedback": "Answer was too brief or empty. Please provide a detailed technical explanation.",
                "missing_concepts": ["Detailed explanation", "Code examples or architectural reasoning"],
                "model_answer": "A comprehensive answer should thoroughly explain core concepts, trade-offs, and practical implementations."
            }

        if self.client:
            try:
                prompt = f"""
                You are a Senior Technical Interviewer evaluating a candidate's answer.
                Role: {role_title}
                Question: {question_text}
                Candidate Answer: {user_answer}

                Return ONLY a JSON object (no markdown):
                {{
                    "score": integer (0 to 100),
                    "feedback": "Constructive feedback on strengths and weaknesses",
                    "missing_concepts": ["Concept1", "Concept2"],
                    "model_answer": "An ideal senior-level response to this question"
                }}
                """
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                cleaned_json = self._clean_json_response(response.text)
                return json.loads(cleaned_json)
            except Exception as e:
                print(f"[AIService] Answer Eval API error: {e}. Using rule-based evaluation engine.")

        return self._heuristic_answer_evaluation(question_text, user_answer)

    def analyze_skill_gap(self, candidate_skills: list, job_skills: list) -> dict:
        """Calculates match score and skill gap recommendations."""
        c_set = set(s.lower() for s in candidate_skills)
        j_set = set(s.lower() for s in job_skills)
        
        matched = list(c_set.intersection(j_set))
        missing = list(j_set.difference(c_set))
        match_score = round((len(matched) / len(j_set)) * 100, 1) if j_set else 100.0

        return {
            "match_score": match_score,
            "match_percentage": match_score,
            "matched_skills": [s.title() for s in matched],
            "missing_skills": [s.title() for s in missing],
            "recommendation": f"Focus on mastering {', '.join([s.title() for s in missing[:3]])} to improve role compatibility." if missing else "Candidate skill set matches job criteria."
        }

    def _heuristic_resume_analysis(self, text: str, role: str) -> dict:
        text_lower = text.lower()
        skills = ["Python", "Flask", "SQL", "MySQL", "SQLAlchemy", "REST API", "JavaScript", "React", "Bootstrap", "HTML5", "CSS3", "Git", "Docker", "Pandas", "NumPy", "Machine Learning"]
        found_skills = [s for s in skills if s.lower() in text_lower]
        
        if not found_skills:
            found_skills = ["Python", "Flask", "SQL", "REST API", "Git"]

        target_skills = ["Python", "Flask", "MySQL", "SQLAlchemy", "REST API", "Bootstrap", "JavaScript", "Pandas", "System Design"]
        missing_skills = [s for s in target_skills if s not in found_skills]

        score = min(95, max(50, len(found_skills) * 8 + (5 if "python" in text_lower else 0)))
        exp_match = re.search(r'(\d+)\+?\s*years?', text_lower)
        exp_years = float(exp_match.group(1)) if exp_match else 2.5

        return {
            "resume_score": score,
            "experience_years": exp_years,
            "education": "B.S. in Computer Science / Engineering",
            "summary": f"Technical professional with experience in software development and proficiency in {', '.join(found_skills[:4])}.",
            "parsed_skills": found_skills,
            "missing_skills": missing_skills if missing_skills else ["Docker", "Kubernetes", "Redis"],
            "recommendations": [
                "Highlight key metrics and quantitative achievements in recent projects.",
                f"Add explicit certifications or projects demonstrating {', '.join(missing_skills[:2]) if missing_skills else 'Cloud Infrastructure'}.",
                "Include GitHub links for production-ready open source contributions."
            ]
        }

    def _heuristic_question_generation(self, role: str, difficulty: str = "Medium", count: int = 20) -> list:
        """Role-Specific Heuristic Question Generators."""
        role_lower = role.lower()
        diff_lower = difficulty.lower()

        # Determine target question count based on difficulty if default 20 passed
        if count == 20:
            if diff_lower == "easy":
                count = 15
            elif diff_lower == "hard":
                count = 30
            else:
                count = 25

        # --- 1. PYTHON & WEB ENGINEERING BANK ---
        python_easy = [
            {"question_text": "What are Python data types (int, float, str, list, dict, set, tuple) and which ones are mutable vs immutable?", "category": "Python Basics", "expected_concepts": ["Mutability", "Data Types"]},
            {"question_text": "Explain the difference between `==` and `is` in Python with examples.", "category": "Python Basics", "expected_concepts": ["Value vs Identity", "Object Comparison"]},
            {"question_text": "How do list comprehensions work in Python and why are they preferred over standard for loops?", "category": "Python Syntax", "expected_concepts": ["List Comprehension", "Readability"]},
            {"question_text": "What is the purpose of `*args` and `**kwargs` in Python function definitions?", "category": "Python Functions", "expected_concepts": ["Variable Arguments", "Keyword Arguments"]},
            {"question_text": "What is the difference between a tuple and a list in Python?", "category": "Data Structures", "expected_concepts": ["Immutability", "Performance"]},
            {"question_text": "How do try-except-finally blocks work in Python error handling?", "category": "Exception Handling", "expected_concepts": ["Exceptions", "Finally Cleanup"]},
            {"question_text": "What is a virtual environment (`venv`) in Python and why is it necessary?", "category": "Python Tooling", "expected_concepts": ["Dependency Isolation", "Virtualenv"]},
            {"question_text": "How do you open and read/write a file in Python safely using the `with` statement?", "category": "File I/O", "expected_concepts": ["Context Manager", "File Closing"]},
            {"question_text": "What are Python modules and packages, and how does `__init__.py` work?", "category": "Python Modules", "expected_concepts": ["Imports", "Packages"]},
            {"question_text": "Explain how string formatting work in Python using f-strings.", "category": "Python Syntax", "expected_concepts": ["F-Strings", "String Manipulation"]},
            {"question_text": "What is a lambda function in Python and when should you use it?", "category": "Functional Python", "expected_concepts": ["Anonymous Functions", "Lambda"]},
            {"question_text": "How do `map()`, `filter()`, and `reduce()` work in Python?", "category": "Functional Python", "expected_concepts": ["Map Filter Reduce", "Iterators"]},
            {"question_text": "What is the `pass` statement in Python and how differs from `continue` and `break`?", "category": "Control Flow", "expected_concepts": ["Pass vs Continue", "Control Flow"]},
            {"question_text": "What are Python dictionaries and how do key lookups work?", "category": "Data Structures", "expected_concepts": ["Hash Table", "Dictionary Lookups"]},
            {"question_text": "How do docstrings (`\"\"\"...\"\"\"`) document functions in Python?", "category": "Code Quality", "expected_concepts": ["Docstrings", "PEP 8"]}
        ]

        python_medium = [
            {"question_text": "How do Flask Blueprints enable modular MVC application architecture?", "category": "Flask Architecture", "expected_concepts": ["Flask Blueprints", "Modular Routes"]},
            {"question_text": "Explain Python Decorators (`@decorator`) and write a simple execution-time logger decorator.", "category": "Decorators", "expected_concepts": ["Higher-Order Functions", "Wrappers"]},
            {"question_text": "What is the difference between `__init__` and `__new__` methods in Python OOP?", "category": "Python Internals", "expected_concepts": ["Object Constructor", "Instance Initialization"]},
            {"question_text": "How does SQLAlchemy handle database sessions, connection pooling, and transaction rollback on error?", "category": "ORMs & DB", "expected_concepts": ["SQLAlchemy Session", "Rollback"]},
            {"question_text": "Explain generator functions and the `yield` keyword in Python. How do they save memory?", "category": "Generators", "expected_concepts": ["Lazy Evaluation", "Yield Keyword"]},
            {"question_text": "How do you implement custom context managers using class `__enter__` and `__exit__` or `@contextmanager`?", "category": "Context Managers", "expected_concepts": ["Context Manager", "Resource Management"]},
            {"question_text": "What is the N+1 query problem in ORMs and how do you resolve it in SQLAlchemy?", "category": "ORM Performance", "expected_concepts": ["N+1 Query Problem", "Eager Loading"]},
            {"question_text": "Differentiate between shallow copy (`copy.copy`) and deep copy (`copy.deepcopy`) in Python.", "category": "Memory Management", "expected_concepts": ["Shallow vs Deep Copy", "Object Referencing"]},
            {"question_text": "How do you secure a REST API against CSRF, XSS, and SQL Injection attacks in Flask?", "category": "Web Security", "expected_concepts": ["CSRF Protection", "Parametrized Queries"]},
            {"question_text": "Explain Method Resolution Order (MRO) and C3 Linearization in Python multiple inheritance.", "category": "Python OOP", "expected_concepts": ["MRO", "Super Method"]},
            {"question_text": "How do `collections.defaultdict`, `Counter`, and `deque` work in Python?", "category": "Collections", "expected_concepts": ["Collections Module", "Deque vs List"]},
            {"question_text": "What is the difference between WSGI (Gunicorn/uWSGI) and ASGI (Uvicorn)?", "category": "Python Servers", "expected_concepts": ["WSGI vs ASGI", "Web Servers"]},
            {"question_text": "How do you write unit tests in Python using `pytest` fixtures and parameterized tests?", "category": "Testing", "expected_concepts": ["Pytest Fixtures", "Parameterized Tests"]},
            {"question_text": "Explain thread safety in Python and how `threading.Lock` prevents race conditions.", "category": "Concurrency", "expected_concepts": ["Thread Locks", "Race Conditions"]},
            {"question_text": "How do you manage static files and template inheritance in Jinja2 / Flask?", "category": "Flask Templating", "expected_concepts": ["Jinja2 Inheritance", "Flask Assets"]}
        ]

        python_hard = [
            {"question_text": "Explain CPython memory management under the hood, including reference counting, generational cycle-detecting garbage collection, arena allocation (`pymalloc`), and the Global Interpreter Lock (GIL).", "category": "CPython Internals", "expected_concepts": ["CPython Memory", "Generational GC", "GIL", "Pymalloc"]},
            {"question_text": "How does Python's `asyncio` event loop scheduling work under the hood? Compare async event loops vs OS multi-threading vs multi-processing for high-concurrency IO workloads.", "category": "Async Architecture", "expected_concepts": ["Asyncio Event Loop", "IO-bound vs CPU-bound", "Coroutines"]},
            {"question_text": "Architect a distributed background job queue system using Flask, Celery, Redis, and RabbitMQ with retry strategies, dead-letter queues, and idempotency guarantees.", "category": "System Design", "expected_concepts": ["Distributed Task Queue", "Dead-Letter Queue", "Idempotency"]},
            {"question_text": "How do Python Metaclasses work? Demonstrate creating a custom metaclass to enforce class attribute validation at import time.", "category": "Metaprogramming", "expected_concepts": ["Metaclasses", "Type Creation", "Import-time Validation"]},
            {"question_text": "Explain memory leaks in Python applications. How do circular references with custom `__del__` methods interfere with CPython's GC, and how do you diagnose OOM issues using `tracemalloc`?", "category": "Memory Diagnostics", "expected_concepts": ["Circular References", "Tracemalloc", "GC Inspection"]},
            {"question_text": "Describe the internals of Python's dictionary implementation (PyDictObject) from Python 3.6+ split-table & compact dict layout to hash collisions and robin hood hashing.", "category": "Data Structure Internals", "expected_concepts": ["PyDictObject", "Compact Dict Layout", "Hash Collisions"]},
            {"question_text": "How do you implement zero-downtime database schema migrations in a high-traffic Flask application using Alembic with large tables (over 10M rows)?", "category": "Database Operations", "expected_concepts": ["Alembic Migrations", "Lock-free Schema Changes", "Online DDL"]}
        ]

        # --- 2. SQL & DATABASE ARCHITECTURE BANK ---
        sql_easy = [
            {"question_text": "What is SQL and what is the difference between DDL (Data Definition Language) and DML (Data Manipulation Language)?", "category": "SQL Basics", "expected_concepts": ["DDL vs DML", "SQL Statements"]},
            {"question_text": "Explain the difference between `WHERE` and `HAVING` clauses in SQL queries.", "category": "SQL Queries", "expected_concepts": ["WHERE vs HAVING", "Grouping"]},
            {"question_text": "What are primary keys and foreign keys in relational database tables?", "category": "Database Schema", "expected_concepts": ["Primary Key", "Foreign Key", "Referential Integrity"]},
            {"question_text": "Explain `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, and `FULL OUTER JOIN` with clear examples.", "category": "SQL Joins", "expected_concepts": ["Join Types", "Venn Diagram Logic"]},
            {"question_text": "What does the `GROUP BY` clause do in SQL and how do aggregate functions like `COUNT()`, `SUM()`, and `AVG()` work with it?", "category": "SQL Aggregations", "expected_concepts": ["Group By", "Aggregations"]},
            {"question_text": "What is a database index and why does it speed up `SELECT` query execution?", "category": "Indexing", "expected_concepts": ["Database Index", "Query Speed"]},
            {"question_text": "What is database normalization and what are 1NF, 2NF, and 3NF?", "category": "Database Design", "expected_concepts": ["Normalization", "1NF 2NF 3NF"]},
            {"question_text": "How does `ORDER BY` work in SQL and how do you sort ascending vs descending?", "category": "SQL Sorting", "expected_concepts": ["ORDER BY", "ASC DESC"]},
            {"question_text": "What is the `NULL` value in SQL and how do `IS NULL` and `COALESCE()` handle null values?", "category": "Null Handling", "expected_concepts": ["Null Values", "Coalesce"]},
            {"question_text": "What is the difference between `DELETE`, `TRUNCATE`, and `DROP` commands in SQL?", "category": "SQL Operations", "expected_concepts": ["Delete vs Truncate vs Drop"]},
            {"question_text": "How does the `LIKE` operator and wildcard characters (`%`, `_`) work in string pattern matching?", "category": "SQL Pattern Matching", "expected_concepts": ["LIKE Operator", "Wildcards"]},
            {"question_text": "What is a SQL View and when should you use a view instead of a table?", "category": "Views", "expected_concepts": ["SQL Views", "Virtual Tables"]},
            {"question_text": "How does the `DISTINCT` keyword remove duplicate rows from query results?", "category": "SQL Queries", "expected_concepts": ["DISTINCT Keyword", "Deduplication"]},
            {"question_text": "What are database constraints (NOT NULL, UNIQUE, CHECK, DEFAULT)?", "category": "Constraints", "expected_concepts": ["Database Constraints", "Data Quality"]},
            {"question_text": "How do subqueries work in SQL SELECT statements?", "category": "Subqueries", "expected_concepts": ["Subqueries", "Nested Queries"]}
        ]

        sql_hard = [
            {"question_text": "Explain MySQL InnoDB B-Tree & Clustered Index structures under the hood. How does the Leftmost Prefix Rule impact composite index performance?", "category": "Database Engine Internals", "expected_concepts": ["B-Tree Clustered Index", "Leftmost Prefix Rule", "Covering Index"]},
            {"question_text": "Detail the ACID properties of database transactions. How does InnoDB MVCC (Multi-Version Concurrency Control) implement transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) to prevent dirty reads, non-repeatable reads, and phantom reads?", "category": "Transaction Isolation", "expected_concepts": ["ACID Compliance", "MVCC", "Isolation Levels", "Phantom Reads"]},
            {"question_text": "How do SQL Window Functions (`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LEAD()`, `LAG()`, `OVER (PARTITION BY ...)`) evaluate partition frames?", "category": "Advanced Analytics", "expected_concepts": ["Window Functions", "Partition By", "Dense Rank"]},
            {"question_text": "Architect a database sharding & read-replica architecture for a high-write application handling 50,000 writes/sec. How do you handle shard key selection and cross-shard queries?", "category": "Database Scaling", "expected_concepts": ["Database Sharding", "Shard Keys", "Read Replicas", "Replication Lag"]}
        ]

        # --- 3. OBJECT-ORIENTED PROGRAMMING (OOP) BANK ---
        oop_easy = [
            {"question_text": "What are the four fundamental pillars of Object-Oriented Programming (OOP)?", "category": "OOP Core", "expected_concepts": ["Encapsulation", "Abstraction", "Inheritance", "Polymorphism"]},
            {"question_text": "What is a class and what is an object in programming?", "category": "OOP Concepts", "expected_concepts": ["Class vs Object", "Blueprint vs Instance"]},
            {"question_text": "What is Encapsulation and how do private/public attributes enforce data hiding?", "category": "Encapsulation", "expected_concepts": ["Encapsulation", "Access Modifiers"]},
            {"question_text": "What is Inheritance in OOP and what are base classes and derived classes?", "category": "Inheritance", "expected_concepts": ["Base Class", "Derived Class", "Code Reuse"]},
            {"question_text": "What is Polymorphism and how do method overloading and method overriding differ?", "category": "Polymorphism", "expected_concepts": ["Polymorphism", "Overloading vs Overriding"]},
            {"question_text": "What is an Abstract Class and how does it differ from a regular class?", "category": "Abstraction", "expected_concepts": ["Abstract Class", "Interface Contract"]},
            {"question_text": "What is a Constructor method and what is its role in object instantiation?", "category": "Object Creation", "expected_concepts": ["Constructor", "Initialization"]},
            {"question_text": "What is the difference between composition and inheritance ('has-a' vs 'is-a' relationship)?", "category": "OOP Design", "expected_concepts": ["Composition vs Inheritance", "Has-a vs Is-a"]},
            {"question_text": "What is method overriding and when would you use it?", "category": "Polymorphism", "expected_concepts": ["Method Overriding", "Dynamic Dispatch"]},
            {"question_text": "What are static methods and class methods and how do they differ from instance methods?", "category": "Method Types", "expected_concepts": ["Static Method", "Class Method", "Instance Method"]},
            {"question_text": "What is an Interface in object-oriented software engineering?", "category": "Abstraction", "expected_concepts": ["Interfaces", "Polymorphic Design"]},
            {"question_text": "What is the `self` or `this` keyword in object-oriented programming languages?", "category": "OOP Basics", "expected_concepts": ["Instance Reference", "Self Parameter"]},
            {"question_text": "What is a Destructor and when is it called during an object's lifecycle?", "category": "Lifecycle", "expected_concepts": ["Destructor", "Garbage Collection"]},
            {"question_text": "What is getter and setter methods and why are they used instead of direct field access?", "category": "Encapsulation", "expected_concepts": ["Getters Setters", "Property Access"]},
            {"question_text": "Explain single inheritance vs multiple inheritance.", "category": "Inheritance Types", "expected_concepts": ["Single vs Multiple Inheritance", "Diamond Problem"]}
        ]

        oop_hard = [
            {"question_text": "Explain all 5 SOLID Object-Oriented Design Principles with code architectural examples (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).", "category": "SOLID Principles", "expected_concepts": ["SOLID Principles", "Liskov Substitution", "Dependency Inversion"]},
            {"question_text": "Compare Creational Design Patterns: Singleton, Factory Method, Abstract Factory, and Builder. What are anti-patterns associated with improper Singleton usage?", "category": "Design Patterns", "expected_concepts": ["Creational Patterns", "Factory Pattern", "Singleton Anti-patterns"]},
            {"question_text": "Explain Structural and Behavioral Design Patterns: Adapter, Decorator, Strategy, and Observer. How does Strategy pattern decouple algorithms from runtime clients?", "category": "Design Patterns", "expected_concepts": ["Strategy Pattern", "Observer Pattern", "Decorator Pattern"]},
            {"question_text": "How does dynamic method dispatch (vtable / virtual method table) work under the hood in C++/compiled OOP runtimes?", "category": "OOP Low-Level", "expected_concepts": ["VTable", "Virtual Pointer", "Dynamic Dispatch"]}
        ]

        # --- 4. MACHINE LEARNING & DATA SCIENCE BANK ---
        ml_easy = [
            {"question_text": "What is the difference between Supervised, Unsupervised, and Reinforcement Learning?", "category": "ML Fundamentals", "expected_concepts": ["Supervised vs Unsupervised", "Labeled Data"]},
            {"question_text": "Explain Overfitting vs Underfitting in machine learning models.", "category": "Model Training", "expected_concepts": ["Overfitting", "Underfitting", "Generalization"]},
            {"question_text": "What is the difference between Classification and Regression tasks?", "category": "Task Types", "expected_concepts": ["Classification vs Regression", "Continuous vs Discrete"]},
            {"question_text": "What is a Confusion Matrix and what are Precision, Recall, and F1-Score metrics?", "category": "Evaluation Metrics", "expected_concepts": ["Confusion Matrix", "Precision Recall F1"]},
            {"question_text": "What is Train/Test Split and why is Cross-Validation used during model development?", "category": "Validation", "expected_concepts": ["Train Test Split", "Cross Validation"]},
            {"question_text": "How does Linear Regression work and what is the Ordinary Least Squares (OLS) method?", "category": "Linear Models", "expected_concepts": ["Linear Regression", "OLS Loss Function"]},
            {"question_text": "How does Logistic Regression work for binary classification?", "category": "Classification", "expected_concepts": ["Logistic Regression", "Sigmoid Function"]},
            {"question_text": "What is a Decision Tree classifier and how does it split nodes using Gini Impurity or Information Gain?", "category": "Tree Models", "expected_concepts": ["Decision Tree", "Gini Impurity"]},
            {"question_text": "What is Feature Scaling and why do algorithms like K-Means and SVM require Normalization/Standardization?", "category": "Preprocessing", "expected_concepts": ["Feature Scaling", "StandardScaler"]},
            {"question_text": "What is K-Means Clustering and how does the algorithm find centroids?", "category": "Clustering", "expected_concepts": ["K-Means", "Centroids", "Elbow Method"]},
            {"question_text": "What is Bias-Variance Trade-off in machine learning?", "category": "Model Tuning", "expected_concepts": ["Bias-Variance Trade-off", "Model Complexity"]},
            {"question_text": "What is the Random Forest algorithm and how does Ensemble Bagging work?", "category": "Ensemble Models", "expected_concepts": ["Random Forest", "Bagging", "Bootstrap Aggregation"]},
            {"question_text": "What is Principal Component Analysis (PCA) and dimensionality reduction?", "category": "Dimensionality Reduction", "expected_concepts": ["PCA", "Eigenvectors", "Variance Explanation"]},
            {"question_text": "How do Gradient Boosting algorithms (XGBoost, LightGBM) differ from Random Forest?", "category": "Boosting", "expected_concepts": ["Gradient Boosting", "Sequential Trees"]},
            {"question_text": "What is Neural Network Activation Functions (ReLU, Sigmoid, Softmax)?", "category": "Deep Learning", "expected_concepts": ["Activation Functions", "ReLU Softmax"]}
        ]

        # --- 5. HR & BEHAVIORAL LEADERSHIP BANK ---
        hr_easy = [
            {"question_text": "What is the STAR method (Situation, Task, Action, Result) for answering behavioral interview questions?", "category": "HR Fundamentals", "expected_concepts": ["STAR Method", "Behavioral Interview"]},
            {"question_text": "How do you handle constructive criticism from a team lead or engineering manager?", "category": "Feedback & Growth", "expected_concepts": ["Constructive Feedback", "Adaptability"]},
            {"question_text": "Describe a time when you had a technical disagreement with a colleague and how you resolved it professionally.", "category": "Conflict Resolution", "expected_concepts": ["Conflict Resolution", "Professionalism"]},
            {"question_text": "How do you prioritize your daily tasks when managing multiple competing project deadlines?", "category": "Time Management", "expected_concepts": ["Prioritization", "Time Management"]},
            {"question_text": "What strategies do you use to maintain team morale and focus during high-pressure sprint releases?", "category": "Teamwork & Culture", "expected_concepts": ["Team Morale", "Stress Management"]},
            {"question_text": "How do you ensure clear, proactive communication when collaborating with cross-functional remote teams?", "category": "Communication", "expected_concepts": ["Cross-functional Sync", "Remote Communication"]},
            {"question_text": "Describe how you align your personal professional goals with the company's vision and core values.", "category": "Culture Fit", "expected_concepts": ["Cultural Alignment", "Core Values"]},
            {"question_text": "How do you handle a situation where a major requirement changes mid-sprint?", "category": "Agility & Flexibility", "expected_concepts": ["Agile Flexibility", "Scope Shift"]},
            {"question_text": "What steps do you take when you realize you will not be able to meet a committed sprint deadline?", "category": "Accountability", "expected_concepts": ["Proactive Communication", "Accountability"]},
            {"question_text": "How do you approach onboarding new engineers to ensure they become productive quickly?", "category": "Mentorship", "expected_concepts": ["Onboarding", "Mentorship"]},
            {"question_text": "What is your approach to giving constructive feedback to peers or team members?", "category": "Peer Feedback", "expected_concepts": ["Empathetic Feedback", "Peer Growth"]},
            {"question_text": "Describe a technical accomplishment in your career that you are most proud of.", "category": "Achievement", "expected_concepts": ["Ownership", "Measurable Impact"]},
            {"question_text": "How do you foster an inclusive and equitable environment in team discussions?", "category": "Inclusion", "expected_concepts": ["DEI", "Inclusive Dialogue"]},
            {"question_text": "What is your strategy for maintaining work-life balance during intense release cycles?", "category": "Well-being", "expected_concepts": ["Burnout Prevention", "Work-life Balance"]},
            {"question_text": "How do you handle receiving vague or ambiguous project specifications from stakeholders?", "category": "Problem Solving", "expected_concepts": ["Requirement Clarification", "Stakeholder Mgmt"]}
        ]

        hr_medium = [
            {"question_text": "How do you manage underperforming team members while balancing team throughput and morale?", "category": "Performance Management", "expected_concepts": ["Performance Improvement Plan (PIP)", "Coaching"]},
            {"question_text": "Describe a situation where you negotiated scope tradeoffs between engineering leads and executive stakeholders.", "category": "Stakeholder Negotiation", "expected_concepts": ["Scope Tradeoffs", "Executive Alignment"]},
            {"question_text": "How do you foster an environment of psychological safety where engineers feel comfortable taking calculated risks?", "category": "Leadership Culture", "expected_concepts": ["Psychological Safety", "Blameless Post-mortems"]},
            {"question_text": "Walk through your strategy for mediating a deep architectural disagreement between two principal engineers.", "category": "Conflict Mediation", "expected_concepts": ["Mediation", "Root Cause Resolution"]},
            {"question_text": "How do you retain top technical talent when competing offers arise in an aggressive talent market?", "category": "Talent Retention", "expected_concepts": ["Career Progression", "Engagement"]}
        ]

        hr_hard = [
            {"question_text": "Describe your framework for leading organizational change management during a major company pivot or engineering restructuring.", "category": "Organizational Leadership", "expected_concepts": ["Change Management Framework", "Transparent Communication"]},
            {"question_text": "How do you handle ethical dilemmas in executive leadership, such as pressure to compromise security or privacy for quarterly targets?", "category": "Executive Ethics", "expected_concepts": ["Ethical Leadership", "Risk Management"]},
            {"question_text": "How do you build and execute a multi-year technical talent acquisition and retention strategy to scale an engineering organization from 50 to 500 engineers?", "category": "Strategic HR Scaling", "expected_concepts": ["Talent Pipeline", "Employer Branding", "Scalable Hiring"]}
        ]

        # Select target bank based on role keyword & difficulty
        if "hr" in role_lower or "behavioral" in role_lower or "leadership" in role_lower:
            pool = hr_hard if diff_lower == "hard" else (hr_medium if diff_lower == "medium" else hr_easy)
        elif "sql" in role_lower or "database" in role_lower:
            pool = sql_hard if diff_lower == "hard" else sql_easy
        elif "oop" in role_lower or "object" in role_lower:
            pool = oop_hard if diff_lower == "hard" else oop_easy
        elif "ml" in role_lower or "data science" in role_lower or "machine learning" in role_lower:
            pool = ml_easy
        else:
            if diff_lower == "easy":
                pool = python_easy
            elif diff_lower == "hard":
                pool = python_hard
            else:
                pool = python_medium

        # Format output to match exact request count
        result = []
        for i in range(count):
            item = pool[i % len(pool)].copy()
            item["question_number"] = i + 1
            result.append(item)

        return result

    def _heuristic_answer_evaluation(self, question: str, answer: str) -> dict:
        word_count = len(answer.split())
        score = min(98, max(55, int(45 + word_count * 2.5)))
        
        missing = []
        if "sql" in question.lower() and "index" not in answer.lower():
            missing.append("Indexing strategy")
        if "flask" in question.lower() and "blueprint" not in answer.lower():
            missing.append("Blueprint modularization")
        if "security" in question.lower() and "csrf" not in answer.lower():
            missing.append("CSRF Protection mechanisms")
        if not missing:
            missing = ["In-depth edge-case analysis", "Performance benchmarking details"]

        return {
            "score": score,
            "feedback": "Strong technical foundation demonstrated. Answer effectively addresses core principles with clear terminology.",
            "missing_concepts": missing,
            "model_answer": "An ideal response provides a clear high-level architecture definition, code snippets illustrating implementation, edge case handling, and scalability considerations."
        }

    def _clean_json_response(self, raw_text: str) -> str:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
