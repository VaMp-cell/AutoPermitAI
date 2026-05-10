import os
import sys
import logging
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock vision service to return some plausible detections for the demo
def mock_process_blueprint(pdf_path, output_dir):
    from app.schemas import DetectionBox
    import shutil
    from PIL import Image
    
    # Just copy the first page image or a placeholder
    # For this test, we'll use the one we generated earlier
    img_path = Path(r'C:\Users\Om\OneDrive\Desktop\AutoPermitAi\backend\uploads\demo_blueprint.pdf') # Wait, this is PDF
    # We need an image. The script earlier created the PDF from the PNG.
    # The PNG is at C:\Users\Om\.gemini\antigravity\brain\9d1164f6-32f2-4b49-995b-0bd72acbea88\demo_blueprint_goa_1778435954358.png
    orig_png = r'C:\Users\Om\.gemini\antigravity\brain\9d1164f6-32f2-4b49-995b-0bd72acbea88\demo_blueprint_goa_1778435954358.png'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(orig_png, output_dir / "original.jpg")
    shutil.copy(orig_png, output_dir / "annotated.jpg")
    
    detections = [
        DetectionBox(label="bedroom", confidence=0.95, x=0.2, y=0.3, width=0.15, height=0.2),
        DetectionBox(label="kitchen", confidence=0.92, x=0.5, y=0.3, width=0.1, height=0.15),
        DetectionBox(label="living_room", confidence=0.98, x=0.3, y=0.6, width=0.3, height=0.25),
        DetectionBox(label="staircase", confidence=0.88, x=0.8, y=0.5, width=0.1, height=0.2),
        DetectionBox(label="fire_exit", confidence=0.85, x=0.9, y=0.1, width=0.05, height=0.05),
    ]
    return Image.open(orig_png), Image.open(orig_png), detections

def test_full_analysis():
    print("--- Testing Full Compliance Analysis Pipeline ---")
    from app.services.compliance_service import ComplianceService
    from app.services.ocr_service import OCRService
    from app.config import settings
    
    # Setup
    pdf_path = Path("backend/uploads/demo_blueprint.pdf")
    output_dir = Path("backend/outputs/demo_report")
    
    ocr_service = OCRService()
    compliance_service = ComplianceService()
    compliance_service.initialize()
    
    # 1. Vision (Mocked for this test to ensure consistency)
    print("1. Running Vision Pipeline (Mocked)...")
    original_img, _, detections = mock_process_blueprint(pdf_path, output_dir)
    
    # 2. OCR
    print("2. Running OCR Extraction...")
    ocr_results = ocr_service.extract_dimensions(original_img)
    ocr_formatted = ocr_service.format_for_llm(ocr_results)
    print(f"   Extracted {len(ocr_results)} text regions.")
    
    # 3. Compliance
    print("3. Running LLM Compliance Analysis...")
    result = compliance_service.analyze(
        detections=detections,
        ocr_results=ocr_results,
        ocr_formatted=ocr_formatted
    )
    
    print("\n--- Analysis Result ---")
    print(f"Overall Status: {result.get('overall_status')}")
    print(f"Summary: {result.get('summary')[:200]}...")
    
    checks = result.get("compliance_checks", [])
    print(f"\nPerformed {len(checks)} compliance checks:")
    for check in checks[:5]:
        line = f"  [{check['status']}] {check['code_reference']}: {check['requirement']}"
        print(line.encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    test_full_analysis()
