import hashlib
import streamlit as st
from database.db_connection import run_query
from database.heart_db_mysql import init_db as heart_init_db, register_user, login_user

st.set_page_config(page_title="Smart Healthcare System", page_icon="🏥", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
.hero-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
    border-radius: 20px; padding: 40px; text-align: center;
    color: white; margin-bottom: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}
.auth-card {
    background: white; border-radius: 16px; padding: 30px 28px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.10); border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

heart_init_db()

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def ensure_staff_table():
    run_query("""
        CREATE TABLE IF NOT EXISTS hospital_staff (
            staff_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            role ENUM('doctor','receptionist','admin') NOT NULL,
            full_name VARCHAR(120),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """)
    defaults = [
        ("doctor1",       _hash("doctor123"),  "doctor",       "Dr. Rajesh Mehta"),
        ("receptionist1", _hash("recept123"),   "receptionist", "Reception Desk"),
        ("admin",         _hash("admin123"),    "admin",        "Super Admin"),
    ]
    for uname, pwd, role, name in defaults:
        if not run_query("SELECT staff_id FROM hospital_staff WHERE username=%s", (uname,), fetch=True):
            run_query("INSERT INTO hospital_staff (username,password,role,full_name) VALUES (%s,%s,%s,%s)",
                      (uname, pwd, role, name))

ensure_staff_table()

for k, v in {"logged_in": False, "user_id": None, "username": None, "role": None}.items():
    if k not in st.session_state: st.session_state[k] = v

def logout():
    for k in ["logged_in","user_id","username","role"]: st.session_state[k] = None
    st.session_state["logged_in"] = False
    st.rerun()

def show_landing():
    st.markdown("""
    <div class="hero-card">
        <div style="font-size:42px; font-weight:800">🏥 Smart Healthcare System</div>
        <div style="color:#a0aec0">Hospital Management · Heart Disease Prediction · AI Reports</div>
    </div>
    """, unsafe_allow_html=True)

    left, mid, right = st.columns([1, 1.6, 1])
    with left:
        st.markdown("### Features")
        st.markdown("- 🏥 Hospital PMS\n- ❤️ Heart Disease AI\n- 📊 Analytics\n- 📄 PDF Reports\n- 🔐 Role-Based Access")
    with mid:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        choice = st.selectbox("I am a…", ["Patient — Login or Register","Doctor — Login","Receptionist — Login"])
        st.markdown("---")
        if choice == "Patient — Login or Register": _patient_auth_ui()
        elif choice == "Doctor — Login":            _staff_login_ui("doctor")
        else:                                       _staff_login_ui("receptionist")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown("### Role Guide")
        st.markdown("**Patient** — Login/Register. Access Heart Prediction & Hospital records.\n\n"
                    "**Doctor** — View appointments, add diagnosis & prescriptions.\n\n"
                    "**Receptionist** — Register patients, book appointments, generate bills.")

def _patient_auth_ui():
    tab1, tab2 = st.tabs(["🔑 Login","📝 Register"])
    with tab1:
        st.subheader("Patient Login")
        uname = st.text_input("Username", key="pt_lu")
        pwd   = st.text_input("Password", type="password", key="pt_lp")
        if st.button("Login", use_container_width=True, type="primary", key="pt_lbtn"):
            if not uname or not pwd: st.warning("Both fields required.")
            else:
                user = login_user(uname, pwd)
                if user:
                    st.session_state.update(logged_in=True, user_id=user["id"],
                                            username=user["username"], role=user["role"])
                    st.rerun()
                else: st.error("Invalid username or password.")
    with tab2:
        st.subheader("Create Account")
        new_u  = st.text_input("Username", key="pt_ru")
        new_e  = st.text_input("Email (optional)", key="pt_re")
        new_p  = st.text_input("Password", type="password", key="pt_rp")
        conf_p = st.text_input("Confirm Password", type="password", key="pt_rc")
        if st.button("Register", use_container_width=True, type="primary", key="pt_rbtn"):
            if not new_u or not new_p: st.warning("Username and Password required.")
            elif new_p != conf_p:      st.error("Passwords do not match!")
            elif len(new_p) < 6:       st.warning("Password must be at least 6 characters.")
            else:
                ok, msg = register_user(new_u, new_p, new_e)
                if ok: st.success(msg + " Please login.")
                else: st.error(msg)

def _staff_login_ui(role):
    hints = {"doctor": "doctor1 / doctor123", "receptionist": "receptionist1 / recept123"}
    st.subheader(f"{'👨‍⚕️' if role=='doctor' else '🧑‍💼'} {role.title()} Login")
    uname = st.text_input("Username", key=f"st_{role}_u")
    pwd   = st.text_input("Password", type="password", key=f"st_{role}_p")
    st.caption(f"Default: `{hints[role]}`")
    if st.button(f"Login as {role.title()}", use_container_width=True, type="primary", key=f"st_{role}_btn"):
        if not uname or not pwd: st.warning("Both fields required.")
        else:
            row = run_query("SELECT * FROM hospital_staff WHERE username=%s AND password=%s AND role=%s",
                            (uname.strip(), _hash(pwd), role), fetch=True)
            if row:
                r = row[0]
                st.session_state.update(logged_in=True, user_id=r["staff_id"],
                                        username=r["username"], role=r["role"])
                st.rerun()
            else: st.error("Invalid credentials or wrong role.")

def show_sidebar():
    role, uname = st.session_state.role, st.session_state.username
    colors = {"user":"#2ecc71","admin":"#e74c3c","doctor":"#3498db","receptionist":"#9b59b6"}
    color  = colors.get(role, "#667eea")
    with st.sidebar:
        st.markdown(f"""
        <div style='background:{color}; color:white; padding:14px; border-radius:12px; text-align:center; margin-bottom:14px'>
            <h3 style='margin:0'>🏥 Smart Healthcare</h3>
            <p style='margin:6px 0 2px; font-size:14px'><b>{uname}</b></p>
            <span style='font-size:11px; background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:20px'>{role.upper()}</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        module = None
        if role in ("user","admin"):
            module = st.radio("Module", ["❤️ Heart Disease Prediction","🏥 My Hospital Records"],
                              label_visibility="collapsed", key="patient_module")
            st.divider()
        if st.button("🚪 Logout", use_container_width=True): logout()
    return module

def show_patient_hospital_section():
    patients = run_query("SELECT patient_id, full_name FROM patients ORDER BY full_name", fetch=True)
    with st.sidebar:
        st.markdown("#### 🏥 Patient Menu")
        if not patients: st.warning("No patient records found."); return
        pat_opts = {p["full_name"]: p["patient_id"] for p in patients}
        sel  = st.selectbox("Select Your Record", list(pat_opts.keys()), key="pat_hosp_sel")
        page = st.radio("nav", ["🏠 Dashboard","📅 Appointments","💊 Prescriptions","🛏️ Admissions","💰 Bills"],
                        label_visibility="collapsed", key="pat_hosp_page")
    pid = pat_opts[sel]
    from portals import hospital_portal as hp
    if   page == "🏠 Dashboard":      hp._patient_dashboard(pid)
    elif page == "📅 Appointments":   hp._patient_appointments(pid)
    elif page == "💊 Prescriptions":  hp._patient_prescriptions(pid)
    elif page == "🛏️ Admissions":     hp._patient_admissions(pid)
    elif page == "💰 Bills":          hp._patient_bills(pid)

if not st.session_state.logged_in:
    show_landing()
else:
    role   = st.session_state.role
    module = show_sidebar()

    if role == "user":
        if module == "🏥 My Hospital Records": show_patient_hospital_section()
        else:
            from portals import heart_portal; heart_portal.main()
    elif role == "admin":
        if module == "❤️ Heart Disease Prediction":
            from portals import heart_portal; heart_portal.main()
        else:
            from portals import hospital_portal; hospital_portal.main()
    elif role in ("doctor","receptionist"):
        from portals import hospital_portal; hospital_portal.main()
