from fpdf import FPDF
from datetime import datetime

LABELS = {
    "age": "Age (years)", "sex": "Sex", "cp": "Chest Pain Type",
    "trestbps": "Resting BP (mmHg)", "chol": "Cholesterol (mg/dl)",
    "fbs": "Fasting Blood Sugar >120", "restecg": "Resting ECG",
    "thalach": "Max Heart Rate", "exang": "Exercise Angina",
    "oldpeak": "ST Depression", "slope": "Slope", "ca": "Major Vessels", "thal": "Thalassemia",
}
MAPS = {
    "sex":     {0:"Female", 1:"Male"},
    "cp":      {0:"Typical Angina", 1:"Atypical Angina", 2:"Non-anginal", 3:"Asymptomatic"},
    "restecg": {0:"Normal", 1:"ST-T Abnormality", 2:"LV Hypertrophy"},
    "slope":   {0:"Upsloping", 1:"Flat", 2:"Downsloping"},
    "thal":    {1:"Normal", 2:"Fixed Defect", 3:"Reversible Defect"},
    "fbs":     {0:"No", 1:"Yes"}, "exang": {0:"No", 1:"Yes"},
}

def fmt(key, val):
    return MAPS[key].get(val, str(val)) if key in MAPS else str(val)

class HeartReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(220, 50, 50)
        self.cell(0, 10, "Heart Disease Prediction Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_draw_color(220, 50, 50)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential Medical Report", align="C")

def generate_pdf_report(username, inputs, prediction, confidence):
    pdf = HeartReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 9, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    section("Patient Information")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Username    : {username}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Report Date : {datetime.now().strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    section("Clinical Input Values")
    pdf.set_font("Helvetica", "", 10)
    for key, label in LABELS.items():
        val = fmt(key, inputs.get(key, "-"))
        pdf.cell(95, 8, f"  {label}", border=1, fill=True)
        pdf.cell(95, 8, f"  {val}",   border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    section("Prediction Result")
    is_high = "High" in prediction
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(200, 0, 0) if is_high else pdf.set_text_color(0, 150, 50)
    result_text = "HIGH RISK - Heart Disease Detected" if is_high else "LOW RISK - No Heart Disease Detected"
    pdf.cell(0, 12, result_text, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Model Confidence: {confidence}%", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: This report is an ML model output only. "
        "It is not a medical diagnosis. Please consult a qualified doctor.", align="C")

    return bytes(pdf.output())
