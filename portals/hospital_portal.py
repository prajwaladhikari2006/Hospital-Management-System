import streamlit as st
import pandas as pd
from datetime import date
from database.db_connection import run_query

def main():
    role = st.session_state.role
    if   role == "doctor":       _doctor_main()
    elif role == "receptionist": _receptionist_main()
    elif role == "admin":        _admin_main()
    else: st.info("Hospital portal not available for your role.")

# ── DOCTOR ──────────────────────────────────────────────────
def _doctor_main():
    st.title("Doctor Portal")
    with st.sidebar:
        st.markdown("#### Doctor Menu")
        page = st.radio("nav", ["📅 My Appointments","📝 Add Diagnosis","💊 Add Prescription"],
                        label_visibility="collapsed", key="doc_page")
    did = _resolve_doctor_id(st.session_state.username)
    if did is None:
        st.warning("Staff account not linked to a doctor record. Select your name:")
        doctors = run_query("SELECT doctor_id, full_name, specialisation FROM doctors WHERE is_active=1", fetch=True)
        if not doctors: st.error("No doctor records found."); return
        opts = {f"{d['full_name']} ({d['specialisation']})": d["doctor_id"] for d in doctors}
        did  = opts[st.selectbox("Select doctor profile", list(opts.keys()), key="doc_fallback_sel")]

    if   page == "📅 My Appointments": _doctor_appointments(did)
    elif page == "📝 Add Diagnosis":   _doctor_add_diagnosis(did)
    elif page == "💊 Add Prescription":_doctor_add_prescription(did)

def _resolve_doctor_id(username):
    row = run_query("SELECT full_name FROM hospital_staff WHERE username=%s AND role='doctor'",
                    (username,), fetch=True)
    if row and row[0].get("full_name"):
        name = row[0]["full_name"].replace("Dr.", "").strip()
        match = run_query("SELECT doctor_id FROM doctors WHERE full_name LIKE %s AND is_active=1",
                          (f"%{name}%",), fetch=True)
        if match: return match[0]["doctor_id"]
    return None

def _doctor_appointments(did):
    st.subheader("📅 My Appointments")
    rows = run_query("""
        SELECT a.appt_id, p.full_name AS patient_name, a.appt_date,
               a.appt_time, a.status, a.diagnosis_notes
        FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
        WHERE a.doctor_id=%s ORDER BY a.appt_date DESC
    """, (did,), fetch=True)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No appointments.")

def _doctor_add_diagnosis(did):
    st.subheader("📝 Add Diagnosis Notes")
    appts = run_query("""
        SELECT a.appt_id, p.full_name, a.appt_date, a.status
        FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
        WHERE a.doctor_id=%s ORDER BY a.appt_date DESC
    """, (did,), fetch=True)
    if not appts: st.info("No appointments."); return
    opts = {f"#{a['appt_id']} - {a['full_name']} - {a['appt_date']} [{a['status']}]": a["appt_id"] for a in appts}
    appt_id = opts[st.selectbox("Select Appointment", list(opts.keys()), key="diag_sel")]
    notes   = st.text_area("Diagnosis Notes", key="diag_notes")
    if st.button("Save Diagnosis", type="primary"):
        run_query("UPDATE appointments SET diagnosis_notes=%s, status='Completed' WHERE appt_id=%s AND doctor_id=%s",
                  (notes, appt_id, did))
        st.success("Diagnosis saved.")

def _doctor_add_prescription(did):
    st.subheader("💊 Add Prescription")
    appts = run_query("""
        SELECT a.appt_id, p.full_name, a.appt_date
        FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
        WHERE a.doctor_id=%s ORDER BY a.appt_date DESC
    """, (did,), fetch=True)
    if not appts: st.info("No appointments."); return
    opts     = {f"#{a['appt_id']} - {a['full_name']} - {a['appt_date']}": a["appt_id"] for a in appts}
    appt_id  = opts[st.selectbox("Select Appointment", list(opts.keys()), key="rx_sel")]
    medicine = st.text_input("Medicine Name", key="rx_med")
    dosage   = st.text_input("Dosage", key="rx_dos")
    duration = st.number_input("Duration (Days)", 1, 365, key="rx_dur")
    instruct = st.text_area("Instructions", key="rx_instr")
    if st.button("Add Prescription", type="primary"):
        if not medicine: st.warning("Medicine name required.")
        else:
            run_query("INSERT INTO prescriptions (appt_id,medicine_name,dosage,duration_days,instructions) VALUES (%s,%s,%s,%s,%s)",
                      (appt_id, medicine, dosage, duration, instruct))
            st.success("Prescription added.")

# ── RECEPTIONIST ─────────────────────────────────────────────
def _receptionist_main():
    st.title("Receptionist Portal")
    with st.sidebar:
        st.markdown("#### Receptionist Menu")
        page = st.radio("nav", ["➕ Register Patient","📅 Book Appointment","🛏️ Admit Patient","💰 Generate Bill"],
                        label_visibility="collapsed", key="rec_page")
    if   page == "➕ Register Patient":  _register_patient()
    elif page == "📅 Book Appointment":  _book_appointment()
    elif page == "🛏️ Admit Patient":     _admit_patient()
    elif page == "💰 Generate Bill":     _generate_bill()

def _register_patient():
    st.subheader("➕ Register New Patient")
    with st.form("reg_pat_form"):
        full_name = st.text_input("Full Name")
        dob       = st.date_input("Date of Birth", value=date(2000,1,1))
        gender    = st.selectbox("Gender", ["Male","Female","Other"])
        blood     = st.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])
        contact   = st.text_input("Contact Number")
        email     = st.text_input("Email")
        address   = st.text_area("Address")
        emergency = st.text_input("Emergency Contact")
        submit    = st.form_submit_button("Register Patient")
    if submit:
        if not full_name or not contact: st.warning("Full name and contact required.")
        else:
            run_query("INSERT INTO patients (full_name,dob,gender,blood_group,contact_no,email,address,emergency_contact,reg_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURDATE())",
                      (full_name, str(dob), gender, blood, contact, email or None, address or None, emergency or None))
            st.success("Patient registered.")

def _book_appointment():
    st.subheader("📅 Book Appointment")
    patients = run_query("SELECT patient_id, full_name FROM patients ORDER BY full_name", fetch=True)
    doctors  = run_query("SELECT doctor_id, full_name, specialisation FROM doctors WHERE is_active=1", fetch=True)
    if not patients: st.warning("No patients registered."); return
    if not doctors:  st.warning("No active doctors."); return
    pat_opts  = {f"{p['patient_id']} - {p['full_name']}": p["patient_id"] for p in patients}
    doc_opts  = {f"{d['full_name']} ({d['specialisation']})": d["doctor_id"] for d in doctors}
    sel_p     = st.selectbox("Patient", list(pat_opts.keys()), key="ba_pat")
    sel_d     = st.selectbox("Doctor",  list(doc_opts.keys()), key="ba_doc")
    appt_date = st.date_input("Date", key="ba_date")
    appt_time = st.text_input("Time (e.g. 10:30)", key="ba_time")
    if st.button("Book Appointment", type="primary"):
        run_query("INSERT INTO appointments (patient_id,doctor_id,appt_date,appt_time,status) VALUES (%s,%s,%s,%s,'Scheduled')",
                  (pat_opts[sel_p], doc_opts[sel_d], str(appt_date), appt_time))
        st.success("Appointment booked.")

def _admit_patient():
    st.subheader("🛏️ Admit Patient")
    patients = run_query("SELECT patient_id, full_name FROM patients ORDER BY full_name", fetch=True)
    doctors  = run_query("SELECT doctor_id, full_name FROM doctors WHERE is_active=1", fetch=True)
    wards    = run_query("SELECT ward_id, ward_name FROM wards", fetch=True)
    if not patients: st.warning("No patients."); return
    if not wards:    st.warning("No wards."); return
    pat_opts  = {f"{p['patient_id']} - {p['full_name']}": p["patient_id"] for p in patients}
    ward_opts = {f"{w['ward_id']} - {w['ward_name']}": w["ward_id"] for w in wards}
    doc_opts  = {d["full_name"]: d["doctor_id"] for d in doctors} if doctors else {}
    sel_p    = st.selectbox("Patient", list(pat_opts.keys()),  key="ap_pat")
    sel_w    = st.selectbox("Ward",    list(ward_opts.keys()), key="ap_ward")
    sel_d    = st.selectbox("Attending Doctor", list(doc_opts.keys()), key="ap_doc") if doc_opts else None
    adm_date = st.date_input("Admit Date", key="ap_date")
    reason   = st.text_area("Reason", key="ap_reason")
    if st.button("Admit Patient", type="primary"):
        run_query("INSERT INTO admissions (patient_id,ward_id,attending_doctor,admit_date,reason) VALUES (%s,%s,%s,%s,%s)",
                  (pat_opts[sel_p], ward_opts[sel_w], doc_opts[sel_d] if sel_d else None, str(adm_date), reason))
        st.success("Patient admitted.")

def _generate_bill():
    st.subheader("💰 Generate Bill")
    patients = run_query("SELECT patient_id, full_name FROM patients ORDER BY full_name", fetch=True)
    if not patients: st.warning("No patients."); return
    pat_opts = {f"{p['patient_id']} - {p['full_name']}": p["patient_id"] for p in patients}
    pid      = pat_opts[st.selectbox("Patient", list(pat_opts.keys()), key="gb_pat")]
    adm      = run_query("SELECT admission_id, admit_date FROM admissions WHERE patient_id=%s", (pid,), fetch=True)
    adm_id   = None
    if adm:
        adm_opts = {f"Admission #{a['admission_id']} - {a['admit_date']}": a["admission_id"] for a in adm}
        sel = st.selectbox("Linked Admission", ["No Admission / OPD"] + list(adm_opts.keys()), key="gb_adm")
        if sel != "No Admission / OPD": adm_id = adm_opts[sel]
    c_fee  = st.number_input("Consultation Fee (₹)", 0.0, key="gb_cf")
    m_fee  = st.number_input("Medicine Fee (₹)",     0.0, key="gb_mf")
    r_fee  = st.number_input("Room Charge (₹)",      0.0, key="gb_rc")
    paid   = st.selectbox("Paid Status", ["Pending","Paid"], key="gb_ps")
    if st.button("Generate Bill", type="primary"):
        run_query("INSERT INTO bills (patient_id,admission_id,consultation_fee,medicine_fee,room_charge,paid_status,bill_date) VALUES (%s,%s,%s,%s,%s,%s,CURDATE())",
                  (pid, adm_id, c_fee, m_fee, r_fee, 1 if paid=="Paid" else 0))
        st.success("Bill generated.")

# ── ADMIN ────────────────────────────────────────────────────
def _admin_main():
    with st.sidebar:
        st.markdown("#### Admin - Hospital")
        portal = st.radio("nav", ["👤 Patient Portal","👨‍⚕️ Doctor Portal","🧑‍💼 Receptionist Portal"],
                          label_visibility="collapsed", key="admin_hosp_page")
    if   portal == "👤 Patient Portal":         _admin_patient_portal()
    elif portal == "👨‍⚕️ Doctor Portal":         _admin_doctor_portal()
    elif portal == "🧑‍💼 Receptionist Portal":   _receptionist_main()

def _admin_patient_portal():
    st.title("Patient Portal")
    patients = run_query("SELECT patient_id, full_name FROM patients ORDER BY patient_id", fetch=True)
    if not patients: st.warning("No patients."); return
    pat_opts = {f"{p['patient_id']} - {p['full_name']}": p["patient_id"] for p in patients}
    with st.sidebar:
        st.markdown("---")
        sel  = st.selectbox("Select Patient", list(pat_opts.keys()), key="adm_pat_sel")
        menu = st.radio("menu", ["Dashboard","Appointments","Prescriptions","Admissions","Bills"],
                        label_visibility="collapsed", key="adm_pat_page")
    pid = pat_opts[sel]
    if   menu == "Dashboard":      _patient_dashboard(pid)
    elif menu == "Appointments":   _patient_appointments(pid)
    elif menu == "Prescriptions":  _patient_prescriptions(pid)
    elif menu == "Admissions":     _patient_admissions(pid)
    elif menu == "Bills":          _patient_bills(pid)

def _admin_doctor_portal():
    st.title("Doctor Portal")
    doctors = run_query("SELECT doctor_id, full_name, specialisation FROM doctors WHERE is_active=1", fetch=True)
    if not doctors: st.warning("No active doctors."); return
    doc_opts = {f"{d['full_name']} ({d['specialisation']})": d["doctor_id"] for d in doctors}
    with st.sidebar:
        st.markdown("---")
        sel  = st.selectbox("Select Doctor", list(doc_opts.keys()), key="adm_doc_sel")
        page = st.radio("menu", ["📅 My Appointments","📝 Add Diagnosis","💊 Add Prescription"],
                        label_visibility="collapsed", key="adm_doc_page")
    did = doc_opts[sel]
    if   page == "📅 My Appointments":  _doctor_appointments(did)
    elif page == "📝 Add Diagnosis":    _doctor_add_diagnosis(did)
    elif page == "💊 Add Prescription": _doctor_add_prescription(did)

# ── PATIENT VIEWS (shared) ────────────────────────────────────
def _patient_dashboard(pid):
    p = run_query("SELECT * FROM patients WHERE patient_id=%s", (pid,), fetch=True)
    if not p: st.error("Patient not found."); return
    p = p[0]
    st.subheader(f"Welcome, {p['full_name']}")
    c1,c2,c3,c4 = st.columns(4)
    appts = run_query("SELECT COUNT(*) AS cnt FROM appointments WHERE patient_id=%s", (pid,), fetch=True)
    bills = run_query("SELECT COUNT(*) AS cnt FROM bills WHERE patient_id=%s AND paid_status=0", (pid,), fetch=True)
    rx    = run_query("SELECT COUNT(*) AS cnt FROM prescriptions r JOIN appointments a ON r.appt_id=a.appt_id WHERE a.patient_id=%s", (pid,), fetch=True)
    adm   = run_query("SELECT COUNT(*) AS cnt FROM admissions WHERE patient_id=%s AND discharge_date IS NULL", (pid,), fetch=True)
    c1.metric("Appointments",     appts[0]["cnt"] if appts else 0)
    c2.metric("Pending Bills",    bills[0]["cnt"] if bills else 0)
    c3.metric("Prescriptions",    rx[0]["cnt"]    if rx    else 0)
    c4.metric("Currently Admitted",adm[0]["cnt"]  if adm   else 0)
    st.divider()
    st.markdown(f"**Blood Group:** {p['blood_group']}  |  **DOB:** {p['dob']}  |  **Contact:** {p['contact_no']}")
    if p['address']: st.markdown(f"**Address:** {p['address']}")

def _patient_appointments(pid):
    st.subheader("📅 My Appointments")
    rows = run_query("""
        SELECT a.appt_id, a.appt_date, a.appt_time, a.status,
               a.diagnosis_notes, d.full_name AS doctor_name, d.specialisation
        FROM appointments a JOIN doctors d ON a.doctor_id=d.doctor_id
        WHERE a.patient_id=%s ORDER BY a.appt_date DESC
    """, (pid,), fetch=True)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No appointments.")

def _patient_prescriptions(pid):
    st.subheader("💊 My Prescriptions")
    rows = run_query("""
        SELECT r.medicine_name, r.dosage, r.duration_days, r.instructions,
               a.appt_date, d.full_name AS doctor_name
        FROM prescriptions r
        JOIN appointments a ON r.appt_id=a.appt_id
        JOIN doctors d ON a.doctor_id=d.doctor_id
        WHERE a.patient_id=%s ORDER BY a.appt_date DESC
    """, (pid,), fetch=True)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No prescriptions.")

def _patient_admissions(pid):
    st.subheader("🛏️ My Admissions")
    rows = run_query("""
        SELECT adm.admission_id, adm.admit_date, adm.discharge_date, adm.reason,
               w.ward_name, d.full_name AS doctor_name
        FROM admissions adm JOIN wards w ON adm.ward_id=w.ward_id
        LEFT JOIN doctors d ON adm.attending_doctor=d.doctor_id
        WHERE adm.patient_id=%s ORDER BY adm.admit_date DESC
    """, (pid,), fetch=True)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No admissions.")

def _patient_bills(pid):
    st.subheader("💰 My Bills")
    rows = run_query("""
        SELECT bill_id, consultation_fee, medicine_fee, room_charge,
               total_amount, paid_status, bill_date
        FROM bills WHERE patient_id=%s ORDER BY bill_date DESC
    """, (pid,), fetch=True)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No bills.")
