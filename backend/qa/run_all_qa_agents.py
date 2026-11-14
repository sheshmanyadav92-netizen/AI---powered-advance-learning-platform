"""Master QA Swarm Runner.
Executes all 5 QA agents, collects their literal raw terminal outputs,
and generates the authoritative qa-report.md deliverable.
"""
import subprocess
import sys
import os
from datetime import datetime, timezone

QA_AGENTS = [
    ("Agent 1: Formula Cross-Check Agent", "backend/qa/qa_agent_1_formula_crosscheck.py"),
    ("Agent 2: API Contract Agent", "backend/qa/qa_agent_2_api_contract.py"),
    ("Agent 3: Security Verification & OWASP ASVS Agent", "backend/qa/qa_agent_3_security.py"),
    ("Agent 4: E2E Pedagogical Adaptation Flow Agent", "backend/qa/qa_agent_4_e2e_flow.py"),
    ("Agent 5: Accessibility & Responsive Design Agent", "backend/qa/qa_agent_5_accessibility_responsive.py"),
]

def run_all_qa():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    python_bin = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    
    report_sections = []
    overall_success = True
    
    report_sections.append("# Autonomous QA Agent Swarm — Comprehensive Verification Report\n")
    report_sections.append(f"**Generated At:** {datetime.now(timezone.utc).isoformat()}  \n")
    report_sections.append(f"**Platform:** AI-Powered Personalized Learning Platform  \n")
    report_sections.append("**Execution Policy:** Zero narrative summarization; raw terminal execution outputs appended per agent.\n\n---\n")

    for title, script_rel in QA_AGENTS:
        script_path = os.path.join(base_dir, script_rel)
        print(f"\n[RUNNING] {title}...")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(base_dir, "backend")
        
        proc = subprocess.run(
            [python_bin, script_path],
            capture_output=True,
            text=True,
            env=env
        )
        
        status_badge = "✅ PASSED (Exit Code 0)" if proc.returncode == 0 else f"❌ FAILED (Exit Code {proc.returncode})"
        if proc.returncode != 0:
            overall_success = False
            
        print(f"[{status_badge}] {title}")
        
        report_sections.append(f"## {title}\n")
        report_sections.append(f"**Status:** {status_badge}  \n")
        report_sections.append(f"**Script Target:** `{script_rel}`\n\n")
        report_sections.append("### Literal Terminal Output:\n")
        report_sections.append("```text\n")
        report_sections.append(proc.stdout)
        if proc.stderr:
            report_sections.append("\n[STDERR]:\n" + proc.stderr)
        report_sections.append("\n```\n\n---\n")

    # Final verdict
    report_sections.append("## Overall QA Swarm Verdict\n")
    if overall_success:
        report_sections.append("🏆 **ALL 5 QA AGENTS PASSED WITH EXIT CODE 0.**  \n")
        report_sections.append("All mathematical formulas, API contracts, security controls, adaptation flows, and WCAG AA accessibility contrast ratios were independently verified against raw execution.\n")
    else:
        report_sections.append("❌ **QA VERIFICATION DETECTED FAILURES.** Review raw logs above.\n")

    report_content = "".join(report_sections)
    report_path = os.path.join(base_dir, "qa-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\nReport written to {report_path}")
    return overall_success

if __name__ == "__main__":
    success = run_all_qa()
    sys.exit(0 if success else 1)
