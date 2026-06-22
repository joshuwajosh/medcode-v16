import json

# Test the LLM output
json_text = '''{
  "note_type": "operative_report",
  "chief_complaint": "suspicious dark lesions on her back",
  "primary_diagnosis": "two benign skin lesions",
  "secondary_diagnoses": [],
  "procedures_performed": [
    {
      "procedure_name": "Excision of benign skin lesion",
      "lesion_diameter_cm": 1.0,
      "margin_mm": 3,
      "excised_diameter_cm": 1.0 + (2 * 0.3),
      "laterality": "right",
      "pathology": "benign",
      "anatomic_site": "right upper back"
    },
    {
      "procedure_name": "Excision of benign skin lesion",
      "lesion_diameter_cm": 1.5,
      "margin_mm": 4,
      "excised_diameter_cm": 1.5 + (2 * 0.4),
      "laterality": "left",
      "pathology": "benign",
      "anatomic_site": "left upper back"
    }
  ],
  "medications": ["1 percent Lidocaine with epinephrine"],
  "comorbidities": [],
  "clinical_summary": "The patient is a 45-year-old female with two benign skin lesions on her right and left upper back, which were excised under general anesthesia. The procedure was well-tolerated, and the patient was sent home in stable condition. The lesions were found to be benign on preoperative diagnosis.",
  "coding_relevant_details": ["laterality (bilateral)", "lesion diameter (1 cm and 1.5 cm)", "margin (3 mm and 4 mm)"]
}'''

try:
    data = json.loads(json_text)
    print("JSON parsed successfully!")
    print("Note type:", data.get("note_type"))
    print("Procedures performed:", len(data.get("procedures_performed", [])))
    
    # Calculate excised diameter
    for i, proc in enumerate(data.get("procedures_performed", [])):
        lesion_dia = proc.get("lesion_diameter_cm", 0)
        margin_mm = proc.get("margin_mm", 0)
        # The LLM gave us a string expression, we need to evaluate it
        excised_expr = proc.get("excised_diameter_cm", "")
        print(f"Procedure {i+1}:")
        print(f"  Lesion diameter: {lesion_dia} cm")
        print(f"  Margin: {margin_mm} mm")
        print(f"  Excised diameter expression: {excised_expr}")
        
        # Calculate the actual value
        if " + " in excised_expr and "*" in excised_expr:
            # Handle expression like "1.0 + (2 * 0.3)"
            try:
                # Simple evaluation for our specific format
                parts = excised_expr.split(" + ")
                if len(parts) == 2:
                    base = float(parts[0])
                    multiplier_part = parts[1].strip()
                    if multiplier_part.startswith("(2 * ") and multiplier_part.endswith(")"):
                        multiplier = float(multiplier_part[5:-1])
                        excised_dia = base + (2 * multiplier)
                        proc["excised_diameter_cm"] = excised_dia
                        print(f"  Calculated excised diameter: {excised_dia} cm")
            except (ValueError, IndexError, KeyError):
                print(f"  Could not parse expression: {excised_expr}")
                
except Exception as e:
    print("Error parsing JSON:", str(e))