"""Seed data matching the assignment specification, real course catalog, and sample scenario.
Role: Full Stack Developer
Skills:
- Python (R=70, I=0.8)
- SQL (R=60, I=0.6)
- HTML (R=50, I=0.5)
- JavaScript (R=80, I=1.0)
- React (R=75, I=1.0)
- Node.js (R=70, I=0.9)
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import (
    Skill, CareerRole, RoleSkillRequirement, LearningResource,
    User, UserSkill, UserCareerGoal, BKTState, UserSettings,
    Recommendation, Certificate
)
from ..core.security import hash_password
from ..core.certificate import generate_certificate_pdf
from ..formulas.proficiency import calculate_skill_proficiency

def seed_database(db: Session):
    # 1. Create Skills
    skills_data = [
        {"name": "Python", "category": "Backend"},
        {"name": "SQL", "category": "Database"},
        {"name": "HTML", "category": "Frontend"},
        {"name": "JavaScript", "category": "Frontend"},
        {"name": "React", "category": "Frontend Framework"},
        {"name": "Node.js", "category": "Backend Runtime"},
    ]

    skill_records = {}
    for s_item in skills_data:
        skill = db.query(Skill).filter_by(name=s_item["name"]).first()
        if not skill:
            skill = Skill(name=s_item["name"], category=s_item["category"])
            db.add(skill)
            db.flush()
        skill_records[s_item["name"]] = skill

    # 2. Create Career Role: Full Stack Developer
    role_title = "Full Stack Developer"
    role = db.query(CareerRole).filter_by(title=role_title).first()
    if not role:
        role = CareerRole(
            title=role_title,
            description="Designs, builds, and maintains full-stack web applications across frontend UI, backend APIs, and databases."
        )
        db.add(role)
        db.flush()

    # 3. Create Role Skill Requirements
    requirements = [
        {"skill": "Python", "R_s": 70.0, "I_s": 0.8},
        {"skill": "SQL", "R_s": 60.0, "I_s": 0.6},
        {"skill": "HTML", "R_s": 50.0, "I_s": 0.5},
        {"skill": "JavaScript", "R_s": 80.0, "I_s": 1.0},
        {"skill": "React", "R_s": 75.0, "I_s": 1.0},
        {"skill": "Node.js", "R_s": 70.0, "I_s": 0.9},
    ]

    for req in requirements:
        skill = skill_records[req["skill"]]
        existing_req = db.query(RoleSkillRequirement).filter_by(role_id=role.id, skill_id=skill.id).first()
        if not existing_req:
            r_entry = RoleSkillRequirement(
                role_id=role.id,
                skill_id=skill.id,
                R_s=req["R_s"],
                I_s=req["I_s"]
            )
            db.add(r_entry)

    # 4. Create Real Course Catalog (Minimum 3 real free resources per skill = 18 total)
    resources_data = [
        # Python (3 Real Resources)
        {
            "title": "freeCodeCamp Scientific Computing with Python",
            "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
            "skill": "Python",
            "provider": "freeCodeCamp",
            "difficulty": 1,
            "est_hours": 20.0,
            "tags": "python, backend, fundamentals, algorithms, data-structures"
        },
        {
            "title": "Official Python 3 Documentation Tutorial",
            "url": "https://docs.python.org/3/tutorial/",
            "skill": "Python",
            "provider": "Python Software Foundation",
            "difficulty": 2,
            "est_hours": 15.0,
            "tags": "python, backend, oop, language-reference, standard-library"
        },
        {
            "title": "Real Python: Python Basics & Practical Exercises",
            "url": "https://realpython.com/python-basics/",
            "skill": "Python",
            "provider": "Real Python",
            "difficulty": 1,
            "est_hours": 12.0,
            "tags": "python, backend, syntax, programming, idioms"
        },

        # SQL (3 Real Resources)
        {
            "title": "SQLBolt: Interactive Lessons & Query Exercises",
            "url": "https://sqlbolt.com/",
            "skill": "SQL",
            "provider": "SQLBolt",
            "difficulty": 1,
            "est_hours": 10.0,
            "tags": "sql, database, queries, joins, fundamentals"
        },
        {
            "title": "Mode Analytics SQL Tutorial for Advanced Data Analysis",
            "url": "https://mode.com/sql-tutorial/",
            "skill": "SQL",
            "provider": "Mode",
            "difficulty": 2,
            "est_hours": 15.0,
            "tags": "sql, database, analytics, aggregation, subqueries, window-functions"
        },
        {
            "title": "W3Schools SQL Tutorial, Database Architecture & Exercises",
            "url": "https://www.w3schools.com/sql/",
            "skill": "SQL",
            "provider": "W3Schools",
            "difficulty": 1,
            "est_hours": 8.0,
            "tags": "sql, database, crud, tables, syntax, indexing"
        },

        # HTML (3 Real Resources)
        {
            "title": "MDN Web Docs: Structuring the Web with HTML",
            "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
            "skill": "HTML",
            "provider": "MDN Web Docs",
            "difficulty": 1,
            "est_hours": 12.0,
            "tags": "html, frontend, semantics, accessibility, web-standards"
        },
        {
            "title": "freeCodeCamp Responsive Web Design Certification",
            "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
            "skill": "HTML",
            "provider": "freeCodeCamp",
            "difficulty": 1,
            "est_hours": 25.0,
            "tags": "html, frontend, responsive, layout, forms, accessibility"
        },
        {
            "title": "W3Schools HTML5 Comprehensive Guide & Reference",
            "url": "https://www.w3schools.com/html/",
            "skill": "HTML",
            "provider": "W3Schools",
            "difficulty": 1,
            "est_hours": 8.0,
            "tags": "html, frontend, tags, web, elements, multimedia"
        },

        # JavaScript (3 Real Resources)
        {
            "title": "freeCodeCamp JavaScript Algorithms & Data Structures",
            "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
            "skill": "JavaScript",
            "provider": "freeCodeCamp",
            "difficulty": 1,
            "est_hours": 30.0,
            "tags": "javascript, frontend, algorithms, es6, fundamentals"
        },
        {
            "title": "MDN JavaScript Guide: Intermediate & Asynchronous Web APIs",
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
            "skill": "JavaScript",
            "provider": "MDN Web Docs",
            "difficulty": 2,
            "est_hours": 20.0,
            "tags": "javascript, frontend, async, dom, promises, closures"
        },
        {
            "title": "The Odin Project: Full Stack JavaScript Curriculum",
            "url": "https://www.theodinproject.com/paths/full-stack-javascript",
            "skill": "JavaScript",
            "provider": "The Odin Project",
            "difficulty": 2,
            "est_hours": 40.0,
            "tags": "javascript, frontend, web, project-based, dom, npm"
        },

        # React (3 Real Resources)
        {
            "title": "Official React Documentation: Learn React (Components & State)",
            "url": "https://react.dev/learn",
            "skill": "React",
            "provider": "React Core Team",
            "difficulty": 1,
            "est_hours": 25.0,
            "tags": "react, frontend, components, state, hooks, fundamentals"
        },
        {
            "title": "freeCodeCamp Front End Development Libraries (React & Redux)",
            "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/",
            "skill": "React",
            "provider": "freeCodeCamp",
            "difficulty": 2,
            "est_hours": 30.0,
            "tags": "react, frontend, redux, libraries, components, state-management"
        },
        {
            "title": "The Odin Project: Complete React Course & Routing",
            "url": "https://www.theodinproject.com/lessons/node-path-react-new-getting-started-with-react",
            "skill": "React",
            "provider": "The Odin Project",
            "difficulty": 2,
            "est_hours": 25.0,
            "tags": "react, frontend, hooks, routing, web, component-lifecycle"
        },

        # Node.js (3 Real Resources)
        {
            "title": "Official Node.js Guides: Architecture & Core Modules",
            "url": "https://nodejs.org/en/learn",
            "skill": "Node.js",
            "provider": "Node.js Foundation",
            "difficulty": 1,
            "est_hours": 20.0,
            "tags": "nodejs, backend, runtime, modules, asynchronous, event-loop"
        },
        {
            "title": "freeCodeCamp Back End Development & REST APIs with Express",
            "url": "https://www.freecodecamp.org/learn/back-end-development-and-apis/",
            "skill": "Node.js",
            "provider": "freeCodeCamp",
            "difficulty": 2,
            "est_hours": 35.0,
            "tags": "nodejs, express, backend, rest, api, mongodb, middleware"
        },
        {
            "title": "The Odin Project: Node.js, Express & Database Integration",
            "url": "https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs",
            "skill": "Node.js",
            "provider": "The Odin Project",
            "difficulty": 2,
            "est_hours": 30.0,
            "tags": "nodejs, backend, express, relational-db, authentication, security"
        },
    ]

    resource_records = {}
    for r_item in resources_data:
        skill = skill_records[r_item["skill"]]
        existing_res = db.query(LearningResource).filter_by(title=r_item["title"]).first()
        if not existing_res:
            existing_res = LearningResource(
                title=r_item["title"],
                url=r_item["url"],
                provider=r_item["provider"],
                skill_id=skill.id,
                difficulty=r_item["difficulty"],
                est_hours=r_item["est_hours"],
                tags=r_item["tags"]
            )
            db.add(existing_res)
            db.flush()
        resource_records[r_item["title"]] = existing_res

    # 5. Create Sample Learner Profile matching sample case
    demo_email = "demo@example.com"
    demo_user = db.query(User).filter_by(email=demo_email).first()
    if not demo_user:
        demo_user = User(
            name="Demo Learner",
            email=demo_email,
            password_hash=hash_password("DemoPass123!")
        )
        db.add(demo_user)
        db.flush()

        # Set user goal to Full Stack Developer
        user_goal = UserCareerGoal(
            user_id=demo_user.id,
            role_id=role.id,
            active=True
        )
        db.add(user_goal)

        # Set default user settings
        demo_settings = UserSettings(
            user_id=demo_user.id,
            theme="dark",
            llm_provider="gemini",
            llm_model="gemini-1.5-flash",
            llm_api_key_encrypted=None
        )
        db.add(demo_settings)

        # Populate user skills matching sample scenario
        sample_skills_init = {
            "Python": (80.0, 70.0, 60.0),
            "SQL": (60.0, 60.0, 60.0),
            "HTML": (50.0, 50.0, 50.0),
            "JavaScript": (0.0, 0.0, 0.0),
            "React": (0.0, 0.0, 0.0),
            "Node.js": (0.0, 0.0, 0.0),
        }

        for skill_name, (a_s, q_s, e_s) in sample_skills_init.items():
            skill = skill_records[skill_name]
            p_s = calculate_skill_proficiency(a_s, q_s, e_s)
            u_skill = UserSkill(
                user_id=demo_user.id,
                skill_id=skill.id,
                A_s=a_s,
                Q_s=q_s,
                E_s=e_s,
                P_s=p_s
            )
            db.add(u_skill)

            # Initialize BKT state (Python has 0.85 mastery for initial certificate!)
            p_mastery = 0.85 if skill_name == "Python" else (0.30 if p_s == 0.0 else round(min(0.75, p_s / 100.0), 2))
            bkt = BKTState(
                user_id=demo_user.id,
                skill_id=skill.id,
                p_mastery=p_mastery,
                p_T=0.15,
                p_G=0.20,
                p_S=0.10,
                attempts_count=2 if skill_name == "Python" else (1 if p_s > 0 else 0)
            )
            db.add(bkt)

        # Seed initial Recommendations immediately so Recommendations is never empty
        initial_recs = [
            ("freeCodeCamp JavaScript Algorithms & Data Structures", "JavaScript", 4.00),
            ("Official React Documentation: Learn React (Components & State)", "React", 3.00),
            ("Official Node.js Guides: Architecture & Core Modules", "Node.js", 2.10),
            ("MDN JavaScript Guide: Intermediate & Asynchronous Web APIs", "JavaScript", 2.667),
            ("freeCodeCamp Front End Development Libraries (React & Redux)", "React", 2.50),
            ("freeCodeCamp Back End Development & REST APIs with Express", "Node.js", 1.80),
        ]
        for title, s_name, prio in initial_recs:
            if title in resource_records:
                r_obj = resource_records[title]
                rec = Recommendation(
                    user_id=demo_user.id,
                    skill_id=r_obj.skill_id,
                    resource_id=r_obj.id,
                    priority_score=prio,
                    status="active"
                )
                db.add(rec)

        # Seed initial Certificate for Python (P(Ln) = 0.85 >= 0.80) so Certificates view has rows
        py_skill = skill_records["Python"]
        code, pdf_path = generate_certificate_pdf(
            learner_name=demo_user.name,
            skill_name="Python",
            role_title="Full Stack Developer",
            issued_at=datetime.now(timezone.utc)
        )
        cert = Certificate(
            user_id=demo_user.id,
            skill_id=py_skill.id,
            issued_at=datetime.now(timezone.utc),
            verification_code=code,
            pdf_path=pdf_path
        )
        db.add(cert)

    db.commit()
