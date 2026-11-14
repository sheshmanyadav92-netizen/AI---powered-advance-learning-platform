from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import Base, SessionLocal, engine
from backend.models import Assessment, Learner, LearnerSkill, Resource, Role, RoleSkill
from backend.services.demo_data import seed_demo_activity

ROLE_DATA = [
    (
        "Full Stack Developer",
        "Build and maintain complete web applications across frontend and backend.",
        [
            ("JavaScript", 75, 1.4), ("React", 70, 1.2), ("Node.js", 70, 1.2),
            ("Express", 65, 0.8),
            ("HTML", 70, 0.8), ("CSS", 70, 0.8), ("Python", 60, 0.8),
            ("SQL", 60, 0.8), ("Git", 65, 0.8), ("REST APIs", 65, 1.0),
            ("Testing", 60, 0.7),
        ],
    ),
    (
        "Data Analyst",
        "Turn structured data into clear, actionable business insights.",
        [
            ("SQL", 75, 1.4), ("Python", 65, 1.0), ("Statistics", 65, 1.0),
            ("Excel", 65, 0.8), ("Data Visualization", 65, 1.0),
            ("Tableau", 60, 0.8), ("Communication", 60, 0.7),
        ],
    ),
    (
        "Data Scientist",
        "Use statistics, programming, and machine learning to solve data problems.",
        [
            ("Python", 80, 1.3), ("Statistics", 75, 1.2), ("SQL", 65, 0.8),
            ("Machine Learning", 70, 1.3), ("Data Visualization", 65, 0.8),
            ("Pandas", 70, 1.0), ("Experiment Design", 60, 0.8),
        ],
    ),
    (
        "ML Engineer",
        "Build, deploy, and maintain production machine learning systems.",
        [
            ("Python", 80, 1.2), ("Machine Learning", 75, 1.3), ("SQL", 60, 0.7),
            ("Statistics", 65, 0.8), ("Docker", 65, 0.8), ("Cloud", 65, 0.9),
            ("MLOps", 65, 1.0), ("Git", 65, 0.6),
        ],
    ),
    (
        "DevOps Engineer",
        "Automate software delivery and operate reliable infrastructure.",
        [
            ("Linux", 75, 1.1), ("Docker", 75, 1.1), ("Kubernetes", 65, 1.0),
            ("CI/CD", 70, 1.1), ("Cloud", 70, 1.1), ("Git", 70, 0.8),
            ("Networking", 65, 0.8), ("Python", 60, 0.7),
        ],
    ),
    (
        "UI/UX Designer",
        "Research user needs and design usable, accessible digital experiences.",
        [
            ("Figma", 75, 1.2), ("UX Research", 70, 1.1), ("Prototyping", 70, 1.0),
            ("Visual Design", 70, 1.0), ("Accessibility", 60, 0.8),
            ("Communication", 65, 0.8), ("HTML", 45, 0.4),
        ],
    ),
    (
        "Cybersecurity Analyst",
        "Identify, investigate, and help mitigate security risks.",
        [
            ("Networking", 75, 1.1), ("Linux", 70, 0.9), ("Security Fundamentals", 75, 1.2),
            ("Python", 60, 0.7), ("Incident Response", 65, 1.0),
            ("SIEM", 65, 1.0), ("Risk Assessment", 60, 0.8),
        ],
    ),
    (
        "Cloud Engineer",
        "Design, deploy, and operate scalable cloud infrastructure.",
        [
            ("Cloud", 80, 1.3), ("Linux", 70, 0.9), ("Networking", 70, 0.9),
            ("Docker", 65, 0.8), ("Kubernetes", 65, 0.9), ("Terraform", 70, 1.0),
            ("Python", 60, 0.6), ("Security Fundamentals", 60, 0.7),
        ],
    ),
]

RESOURCE_SKILLS = {
    "Python": ("https://docs.python.org/3/tutorial/", "Python"),
    "SQL": ("https://sqlbolt.com/", "SQL"),
    "HTML": ("https://developer.mozilla.org/en-US/docs/Learn/HTML", "HTML"),
    "CSS": ("https://developer.mozilla.org/en-US/docs/Learn/CSS", "CSS"),
    "JavaScript": ("https://developer.mozilla.org/en-US/docs/Learn/JavaScript", "JavaScript"),
    "React": ("https://react.dev/learn", "React"),
    "Node.js": ("https://nodejs.org/en/learn", "Node.js"),
    "Express": ("https://expressjs.com/en/starter/installing.html", "Express"),
    "Git": ("https://git-scm.com/book/en/v2", "Git"),
    "REST APIs": ("https://developer.mozilla.org/en-US/docs/Glossary/REST", "REST"),
    "Testing": ("https://testing-library.com/docs/", "Testing"),
    "Statistics": ("https://www.khanacademy.org/math/statistics-probability", "Statistics"),
    "Excel": ("https://support.microsoft.com/excel", "Excel"),
    "Data Visualization": ("https://www.data-to-viz.com/", "Data visualization"),
    "Tableau": ("https://www.tableau.com/learn/training", "Tableau"),
    "Communication": ("https://www.coursera.org/learn/wharton-communication-skills", "Communication"),
    "Machine Learning": ("https://scikit-learn.org/stable/tutorial/index.html", "Machine learning"),
    "Pandas": ("https://pandas.pydata.org/docs/getting_started/intro_tutorials/", "Pandas"),
    "Experiment Design": ("https://www.khanacademy.org/math/statistics-probability", "Experiment design"),
    "Docker": ("https://docs.docker.com/get-started/", "Docker"),
    "Cloud": ("https://aws.amazon.com/training/", "Cloud"),
    "MLOps": ("https://ml-ops.org/", "MLOps"),
    "Linux": ("https://linuxjourney.com/", "Linux"),
    "Kubernetes": ("https://kubernetes.io/docs/tutorials/", "Kubernetes"),
    "CI/CD": ("https://docs.github.com/en/actions", "CI/CD"),
    "Networking": ("https://www.cloudflare.com/learning/network-layer/what-is-a-computer-network/", "Networking"),
    "Figma": ("https://help.figma.com/hc/en-us/categories/360002051613", "Figma"),
    "UX Research": ("https://www.nngroup.com/articles/which-ux-research-methods/", "UX research"),
    "Prototyping": ("https://www.figma.com/resource-library/prototyping/", "Prototyping"),
    "Visual Design": ("https://www.interaction-design.org/literature/topics/visual-design", "Visual design"),
    "Accessibility": ("https://www.w3.org/WAI/fundamentals/", "Accessibility"),
    "Security Fundamentals": ("https://owasp.org/www-project-top-ten/", "Security"),
    "Incident Response": ("https://www.cisa.gov/resources-tools/resources/incident-response", "Incident response"),
    "SIEM": ("https://learn.microsoft.com/en-us/training/azure/", "SIEM"),
    "Risk Assessment": ("https://www.nist.gov/cyberframework", "Risk assessment"),
    "Terraform": ("https://developer.hashicorp.com/terraform/tutorials", "Terraform"),
}

QUIZ_BANKS = {
    "Python": [
        ("Which keyword defines a function?", ["func", "def", "function", "lambda"], 1),
        ("Which type is mutable?", ["tuple", "str", "list", "int"], 2),
        ("What does len([2, 4, 6]) return?", ["2", "3", "6", "Error"], 1),
        ("Which statement handles an exception?", ["catch", "except", "rescue", "error"], 1),
        ("How do you import module math?", ["using math", "include math", "import math", "require math"], 2),
    ],
    "SQL": [
        ("Which clause filters rows?", ["ORDER BY", "WHERE", "GROUP BY", "JOIN"], 1),
        ("Which function counts rows?", ["SUM()", "TOTAL()", "COUNT()", "SIZE()"], 2),
        ("Which command reads records?", ["SELECT", "FETCH", "READ", "OPEN"], 0),
        ("Which join returns matching rows from both tables?", ["LEFT", "FULL", "INNER", "CROSS"], 2),
        ("Which clause sorts query results?", ["SORT", "ORDER BY", "ARRANGE", "GROUP"], 1),
    ],
    "HTML": [
        ("Which element is the main page heading?", ["<head>", "<h1>", "<title>", "<header-text>"], 1),
        ("Which attribute provides an image alternative?", ["title", "src", "alt", "label"], 2),
        ("Which element creates a link?", ["<a>", "<linkto>", "<href>", "<url>"], 0),
        ("Which element represents a paragraph?", ["<para>", "<p>", "<text>", "<body>"], 1),
        ("What does semantic HTML primarily improve?", ["File size", "Meaning and accessibility", "Network speed", "CSS syntax"], 1),
    ],
    "CSS": [
        ("Which property changes text color?", ["font-style", "color", "background", "text-weight"], 1),
        ("Which selector targets an element by id?", [".name", "#name", "*name", "@name"], 1),
        ("Which layout system is one-dimensional?", ["Grid", "Flexbox", "Float", "Table"], 1),
        ("Which property adds space inside a border?", ["margin", "padding", "gap", "outline"], 1),
        ("How is a class selector written?", ["#card", ".card", "card()", "@card"], 1),
    ],
    "JavaScript": [
        ("Which keyword declares a block-scoped variable?", ["var", "let", "define", "dim"], 1),
        ("Which operator checks strict equality?", ["=", "==", "===", "!="], 2),
        ("What does Array.map() return?", ["A new transformed array", "The first item", "A boolean", "Nothing"], 0),
        ("Which value represents absence of an assigned value?", ["NaN", "undefined", "false", "0"], 1),
        ("Which syntax creates an arrow function?", ["->", "=>", "::", "**"], 1),
    ],
    "React": [
        ("What is a React component?", ["Reusable UI unit", "Database table", "CSS selector", "HTTP method"], 0),
        ("Which hook stores local component state?", ["useFetch", "useState", "useRoute", "useClass"], 1),
        ("Why are keys used in rendered lists?", ["For CSS", "To identify items across renders", "For routing", "To encrypt data"], 1),
        ("Props are generally:", ["Inputs passed to a component", "Global CSS", "Database indexes", "DOM events only"], 0),
        ("What does JSX let you write?", ["HTML-like syntax in JavaScript", "SQL in CSS", "Python in HTML", "JSON schemas"], 0),
    ],
    "Node.js": [
        ("Node.js runs JavaScript primarily:", ["In a browser only", "On the server/runtime", "Inside CSS", "In SQL"], 1),
        ("Which file commonly declares npm scripts?", ["package.json", "node.lock", "app.html", "config.css"], 0),
        ("Which built-in module handles file paths?", ["url", "path", "file", "fs-path"], 1),
        ("What does npm install do?", ["Installs dependencies", "Starts a browser", "Compiles CSS only", "Creates a database"], 0),
        ("What does a non-blocking API support?", ["Concurrent I/O", "Synchronous waiting only", "Static HTML", "Type casting"], 0),
    ],
    "Git": [
        ("Which command creates a commit?", ["git save", "git commit", "git push", "git stage"], 1),
        ("Which command shows working tree changes?", ["git status", "git tree", "git diff --all", "git log"], 0),
        ("Which command downloads remote updates without merging?", ["git pull", "git fetch", "git clone", "git add"], 1),
        ("What is a branch used for?", ["Independent line of development", "A remote URL", "A file format", "A commit message"], 0),
        ("Which command stages a file?", ["git add", "git commit", "git init", "git reset"], 0),
    ],
    "REST APIs": [
        ("Which HTTP method usually retrieves a resource?", ["POST", "GET", "PATCH", "DELETE"], 1),
        ("Which status code means resource created?", ["200", "201", "301", "404"], 1),
        ("What does a stateless API mean?", ["Each request carries necessary context", "No data is stored anywhere", "Only one request is allowed", "Responses cannot be cached"], 0),
        ("Which format is commonly used for API data?", ["JSON", "BMP", "DOCX", "MP3"], 0),
        ("Which method usually updates a partial resource?", ["GET", "PATCH", "TRACE", "HEAD"], 1),
    ],
    "Machine Learning": [
        ("What is a training set used for?", ["Fitting model parameters", "Final deployment only", "Storing source code", "Formatting reports"], 0),
        ("What does overfitting mean?", ["Model memorizes training patterns and generalizes poorly", "Model is too small to learn", "Data has no labels", "Training stopped early"], 0),
        ("Which task predicts a category?", ["Regression", "Classification", "Clustering", "Compression"], 1),
        ("Why keep a test set?", ["Estimate performance on unseen data", "Increase training size", "Choose variable names", "Normalize source code"], 0),
        ("What is a feature?", ["An input variable used by a model", "A model score only", "A database index", "A deployment region"], 0),
    ],
}


def seed_roles(db: Session) -> None:
    for name, description, skills in ROLE_DATA:
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=description)
            db.add(role)
            db.flush()
        else:
            role.description = description
            for existing in list(role.skills):
                db.delete(existing)
        role.skills.extend(
            RoleSkill(skill=skill, required_level=level, weight=weight)
            for skill, level, weight in skills
        )


def seed_resources(db: Session) -> None:
    types = ["course", "tutorial", "doc", "exercise", "project"]
    difficulties = ["beginner", "intermediate", "advanced"]
    resource_number = 1
    for skill, (url, label) in RESOURCE_SKILLS.items():
        for index in range(3):
            title = f"{label} {difficulties[index]} {types[index + 1]} — SkillPath {resource_number:02d}"
            resource = db.scalar(select(Resource).where(Resource.title == title))
            values = {
                "type": types[index + 1],
                "skill": skill,
                "difficulty": difficulties[index],
                "duration_hours": float(2 + index * 2),
                "prerequisite_skills": [] if index == 0 else [skill],
                "url": url,
            }
            if resource is None:
                db.add(Resource(title=title, **values))
            else:
                for field, value in values.items():
                    setattr(resource, field, value)
            resource_number += 1
        exercise_title = f"{label} beginner practice exercise — SkillPath {resource_number:02d}"
        exercise_values = {
            "type": "exercise",
            "skill": skill,
            "difficulty": "beginner",
            "duration_hours": 1.0,
            "prerequisite_skills": [],
            "url": url,
        }
        exercise = db.scalar(select(Resource).where(Resource.title == exercise_title))
        if exercise is None:
            db.add(Resource(title=exercise_title, **exercise_values))
        else:
            for field, value in exercise_values.items():
                setattr(exercise, field, value)
        resource_number += 1
    capstone_title = "Full-stack capstone project — SkillPath"
    capstone_values = {
        "type": "project",
        "skill": "Full Stack Project",
        "difficulty": "intermediate",
        "duration_hours": 10.0,
        "prerequisite_skills": ["JavaScript", "React", "Node.js", "Express"],
        "url": "https://developer.mozilla.org/en-US/docs/Learn",
    }
    capstone = db.scalar(select(Resource).where(Resource.title == capstone_title))
    if capstone is None:
        db.add(Resource(title=capstone_title, **capstone_values))
    else:
        for field, value in capstone_values.items():
            setattr(capstone, field, value)


def seed_assessments(db: Session) -> None:
    for skill, questions in QUIZ_BANKS.items():
        title = f"{skill} fundamentals quiz"
        assessment = db.scalar(select(Assessment).where(Assessment.title == title))
        question_data = [
            {"question": question, "options": options, "answer_index": answer}
            for question, options, answer in questions
        ]
        if assessment is None:
            db.add(Assessment(title=title, skill=skill, questions=question_data))
        else:
            assessment.skill = skill
            assessment.questions = question_data


def seed_demo_learner(db: Session) -> None:
    learner = db.scalar(select(Learner).where(Learner.name == "Aarav"))
    if learner is None:
        learner = Learner(
            name="Aarav",
            education="Undergraduate",
            goal_role="Full Stack Developer",
            weekly_hours=8,
        )
        db.add(learner)
        db.flush()
    else:
        learner.education = "Undergraduate"
        learner.goal_role = "Full Stack Developer"
        learner.weekly_hours = 8
    for skill_name, level in [("Python", 70), ("SQL", 60), ("HTML", 40)]:
        skill = db.scalar(
            select(LearnerSkill).where(
                LearnerSkill.learner_id == learner.id, LearnerSkill.skill == skill_name
            )
        )
        if skill is None:
            db.add(
                LearnerSkill(
                    learner_id=learner.id,
                    skill=skill_name,
                    level=level,
                    source="self",
                )
            )
        else:
            skill.level = level
            skill.source = "self"


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        try:
            seed_roles(db)
            seed_resources(db)
            seed_assessments(db)
            seed_demo_learner(db)
            learner = db.scalar(select(Learner).where(Learner.name == "Aarav"))
            if learner is not None:
                seed_demo_activity(db, learner)
            db.commit()
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed()
    print(
        f"Seeded {len(ROLE_DATA)} roles, {len(RESOURCE_SKILLS) * 3} resources, "
        f"{len(QUIZ_BANKS)} quiz banks, and demo learner Aarav."
    )
