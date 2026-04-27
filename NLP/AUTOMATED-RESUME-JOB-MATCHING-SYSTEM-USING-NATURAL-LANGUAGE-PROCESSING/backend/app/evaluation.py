"""
Evaluation module for the Resume-Job Matching pipeline.
Computes confusion matrix, precision, recall, F1, accuracy,
semantic similarity statistics, skill extraction metrics, and more.
"""
import time
import os
import numpy as np
from typing import Optional
from .nlp.matcher import calculate_match, get_model
from .nlp.preprocessor import extract_skills, extract_name


# ─── Ground-truth test data ─────────────────────────────────────────────
# Each entry: (resume_text, job_description, ground_truth_label, expected_name, expected_skills_subset)
# label: 1 = relevant match, 0 = not relevant

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def _read_file(filename: str) -> str:
    path = os.path.join(SAMPLE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def _build_test_dataset():
    """Build a comprehensive test dataset with ground-truth labels."""
    job_desc = _read_file("sample_job.txt")
    good_resume = _read_file("sample_resume_good.txt")
    bad_resume = _read_file("sample_resume_bad.txt")

    # Synthetic test cases to expand evaluation coverage
    synthetic_resumes = [
        # (resume_text, label, name, key_skills)
        (
            "Ravi Kumar\nSenior Python Developer\nEmail: ravi@example.com\n\n"
            "Summary: 7 years of experience building REST APIs with FastAPI and Django. "
            "Expert in React.js frontend development, PostgreSQL databases, and AWS deployment.\n\n"
            "Skills: Python, FastAPI, Django, React, TypeScript, PostgreSQL, Docker, AWS, Git",
            1, "Ravi Kumar", {"python", "fastapi", "django", "react", "typescript", "postgresql", "docker", "aws", "git"}
        ),
        (
            "Priya Sharma\nData Entry Specialist\nEmail: priya@example.com\n\n"
            "Summary: 3 years of experience in data entry and administrative tasks. "
            "Proficient in Microsoft Office suite and basic spreadsheet operations.\n\n"
            "Skills: Microsoft Excel, Data Entry, Filing, Customer Service, Typing Speed 80 WPM",
            0, "Priya Sharma", set()
        ),
        (
            "Alex Chen\nDevOps Engineer\nEmail: alex@example.com\n\n"
            "Summary: 5 years of experience in cloud infrastructure and CI/CD pipelines. "
            "Expert in Docker, Kubernetes, AWS, and infrastructure as code with Terraform.\n\n"
            "Skills: Docker, Kubernetes, AWS, Terraform, Jenkins, Linux, Python, Git, CI/CD",
            1, "Alex Chen", {"docker", "kubernetes", "aws", "terraform", "jenkins", "linux", "python", "git"}
        ),
        (
            "Maria Garcia\nGraphic Designer\nEmail: maria@example.com\n\n"
            "Summary: Creative graphic designer with 4 years of experience in print and digital media. "
            "Specializes in Adobe Photoshop, Illustrator, and brand identity design.\n\n"
            "Skills: Adobe Photoshop, Illustrator, InDesign, Figma, Brand Design",
            0, "Maria Garcia", set()
        ),
        (
            "Sanjay Patel\nFull Stack Developer\nEmail: sanjay@example.com\n\n"
            "Summary: 4 years building web apps with React and Node.js. Experience with "
            "MongoDB, Express, and deploying to AWS using Docker containers.\n\n"
            "Skills: JavaScript, React, Node.js, Express, MongoDB, Docker, AWS, HTML, CSS, Git",
            1, "Sanjay Patel", {"javascript", "react", "node.js", "node", "express", "mongodb", "docker", "aws", "html", "css", "git"}
        ),
        (
            "Emily Brown\nHR Coordinator\nEmail: emily@example.com\n\n"
            "Summary: 5 years managing recruitment, onboarding, and employee relations. "
            "Skilled in ATS software, interview scheduling, and policy administration.\n\n"
            "Skills: Recruitment, Onboarding, Employee Relations, HRIS, Payroll",
            0, "Emily Brown", set()
        ),
        (
            "Vikram Singh\nBackend Developer\nEmail: vikram@example.com\n\n"
            "Summary: 3 years building scalable backend systems with Python and Flask. "
            "Experience with SQL databases, Redis caching, and RESTful API design.\n\n"
            "Skills: Python, Flask, SQL, MySQL, Redis, REST API, Git, Linux, Docker",
            1, "Vikram Singh", {"python", "flask", "sql", "mysql", "redis", "rest api", "git", "linux", "docker"}
        ),
        (
            "Lisa Wang\nAccountant\nEmail: lisa@example.com\n\n"
            "Summary: CPA with 6 years of experience in financial reporting, tax compliance, "
            "and audit preparation for mid-size companies.\n\n"
            "Skills: Financial Reporting, Tax Returns, QuickBooks, Excel, Auditing, GAAP",
            0, "Lisa Wang", set()
        ),
    ]

    test_data = []

    # Add real samples
    if good_resume and job_desc:
        test_data.append({
            "resume": good_resume,
            "job": job_desc,
            "label": 1,
            "expected_name": "John Doe",
            "expected_skills": {"python", "javascript", "typescript", "sql", "react", "fastapi", "django", "tailwind", "docker", "aws", "git", "postgresql"},
            "source": "sample_resume_good.txt"
        })

    if bad_resume and job_desc:
        test_data.append({
            "resume": bad_resume,
            "job": job_desc,
            "label": 0,
            "expected_name": "Jane Smith",
            "expected_skills": set(),  # No tech skills expected
            "source": "sample_resume_bad.txt"
        })

    # Add synthetics
    for resume_text, label, name, skills in synthetic_resumes:
        test_data.append({
            "resume": resume_text,
            "job": job_desc,
            "label": label,
            "expected_name": name,
            "expected_skills": skills,
            "source": f"synthetic_{name.replace(' ', '_').lower()}"
        })

    return test_data


def compute_confusion_matrix(y_true: list, y_pred: list):
    """Compute TP, TN, FP, FN from ground truth and predictions."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    return tp, tn, fp, fn


def compute_metrics(tp, tn, fp, fn):
    """Derive precision, recall, F1, accuracy from confusion matrix."""
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    return {
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2),
        "specificity": round(specificity * 100, 2),
    }


def evaluate_skill_extraction(test_data: list):
    """Evaluate the skill extraction pipeline."""
    total_expected = 0
    total_found_correct = 0
    total_found = 0
    per_sample = []

    for entry in test_data:
        extracted = set(s.lower() for s in extract_skills(entry["resume"]))
        expected = entry["expected_skills"]

        if expected:
            correct = extracted & expected
            total_expected += len(expected)
            total_found_correct += len(correct)
            total_found += len(extracted)

            sample_precision = len(correct) / len(extracted) if extracted else 0
            sample_recall = len(correct) / len(expected) if expected else 0
        else:
            # For non-tech resumes, any technical skill found is noise but acceptable
            total_found += len(extracted)
            sample_precision = 1.0 if len(extracted) == 0 else 0.5
            sample_recall = 1.0
            correct = set()

        per_sample.append({
            "source": entry["source"],
            "expected_count": len(expected),
            "extracted_count": len(extracted),
            "correct_count": len(correct),
            "precision": round(sample_precision * 100, 1),
            "recall": round(sample_recall * 100, 1),
        })

    overall_precision = total_found_correct / total_found if total_found > 0 else 0
    overall_recall = total_found_correct / total_expected if total_expected > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    return {
        "overall_precision": round(overall_precision * 100, 2),
        "overall_recall": round(overall_recall * 100, 2),
        "overall_f1": round(overall_f1 * 100, 2),
        "per_sample": per_sample,
    }


def evaluate_name_extraction(test_data: list):
    """Evaluate name extraction accuracy."""
    correct = 0
    total = len(test_data)
    details = []

    for entry in test_data:
        extracted = extract_name(entry["resume"])
        expected = entry["expected_name"]
        is_correct = extracted.strip().lower() == expected.strip().lower()
        if is_correct:
            correct += 1
        details.append({
            "source": entry["source"],
            "expected": expected,
            "extracted": extracted,
            "correct": is_correct,
        })

    return {
        "accuracy": round(correct / total * 100, 2) if total > 0 else 0,
        "correct": correct,
        "total": total,
        "details": details,
    }


def run_full_evaluation(threshold: float = 50.0):
    """
    Run the complete evaluation pipeline and return all metrics.
    threshold: the score cutoff (%) to classify a resume as 'match' or 'no match'.
    """
    test_data = _build_test_dataset()
    if not test_data:
        return {"error": "No test data available"}

    # ── Semantic Matching ──
    scores = []
    y_true = []
    y_pred = []
    per_sample_scores = []
    total_time = 0

    for entry in test_data:
        start = time.time()
        score = calculate_match(entry["resume"], entry["job"])
        elapsed = time.time() - start
        total_time += elapsed

        scores.append(score)
        y_true.append(entry["label"])
        y_pred.append(1 if score >= threshold else 0)

        per_sample_scores.append({
            "source": entry["source"],
            "score": score,
            "label": entry["label"],
            "predicted": 1 if score >= threshold else 0,
            "correct": (1 if score >= threshold else 0) == entry["label"],
            "inference_time_ms": round(elapsed * 1000, 1),
        })

    # ── Confusion Matrix ──
    tp, tn, fp, fn = compute_confusion_matrix(y_true, y_pred)
    classification_metrics = compute_metrics(tp, tn, fp, fn)

    # ── Score Statistics ──
    scores_np = np.array(scores)
    relevant_scores = [s for s, l in zip(scores, y_true) if l == 1]
    irrelevant_scores = [s for s, l in zip(scores, y_true) if l == 0]

    score_stats = {
        "mean": round(float(scores_np.mean()), 2),
        "std": round(float(scores_np.std()), 2),
        "min": round(float(scores_np.min()), 2),
        "max": round(float(scores_np.max()), 2),
        "median": round(float(np.median(scores_np)), 2),
        "relevant_mean": round(float(np.mean(relevant_scores)), 2) if relevant_scores else 0,
        "irrelevant_mean": round(float(np.mean(irrelevant_scores)), 2) if irrelevant_scores else 0,
        "score_separation": round(
            float(np.mean(relevant_scores)) - float(np.mean(irrelevant_scores)), 2
        ) if relevant_scores and irrelevant_scores else 0,
    }

    # ── Skill Extraction Metrics ──
    skill_metrics = evaluate_skill_extraction(test_data)

    # ── Name Extraction Metrics ──
    name_metrics = evaluate_name_extraction(test_data)

    # ── Model Info ──
    model = get_model()
    model_info = {
        "name": "all-MiniLM-L6-v2",
        "type": "Sentence Transformer (BERT-based)",
        "embedding_dim": model.get_sentence_embedding_dimension(),
        "max_seq_length": model.max_seq_length,
        "parameters": "22.7M",
        "training": "Trained on 1B+ sentence pairs",
        "similarity_metric": "Cosine Similarity",
    }

    # ── Performance ──
    avg_inference_ms = round(total_time / len(test_data) * 1000, 1) if test_data else 0

    return {
        "model_info": model_info,
        "threshold": threshold,
        "test_samples": len(test_data),
        "confusion_matrix": {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "matrix": [[tn, fp], [fn, tp]],  # [[TN, FP], [FN, TP]]
        },
        "classification_metrics": classification_metrics,
        "score_statistics": score_stats,
        "per_sample_results": per_sample_scores,
        "skill_extraction": skill_metrics,
        "name_extraction": name_metrics,
        "performance": {
            "avg_inference_time_ms": avg_inference_ms,
            "total_evaluation_time_ms": round(total_time * 1000, 1),
        },
    }
