"""Certificate generation service using ReportLab.
Issues cryptographically traceable completion certificates upon achieving P(L_n) >= 0.80 mastery.
"""
import os
import uuid
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

CERT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "certificates_storage"))
os.makedirs(CERT_DIR, exist_ok=True)

def generate_certificate_pdf(
    learner_name: str,
    skill_name: str,
    role_title: str,
    verification_code: str | None = None,
    issued_at: datetime | None = None,
) -> tuple[str, str]:
    """Generates an academic certificate PDF and returns (verification_code, file_path)."""
    code = verification_code or str(uuid.uuid4())
    date_str = (issued_at or datetime.now(timezone.utc)).strftime("%B %d, %Y")
    file_name = f"certificate_{code}.pdf"
    pdf_path = os.path.join(CERT_DIR, file_name)

    c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Decorative Border
    c.setStrokeColor(colors.HexColor("#0A0E27"))
    c.setLineWidth(14)
    c.rect(20, 20, width - 40, height - 40)

    c.setStrokeColor(colors.HexColor("#38BDF8"))
    c.setLineWidth(3)
    c.rect(30, 30, width - 60, height - 60)

    # Corner Accents
    c.setFillColor(colors.HexColor("#0A0E27"))
    c.rect(40, 40, width - 80, height - 80, fill=True, stroke=False)

    # Inner Gold Border
    c.setStrokeColor(colors.HexColor("#FBBF24"))
    c.setLineWidth(1.5)
    c.rect(48, 48, width - 96, height - 96)

    # Header / Institution
    c.setFillColor(colors.HexColor("#38BDF8"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2.0, height - 90, "AI-POWERED PERSONALIZED LEARNING PLATFORM")

    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2.0, height - 110, "COGNITIVE MASTERY & SKILL ACQUISITION CREDENTIAL")

    # Certificate Title
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2.0, height - 170, "CERTIFICATE OF MASTERY")

    # Recipient
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2.0, height - 215, "This is hereby awarded to")

    c.setFillColor(colors.HexColor("#34D399"))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2.0, height - 255, learner_name)

    # Skill & Role details
    c.setFillColor(colors.HexColor("#E2E8F0"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(
        width / 2.0,
        height - 300,
        f"for demonstrating verified Bayesian Mastery (P(L_n) >= 0.80) in the competency of",
    )

    c.setFillColor(colors.HexColor("#38BDF8"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2.0, height - 335, skill_name)

    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(
        width / 2.0,
        height - 370,
        f"as evaluated against industry role requirements for {role_title}.",
    )

    # Footer Metadata
    c.setStrokeColor(colors.HexColor("#334155"))
    c.setLineWidth(1)
    c.line(80, 110, width - 80, 110)

    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 10)
    c.drawString(80, 85, f"Issued Date: {date_str}")
    c.drawCentredString(width / 2.0, 85, f"Verification Code: {code}")
    c.drawRightString(width - 80, 85, "Verified via Bayesian Knowledge Tracing")

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(width / 2.0, 62, f"Public Employer Verification URL: /certificates/verify/{code}")

    c.save()
    return code, pdf_path

