import re
import spacy
# Load spaCy model lazily to avoid startup overhead if not immediately needed
nlp = None
def get_nlp():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            print("Downloading spacy model...")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
    return nlp
# --- Name extraction helpers ---
# Words/phrases that are NOT names (section headings, skills, titles, places)
_NOT_A_NAME = {                                                                        
    # Common resume section headings
    'summary', 'objective', 'experience', 'education', 'skills', 'projects',
    'certifications', 'achievements', 'references', 'contact', 'profile',
    'about', 'about me', 'work experience', 'professional experience',
    'technical skills', 'interests', 'hobbies', 'languages', 'awards',
    'curriculum vitae', 'resume', 'cv',
    # Common tech terms that appear as single/short lines in PDF extracts
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c',
    'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
    'html', 'css', 'sql', 'git', 'docker', 'aws', 'algorithms',
    'data structures', 'machine learning', 'deep learning',
    'full stack', 'frontend', 'backend', 'software engineer',
    'software developer', 'web developer', 'data scientist',
    'devops engineer', 'mobile developer',
    # Indian states and major cities (common false positives)
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
    'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
    'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya',
    'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim',
    'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand',
    'west bengal', 'delhi', 'new delhi', 'mumbai', 'bangalore', 'bengaluru',
    'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad', 'jaipur',
    'lucknow', 'kanpur', 'nagpur', 'indore', 'bhopal', 'visakhapatnam',
    'vijayawada', 'guntur', 'tirupati', 'warangal', 'noida', 'gurgaon',
    'gurugram', 'chandigarh', 'coimbatore', 'thiruvananthapuram', 'kochi',
    'mysore', 'mysuru', 'mangalore', 'mangaluru',
}
def _looks_like_a_name(line: str) -> bool:
    """Return True if a line looks like a person's name."""
    line = line.strip()
    if not line:
        return False
    # Must be short (names are typically < 50 chars)
    if len(line) > 50:
        return False
    # Must have 2-4 words (single words are usually headings/skills)
    words = line.split()
    if len(words) < 2 or len(words) > 4:
        return False
    # Must be mostly alphabetic (no digits, no special chars like @, |, -, :)
    if re.search(r'[\d@|:\-/\\#\(\)]', line):
        return False
    # Must not contain common email/phone patterns
    if '@' in line or re.search(r'\d{3}', line):
        return False
    # Check against the blocklist
    if line.lower().strip() in _NOT_A_NAME:
        return False
    # Each word should start with an uppercase letter (title-case names)
    # Allow for initials like "K." or connectors like "van", "de"
    connectors = {'van', 'de', 'von', 'bin', 'al', 'el', 'la', 'le', 'di'}
    for word in words:
        cleaned = word.rstrip('.')
        if cleaned.lower() in connectors:
            continue
        if not cleaned[0].isupper():
            return False
    return True


def extract_name(text: str) -> str:
    """Extract candidate name from resume text.

    Strategy (in priority order):
    1. Check the first 10 non-empty lines for one that looks like a human name.
    2. Use spaCy PERSON entities from the header, filtered against a blocklist.
    3. Fall back to filename (handled by the caller in main.py).
    """
    # --- Approach 1: Heuristic scan of the first few lines ---
    lines_checked = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        lines_checked += 1
        if lines_checked > 10:
            break
        if _looks_like_a_name(line):
            return line

    # --- Approach 2: spaCy NER with blocklist filtering ---
    header_text = text[:800]
    header_doc = get_nlp()(header_text)

    # Collect GPE/LOC/ORG entities to blocklist from full text
    full_doc = get_nlp()(text)
    blocklist = set()
    for ent in full_doc.ents:
        if ent.label_ in ("GPE", "LOC", "ORG", "FAC", "NORP", "EVENT"):
            blocklist.add(ent.text.strip().lower())
    # Also add our static blocklist
    blocklist.update(_NOT_A_NAME)

    for ent in header_doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            if name.lower() not in blocklist and len(name.split()) <= 4:
                return name

    return ""
# --- Skills extraction helpers ---
def extract_skills(text: str) -> list[str]:
    """Extract assumed skills from text using simple NLP rules (NER and noun chunks).
    In a true production app, we would use a comprehensive skills dictionary/taxonomy.
    """
    # Technical / programming skills only
    common_skills = {
        # Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
        'swift', 'kotlin', 'scala', 'r', 'php', 'perl', 'lua', 'dart', 'matlab',
        # Frontend frameworks
        'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt',
        # Backend frameworks
        'node.js', 'node', 'django', 'flask', 'spring', 'fastapi', 'express', 'rails',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
        'ansible', 'ci/cd', 'linux', 'nginx',
        # Version control
        'git', 'github', 'gitlab', 'bitbucket',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        'sqlite', 'dynamodb', 'firebase',
        # AI/ML/Data
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'data science',
        'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'keras', 'opencv',
        # Web technologies
        'html', 'css', 'sass', 'tailwind', 'bootstrap', 'graphql', 'rest api',
        'webpack', 'vite',
        # Mobile
        'react native', 'flutter', 'android', 'ios',
    }
    
    found_skills = set()
    text_lower = text.lower()
    
    # 1. Dictionary lookup (simple matching)
    for skill in common_skills:
        if skill in text_lower:
            found_skills.add(skill.title())
            
    # 2. NLP-based extraction (optional additional logic, e.g. grabbing noun chunks)
    # Using spacy to find other potential skills (simplified for this scope)
    doc = get_nlp()(text)
    
    # Extract organizations or tech entities if they match patterns
    # (Just an example of how NER might be utilized)
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT']:
            # Highly prone to false positives, normally requires a specialized NER model
            pass
    return sorted(list(found_skills))
def clean_text(text: str) -> str:
    """Clean and preprocess text."""
    doc = get_nlp()(text)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and not token.is_space]
    return " ".join(tokens)