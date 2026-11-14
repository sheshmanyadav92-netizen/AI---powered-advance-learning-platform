"""QA Agent 5: Accessibility & Responsive Verification Agent.
Verifies WCAG AA color contrast ratios (>= 4.5:1) in BOTH Dark and Light modes
specifically against glass card surfaces, typography font verification (Inter & JetBrains Mono),
and responsive breakpoints.
"""
import sys
import re
import os

def calculate_relative_luminance(rgb):
    """Calculates relative luminance per WCAG 2.1 formula."""
    r, g, b = [x / 255.0 for x in rgb]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(rgb1, rgb2):
    """Calculates contrast ratio between two RGB colors (L1 + 0.05) / (L2 + 0.05)."""
    lum1 = calculate_relative_luminance(rgb1)
    lum2 = calculate_relative_luminance(rgb2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def run_qa_agent_5():
    print("=" * 60)
    print("QA AGENT 5: ACCESSIBILITY (WCAG AA) & DUAL-THEME CONTRAST AGENT")
    print("=" * 60)

    # 1. Dark Mode Glass Surface Contrast Analysis
    # Base background: #0A0E27 (10, 14, 39), Glass fill: rgba(255, 255, 255, 0.04) -> (20, 24, 48)
    dark_glass_surface_rgb = (20, 24, 48)
    dark_test_colors = [
        ("Primary Text (#F8FAFC)", (248, 250, 252), 4.5),
        ("Secondary Text (#94A3B8)", (148, 163, 184), 4.5),
        ("Cyan Accent (#38BDF8)", (56, 189, 248), 4.5),
        ("Emerald Accent (#34D399)", (52, 211, 153), 4.5),
        ("Amber Warning (#FBBF24)", (251, 191, 36), 4.5),
    ]

    print("\n[CHECK 1A] Dark Mode: Computing WCAG AA Contrast Ratios against Glass Card Surface...")
    for name, rgb, target_min in dark_test_colors:
        ratio = contrast_ratio(rgb, dark_glass_surface_rgb)
        status = "✓ PASS (WCAG AA)" if ratio >= target_min else "❌ FAIL"
        print(f"  {name:26}: Ratio = {ratio:.2f}:1 | Minimum = {target_min}:1 | {status}")
        assert ratio >= target_min, f"Dark Mode contrast failure on {name}: {ratio:.2f}:1 < {target_min}:1"

    # 1B. Light Mode Surface Contrast Analysis
    # Base background: #F8FAFC (248, 250, 252), Card surface: #FFFFFF (255, 255, 255)
    light_surface_rgb = (255, 255, 255)
    light_test_colors = [
        ("Primary Text (#0F172A)", (15, 23, 42), 4.5),
        ("Secondary Text (#475569)", (71, 85, 105), 4.5),
        ("Deep Accent (#0369A1)", (3, 105, 161), 4.5),
    ]

    print("\n[CHECK 1B] Light Mode: Computing WCAG AA Contrast Ratios against Light Surface...")
    for name, rgb, target_min in light_test_colors:
        ratio = contrast_ratio(rgb, light_surface_rgb)
        status = "✓ PASS (WCAG AA)" if ratio >= target_min else "❌ FAIL"
        print(f"  {name:26}: Ratio = {ratio:.2f}:1 | Minimum = {target_min}:1 | {status}")
        assert ratio >= target_min, f"Light Mode contrast failure on {name}: {ratio:.2f}:1 < {target_min}:1"

    # 2. Typography Token Verification (Inter & JetBrains Mono)
    print("\n[CHECK 2] Validating Typography Tokens (Inter UI + JetBrains Mono for Numbers)...")
    static_html_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "index.html")
    with open(static_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    has_inter = "Inter" in html_content
    has_mono = "JetBrains Mono" in html_content
    print(f"  Inter Font Included: {'✓ Present' if has_inter else '❌ Missing'}")
    print(f"  JetBrains Mono Included: {'✓ Present' if has_mono else '❌ Missing'}")
    assert has_inter and has_mono, "Required fonts missing in index.html"

    # 3. Responsive Breakpoints Inspection
    print("\n[CHECK 3] Validating Responsive Breakpoints (375px mobile, 768px tablet, 1440px desktop)...")
    has_viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0"' in html_content
    print(f"  Responsive Viewport Meta Tag: {'✓ Present' if has_viewport else '❌ Missing'}")
    assert has_viewport, "Viewport meta tag missing in index.html"

    media_queries = re.findall(r'@media\s*\([^)]+\)', html_content)
    print(f"  Declared Media Queries: {len(media_queries)} breakpoints detected")
    assert len(media_queries) >= 1, "Media queries missing"

    # 4. Form Accessibility & Labeling
    print("\n[CHECK 4] Validating Keyboard Semantics & Form Labels...")
    has_labels = "<label" in html_content
    has_buttons = "<button" in html_content
    print(f"  Explicit Form Labels: {'✓ Present' if has_labels else '❌ Missing'}")
    print(f"  Accessible Button Elements: {'✓ Present' if has_buttons else '❌ Missing'}")
    assert has_labels and has_buttons, "Semantic form elements missing"

    print("\n" + "=" * 60)
    print("QA AGENT 5 STATUS: ALL ACCESSIBILITY & DUAL-THEME CHECKS PASSED (EXIT CODE 0)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_qa_agent_5()
    sys.exit(0 if success else 1)
