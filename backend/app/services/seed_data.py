"""Reference dataset seeded into PostgreSQL on first start.

Everything the career intelligence features rely on lives here so that PRS and
skill-gap results are database backed and differ per student and per target role:

* `ROLE_CATALOG`        -> `role_profiles` + `role_skills`
* `LEARNING_RESOURCES`  -> `learning_resources`
* `INTERVIEW_QUESTIONS` -> `interview_questions`

Each role skill is (skill_name, priority, target_proficiency). Priority decides how
much a missing skill costs the skills component of the readiness score.
"""

ROLE_CATALOG: dict[str, dict] = {
    "Full-Stack Developer": {
        "category": "Software Engineering",
        "description": "Builds and ships both client and server sides of a web product.",
        "skills": [
            ("React", "high", "advanced"),
            ("TypeScript", "high", "intermediate"),
            ("Node.js", "high", "intermediate"),
            ("JavaScript", "high", "advanced"),
            ("REST API", "high", "intermediate"),
            ("PostgreSQL", "medium", "intermediate"),
            ("HTML/CSS", "medium", "intermediate"),
            ("Git", "medium", "intermediate"),
            ("Docker", "medium", "beginner"),
            ("Testing", "medium", "beginner"),
        ],
    },
    "Backend Developer": {
        "category": "Software Engineering",
        "description": "Designs services, data models and APIs that other systems depend on.",
        "skills": [
            ("Python", "high", "advanced"),
            ("FastAPI", "high", "intermediate"),
            ("PostgreSQL", "high", "intermediate"),
            ("REST API", "high", "advanced"),
            ("SQLAlchemy", "medium", "intermediate"),
            ("Data Structures and Algorithms", "high", "intermediate"),
            ("JWT Authentication", "medium", "intermediate"),
            ("Docker", "medium", "beginner"),
            ("Testing", "medium", "beginner"),
            ("Redis", "low", "beginner"),
        ],
    },
    "Frontend Developer": {
        "category": "Software Engineering",
        "description": "Owns the user interface, accessibility and front-end performance.",
        "skills": [
            ("JavaScript", "high", "advanced"),
            ("React", "high", "advanced"),
            ("TypeScript", "high", "intermediate"),
            ("HTML/CSS", "high", "advanced"),
            ("REST API", "medium", "intermediate"),
            ("Git", "medium", "intermediate"),
            ("Accessibility", "medium", "beginner"),
            ("Testing", "medium", "beginner"),
            ("Web Performance", "low", "beginner"),
        ],
    },
    "AI / ML Engineer": {
        "category": "Data and AI",
        "description": "Builds, evaluates and deploys machine learning models.",
        "skills": [
            ("Python", "high", "advanced"),
            ("Machine Learning", "high", "advanced"),
            ("Statistics", "high", "intermediate"),
            ("NumPy", "high", "intermediate"),
            ("Pandas", "high", "intermediate"),
            ("Scikit-learn", "high", "intermediate"),
            ("Deep Learning", "medium", "intermediate"),
            ("SQL", "medium", "intermediate"),
            ("Data Visualization", "medium", "beginner"),
            ("MLOps", "low", "beginner"),
        ],
    },
    "Data Analyst": {
        "category": "Data and AI",
        "description": "Turns raw data into decisions with reporting and visualisation.",
        "skills": [
            ("SQL", "high", "advanced"),
            ("Excel", "high", "intermediate"),
            ("Power BI", "high", "intermediate"),
            ("Python", "high", "intermediate"),
            ("Statistics", "high", "intermediate"),
            ("Pandas", "medium", "intermediate"),
            ("Data Visualization", "high", "intermediate"),
            ("Data Cleaning", "medium", "intermediate"),
        ],
    },
    "Software Engineer": {
        "category": "Software Engineering",
        "description": "General software engineering role focused on algorithms and clean design.",
        "skills": [
            ("Data Structures and Algorithms", "high", "advanced"),
            ("Java", "high", "intermediate"),
            ("Object Oriented Programming", "high", "intermediate"),
            ("SQL", "high", "intermediate"),
            ("Git", "high", "intermediate"),
            ("REST API", "medium", "intermediate"),
            ("Testing", "medium", "intermediate"),
            ("Operating Systems", "medium", "intermediate"),
            ("System Design", "medium", "beginner"),
        ],
    },
    "DevOps Engineer": {
        "category": "Infrastructure",
        "description": "Automates build, release and operations of production systems.",
        "skills": [
            ("Linux", "high", "intermediate"),
            ("Docker", "high", "advanced"),
            ("Kubernetes", "high", "intermediate"),
            ("CI/CD", "high", "intermediate"),
            ("AWS", "high", "intermediate"),
            ("Git", "high", "intermediate"),
            ("Python", "medium", "intermediate"),
            ("Terraform", "medium", "beginner"),
            ("Monitoring", "medium", "beginner"),
        ],
    },
    "Cybersecurity Analyst": {
        "category": "Security",
        "description": "Monitors, assesses and hardens systems against security threats.",
        "skills": [
            ("Networking", "high", "intermediate"),
            ("Linux", "high", "intermediate"),
            ("Python", "high", "intermediate"),
            ("Network Security", "medium", "intermediate"),
            ("Vulnerability Assessment", "medium", "intermediate"),
            ("SIEM", "medium", "beginner"),
            ("Cryptography", "medium", "beginner"),
            ("Incident Response", "medium", "beginner"),
        ],
    },
    "Mobile Application Developer": {
        "category": "Software Engineering",
        "description": "Builds cross-platform mobile applications and ships them to stores.",
        "skills": [
            ("Flutter", "high", "intermediate"),
            ("Dart", "high", "intermediate"),
            ("REST API", "high", "intermediate"),
            ("State Management", "medium", "intermediate"),
            ("Firebase", "medium", "intermediate"),
            ("Git", "medium", "intermediate"),
            ("UI Design", "medium", "beginner"),
            ("Testing", "medium", "beginner"),
        ],
    },
}

# (skill_name, title, provider, url, resource_type, difficulty, estimated_hours)
LEARNING_RESOURCES: list[tuple[str, str, str, str, str, str, float]] = [
    # Web and front-end
    ("HTML/CSS", "Responsive Web Design Certification", "freeCodeCamp", "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "course", "beginner", 30),
    ("JavaScript", "JavaScript Guide", "MDN Web Docs", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "docs", "beginner", 20),
    ("JavaScript", "JavaScript Algorithms and Data Structures", "freeCodeCamp", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "course", "intermediate", 40),
    ("TypeScript", "TypeScript Handbook", "Microsoft", "https://www.typescriptlang.org/docs/handbook/intro.html", "docs", "intermediate", 12),
    ("React", "Learn React", "React Documentation", "https://react.dev/learn", "docs", "intermediate", 18),
    ("React", "Front End Development Libraries", "freeCodeCamp", "https://www.freecodecamp.org/learn/front-end-development-libraries/", "course", "intermediate", 35),
    ("Web Performance", "Web Performance Fundamentals", "web.dev", "https://web.dev/learn/performance/", "course", "intermediate", 6),
    ("Accessibility", "Learn Accessibility", "web.dev", "https://web.dev/learn/accessibility/", "course", "beginner", 5),
    ("UI Design", "Figma Learn Design", "Figma", "https://help.figma.com/hc/en-us/categories/360002051613", "docs", "beginner", 8),
    # Back-end and APIs
    ("Python", "Python Tutorial", "Python Software Foundation", "https://docs.python.org/3/tutorial/", "docs", "beginner", 25),
    ("Python", "Scientific Computing with Python", "freeCodeCamp", "https://www.freecodecamp.org/learn/scientific-computing-with-python/", "course", "intermediate", 40),
    ("FastAPI", "FastAPI Tutorial", "FastAPI", "https://fastapi.tiangolo.com/tutorial/", "docs", "intermediate", 10),
    ("REST API", "HTTP and REST basics", "MDN Web Docs", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "docs", "beginner", 8),
    ("SQLAlchemy", "SQLAlchemy Unified Tutorial", "SQLAlchemy", "https://docs.sqlalchemy.org/en/20/tutorial/", "docs", "intermediate", 12),
    ("JWT Authentication", "Introduction to JSON Web Tokens", "jwt.io", "https://jwt.io/introduction", "docs", "intermediate", 4),
    ("Redis", "Redis University: Redis for Developers", "Redis", "https://university.redis.io/", "course", "intermediate", 10),
    # Data and databases
    ("SQL", "SQL Tutorial", "W3Schools", "https://www.w3schools.com/sql/", "course", "beginner", 12),
    ("SQL", "SQL for Data Science", "Coursera", "https://www.coursera.org/learn/sql-for-data-science", "course", "intermediate", 20),
    ("PostgreSQL", "PostgreSQL Tutorial", "PostgreSQL Global Development Group", "https://www.postgresql.org/docs/current/tutorial.html", "docs", "intermediate", 14),
    ("Excel", "Excel Basics", "Microsoft Learn", "https://support.microsoft.com/en-us/excel", "docs", "beginner", 10),
    ("Power BI", "Power BI Learning Paths", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "course", "intermediate", 18),
    ("Data Cleaning", "Cleaning Data in Python", "DataCamp", "https://www.datacamp.com/courses/cleaning-data-in-python", "course", "intermediate", 8),
    ("Data Visualization", "Data Visualization with Python", "Coursera", "https://www.coursera.org/learn/python-for-data-visualization", "course", "intermediate", 18),
    # Machine learning
    ("NumPy", "NumPy Absolute Beginner's Guide", "NumPy", "https://numpy.org/doc/stable/user/absolute_beginners.html", "docs", "beginner", 6),
    ("Pandas", "10 Minutes to pandas", "pandas", "https://pandas.pydata.org/docs/user_guide/10min.html", "docs", "intermediate", 8),
    ("Scikit-learn", "scikit-learn User Guide", "scikit-learn", "https://scikit-learn.org/stable/user_guide.html", "docs", "intermediate", 15),
    ("Machine Learning", "Machine Learning Specialization", "Coursera", "https://www.coursera.org/specializations/machine-learning-introduction", "course", "intermediate", 60),
    ("Machine Learning", "Kaggle Intro to Machine Learning", "Kaggle", "https://www.kaggle.com/learn/intro-to-machine-learning", "course", "beginner", 8),
    ("Deep Learning", "Deep Learning Specialization", "Coursera", "https://www.coursera.org/specializations/deep-learning", "course", "advanced", 70),
    ("Statistics", "Statistics and Probability", "Khan Academy", "https://www.khanacademy.org/math/statistics-probability", "course", "intermediate", 25),
    ("MLOps", "Machine Learning Engineering for Production", "Coursera", "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops", "course", "advanced", 45),
    # Engineering fundamentals and infrastructure
    ("Data Structures and Algorithms", "Algorithms, Part I", "Coursera", "https://www.coursera.org/learn/algorithms-part1", "course", "intermediate", 40),
    ("Data Structures and Algorithms", "NeetCode Roadmap Practice", "NeetCode", "https://neetcode.io/roadmap", "practice", "intermediate", 60),
    ("Java", "Java Tutorials", "Oracle", "https://docs.oracle.com/javase/tutorial/", "docs", "intermediate", 30),
    ("Object Oriented Programming", "Object Oriented Programming in Python", "Real Python", "https://realpython.com/python3-object-oriented-programming/", "course", "intermediate", 10),
    ("Operating Systems", "Operating Systems: Three Easy Pieces", "Remzi and Andrea Arpaci-Dusseau", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "docs", "advanced", 40),
    ("System Design", "System Design Primer", "GitHub", "https://github.com/donnemartin/system-design-primer", "docs", "advanced", 35),
    ("Testing", "Test Automation and Unit Testing in Python", "Real Python", "https://realpython.com/python-testing/", "course", "beginner", 10),
    ("Git", "Git Handbook", "GitHub Docs", "https://docs.github.com/en/get-started/using-git/about-git", "docs", "beginner", 6),
    ("Docker", "Docker Get Started", "Docker", "https://docs.docker.com/get-started/", "docs", "beginner", 8),
    ("Kubernetes", "Kubernetes Basics", "Kubernetes", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "docs", "intermediate", 14),
    ("CI/CD", "GitHub Actions Documentation", "GitHub", "https://docs.github.com/en/actions", "docs", "intermediate", 10),
    ("AWS", "AWS Cloud Practitioner Essentials", "AWS Skill Builder", "https://explore.skillbuilder.aws/", "course", "intermediate", 20),
    ("Terraform", "Terraform Tutorials", "HashiCorp", "https://developer.hashicorp.com/terraform/tutorials", "course", "intermediate", 12),
    ("Monitoring", "Prometheus Getting Started", "Prometheus", "https://prometheus.io/docs/prometheus/latest/getting_started/", "docs", "intermediate", 8),
    ("Linux", "Linux Journey", "Linux Journey", "https://linuxjourney.com/", "course", "beginner", 16),
    ("Networking", "Computer Networking: A Top-Down Approach (companion)", "Kurose and Ross", "https://gaia.cs.umass.edu/kurose_ross/index.php", "docs", "intermediate", 30),
    ("Network Security", "Network Security Basics", "Cisco Networking Academy", "https://www.netacad.com/courses/cybersecurity", "course", "intermediate", 20),
    ("Vulnerability Assessment", "Nmap and Vulnerability Scanning basics", "Nmap", "https://nmap.org/book/man.html", "docs", "intermediate", 10),
    ("SIEM", "Splunk Fundamentals", "Splunk", "https://www.splunk.com/en_us/training/free-courses/overview.html", "course", "beginner", 12),
    ("Cryptography", "Cryptography I", "Coursera", "https://www.coursera.org/learn/crypto", "course", "advanced", 30),
    ("Incident Response", "Incident Response Lifecycle", "NIST", "https://csrc.nist.gov/pubs/sp/800/61/r2/final", "docs", "intermediate", 8),
    # Mobile
    ("Flutter", "Flutter Codelabs", "Google", "https://docs.flutter.dev/get-started/codelab", "course", "intermediate", 20),
    ("Dart", "Dart Language Tour", "Dart", "https://dart.dev/language", "docs", "beginner", 10),
    ("State Management", "Flutter State Management Guide", "Flutter Documentation", "https://docs.flutter.dev/data-and-backend/state-mgmt/intro", "docs", "intermediate", 8),
    ("Firebase", "Firebase Fundamentals", "Google", "https://firebase.google.com/docs/guides", "docs", "intermediate", 12),
]

# (category, target_role or None for all roles, difficulty, question, guidance, skill_tags)
INTERVIEW_QUESTIONS: list[tuple[str, str | None, str, str, str, list[str]]] = [
    # General technical
    ("technical", None, "beginner", "Walk me through how you would debug a feature that works locally but fails in production.", "Describe a structured approach: reproduce, compare environments, read logs, isolate the variable, verify the fix, add a guard test.", ["Debugging"]),
    ("technical", None, "intermediate", "Explain the difference between authentication and authorisation in a web application.", "Authentication proves identity (JWT, session). Authorisation decides what the identity may do (roles, permissions). Mention enforcing both on the server.", ["JWT Authentication", "REST API"]),
    ("technical", None, "intermediate", "When would you add an index to a database table, and what is the trade-off?", "Indexes speed up reads on filtered or joined columns but cost write time and storage. Mention composite indexes and using query plans.", ["SQL", "PostgreSQL"]),
    ("technical", None, "intermediate", "How do you decide between SQL and NoSQL for a new service?", "Base it on data shape, consistency needs, query patterns, scaling profile. Give one concrete example of each.", ["SQL"]),
    ("technical", None, "advanced", "Describe how you would design a rate limiter for a public API.", "Cover the algorithm (token bucket, sliding window), storage (Redis), per-key scoping, response codes and observability.", ["System Design", "Redis"]),
    # General behavioural
    ("behavioral", None, "beginner", "Tell me about a project you are proud of and your specific contribution.", "Use a clear structure: context, problem, your actions, measurable result, what you learned.", []),
    ("behavioral", None, "beginner", "Describe a time you received difficult feedback and how you responded.", "Show ownership, the concrete change you made, and the outcome.", []),
    ("behavioral", None, "intermediate", "Tell me about a conflict inside a team project and how it was resolved.", "Focus on listening, objective evidence, and the decision process rather than blame.", []),
    ("behavioral", None, "intermediate", "Describe a deadline you were at risk of missing and what you did.", "Explain prioritisation, early communication, scope negotiation and the final outcome.", []),
    ("behavioral", None, "intermediate", "Why did you choose your target role, and where do you want to be in two years?", "Connect your skills and projects to the role, and describe a realistic growth plan.", []),
    # Role specific: Full-Stack Developer
    ("role_specific", "Full-Stack Developer", "intermediate", "How do you keep the front-end and back-end contracts in sync in a project you own?", "Mention shared type definitions or schemas, versioned API paths, automated tests and a review step.", ["React", "TypeScript", "REST API"]),
    ("role_specific", "Full-Stack Developer", "intermediate", "How would you optimise a page that loads slowly because of many API calls?", "Cover request batching, pagination, caching, server-side aggregation and measuring with browser performance tools.", ["React", "Web Performance", "REST API"]),
    ("role_specific", "Full-Stack Developer", "advanced", "Explain how you would secure a full-stack application end to end.", "Input validation, parameterised queries, password hashing, JWT expiry and refresh, server-side RBAC, CORS and secrets management.", ["JWT Authentication", "REST API"]),
    # Role specific: Backend Developer
    ("role_specific", "Backend Developer", "intermediate", "How do you structure a FastAPI application that will keep growing?", "Layered structure: routers, schemas, models, services, dependency-injected sessions, shared exception handling.", ["FastAPI", "Python"]),
    ("role_specific", "Backend Developer", "intermediate", "Your endpoint becomes slow after the data set grows. How do you investigate?", "Measure first, inspect the query plan, fix N+1 access, add indexes, paginate and cache where safe.", ["PostgreSQL", "SQLAlchemy"]),
    ("role_specific", "Backend Developer", "advanced", "Describe how you would migrate a schema in production without downtime.", "Expand and contract pattern, backward compatible columns, batched backfill, feature flags, reversible migrations.", ["PostgreSQL", "Docker"]),
    # Role specific: Frontend Developer
    ("role_specific", "Frontend Developer", "intermediate", "How do you manage state in a React application with server data?", "Separate server state (fetch layer or cache) from UI state, avoid duplicating derived data, keep fetching in one API module.", ["React", "JavaScript"]),
    ("role_specific", "Frontend Developer", "intermediate", "How do you make a complex form accessible and easy to use?", "Labels tied to inputs, keyboard order, visible validation messages, aria attributes, sensible error summaries.", ["HTML/CSS", "Accessibility"]),
    ("role_specific", "Frontend Developer", "advanced", "Describe a time you improved the rendering performance of a large list.", "Virtualisation or windowing, memoised components, stable keys, avoiding expensive work during render, measuring with the profiler.", ["React", "Web Performance"]),
    # Role specific: AI / ML Engineer
    ("role_specific", "AI / ML Engineer", "intermediate", "How do you know whether a model is actually good, beyond accuracy?", "Class balance, precision/recall or F1, confusion matrix, cross validation, held-out test set and monitoring for drift.", ["Machine Learning", "Statistics"]),
    ("role_specific", "AI / ML Engineer", "intermediate", "Walk me through preparing a messy dataset for training.", "Profiling, missing value strategy, encoding, scaling, leakage checks, train/validation split and documented transforms.", ["Pandas", "Data Cleaning"]),
    ("role_specific", "AI / ML Engineer", "advanced", "How would you deploy a model so predictions stay consistent with training?", "Serialise the pipeline including preprocessing, version the artifact, validate inputs, log predictions, monitor drift.", ["MLOps", "Scikit-learn"]),
    # Role specific: Data Analyst
    ("role_specific", "Data Analyst", "intermediate", "How do you validate a dashboard number that looks wrong to a stakeholder?", "Trace the metric definition, check joins and grain, re-run the query, compare with the source system, document the definition.", ["SQL", "Power BI"]),
    ("role_specific", "Data Analyst", "intermediate", "Explain how you would use a window function to rank records per group.", "PARTITION BY the group, ORDER BY the ranking column, then ROW_NUMBER or RANK; mention filtering in an outer query.", ["SQL"]),
    ("role_specific", "Data Analyst", "beginner", "How do you present an insight to a non-technical audience?", "Lead with the decision, one headline chart, plain language, caveats and a recommended next step.", ["Data Visualization"]),
    # Role specific: Software Engineer
    ("role_specific", "Software Engineer", "intermediate", "Explain how you would detect a cycle in a directed graph and its complexity.", "DFS colouring or topological sort (Kahn). Time O(V+E), space O(V) for the visited and recursion stack.", ["Data Structures and Algorithms"]),
    ("role_specific", "Software Engineer", "intermediate", "What is the difference between an abstract class and an interface, and when do you use each?", "Shared implementation versus pure contract, single versus multiple inheritance, design intent and testability.", ["Object Oriented Programming", "Java"]),
    ("role_specific", "Software Engineer", "advanced", "Design a service that assigns mentors to students at scale.", "Data model (mentor, student, assignment), constraints, matching rules, concurrency, pagination and reporting endpoints.", ["System Design", "SQL"]),
]





