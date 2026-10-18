import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from database.heart_db_mysql import (
    init_db, save_prediction, get_user_predictions,
    get_all_predictions, get_all_users
)
from models.heart_model import predict_heart_disease
from reports.heart_pdf import generate_pdf_report

st.markdown("""
<style>
.high-risk-box { background:linear-gradient(135deg,#ff4b4b,#ff8c8c); color:white;
    padding:20px; border-radius:12px; text-align:center; font-size:22px; font-weight:bold; }
.low-risk-box  { background:linear-gradient(135deg,#21c55d,#6ee7a0); color:white;
    padding:20px; border-radius:12px; text-align:center; font-size:22px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

init_db()

def show_heart_nav():
    with st.sidebar:
        st.markdown("#### Heart Module")
        if st.session_state.role == "admin":
            opts = ["👨‍💼 Admin Panel"]
        else:
            opts = ["🏠 Dashboard","🔬 Prediction","📊 My History"]
        return st.radio("nav", opts, label_visibility="collapsed", key="heart_nav")

def show_user_dashboard():
    st.markdown("## 🏠 My Dashboard")
    preds = get_user_predictions(st.session_state.user_id)
    if not preds:
        st.info("No predictions yet. Go to Prediction tab!")
        return
    total = len(preds)
    high  = sum(1 for p in preds if "High" in p["prediction"])
    avg_c = round(sum(p["confidence"] for p in preds) / total, 1)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", total); c2.metric("High Risk", high)
    c3.metric("Low Risk", total-high); c4.metric("Avg Confidence", f"{avg_c}%")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Risk Distribution")
        pie = pd.DataFrame({"Category":["High Risk","Low Risk"], "Count":[high, total-high]})
        st.plotly_chart(px.pie(pie, names="Category", values="Count",
            color_discrete_map={"High Risk":"#e74c3c","Low Risk":"#2ecc71"}, hole=0.4),
            use_container_width=True)
    with col2:
        st.markdown("#### Prediction Timeline")
        df = pd.DataFrame(preds)
        df["date"] = pd.to_datetime(df["predicted_at"]).dt.date
        tl = df.groupby("date").size().reset_index(name="count")
        tl["date"] = pd.to_datetime(tl["date"]).dt.strftime("%d %b %Y")
        fig = px.bar(tl, x="date", y="count",
            color_discrete_sequence=["#c0392b"],
            labels={"date": "Date", "count": "Number of Predictions"})
        fig.update_xaxes(type="category")
        fig.update_yaxes(dtick=max(1, -(-int(tl["count"].max()) // 5)))
        st.plotly_chart(fig, use_container_width=True)

def show_prediction_page():
    st.markdown("## 🔬 Heart Disease Prediction")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Basic Info**")
        age      = st.number_input("Age", 20, 100, 45)
        sex      = st.selectbox("Sex", [0,1], format_func=lambda x: "Female" if x==0 else "Male")
        cp       = st.selectbox("Chest Pain", [0,1,2,3],
                    format_func=lambda x: {0:"Typical",1:"Atypical",2:"Non-Anginal",3:"Asymptomatic"}[x])
        trestbps = st.number_input("Resting BP", 80, 220, 120)
        chol     = st.number_input("Cholesterol", 100, 600, 200)
        fbs      = st.selectbox("Fasting Sugar >120?", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        restecg  = st.selectbox("Resting ECG", [0,1,2],
                    format_func=lambda x: {0:"Normal",1:"ST-T Abnormal",2:"LV Hypertrophy"}[x])
    with col2:
        st.markdown("**Exercise & Advanced**")
        thalach  = st.number_input("Max Heart Rate", 60, 250, 150)
        exang    = st.selectbox("Exercise Angina?", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        oldpeak  = st.number_input("Oldpeak", 0.0, 10.0, 1.0, 0.1)
        slope    = st.selectbox("Slope", [0,1,2],
                    format_func=lambda x: {0:"Upsloping",1:"Flat",2:"Downsloping"}[x])
        ca       = st.selectbox("Major Vessels (0-3)", [0,1,2,3])
        thal     = st.selectbox("Thalassemia", [1,2,3],
                    format_func=lambda x: {1:"Normal",2:"Fixed Defect",3:"Reversible"}[x])
        predict_btn = st.button("Predict Risk", use_container_width=True, type="primary")

    if predict_btn:
        inputs = dict(age=age, sex=sex, cp=cp, trestbps=trestbps, chol=chol,
                      fbs=fbs, restecg=restecg, thalach=thalach, exang=exang,
                      oldpeak=oldpeak, slope=slope, ca=ca, thal=thal)
        with st.spinner("Calculating..."):
            prediction, confidence = predict_heart_disease(inputs)

        st.divider()
        is_high = "High" in prediction
        box_cls = "high-risk-box" if is_high else "low-risk-box"
        st.markdown(f'<div class="{box_cls}">{prediction}<br><span style="font-size:16px">Confidence: {confidence}%</span></div>',
                    unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(mode="gauge+number", value=confidence,
            title={"text":"Model Confidence (%)"},
            gauge={"axis":{"range":[0,100]},
                   "bar":{"color":"#e74c3c" if is_high else "#2ecc71"}}))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

        save_prediction(st.session_state.user_id, inputs, prediction, confidence)
        pdf_bytes = generate_pdf_report(st.session_state.username, inputs, prediction, confidence)
        st.download_button("Download PDF Report", data=pdf_bytes,
            file_name=f"heart_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf", use_container_width=True)
        st.warning("This is an ML prediction only. Always consult a doctor.")

def show_history_page():
    st.markdown("## 📊 My Prediction History")
    preds = get_user_predictions(st.session_state.user_id)
    if not preds:
        st.info("No predictions yet.")
        return
    df = pd.DataFrame(preds)
    cols = ["predicted_at","age","sex","cp","chol","trestbps","thalach","prediction","confidence"]
    st.dataframe(df[cols].rename(columns={
        "predicted_at":"Date","age":"Age","sex":"Sex","cp":"CP",
        "chol":"Cholesterol","trestbps":"BP","thalach":"Max HR",
        "prediction":"Result","confidence":"Confidence%"
    }), use_container_width=True, hide_index=True)
    st.plotly_chart(px.scatter(df, x="chol", y="thalach", color="prediction",
        color_discrete_map={"High Risk":"#e74c3c","Low Risk":"#2ecc71"},
        hover_data=["age","confidence"]), use_container_width=True)

def show_admin_panel():
    st.markdown("## 👨‍💼 Admin Dashboard")
    all_preds = get_all_predictions()
    all_users = get_all_users()
    total = len(all_preds)
    high  = sum(1 for p in all_preds if "High" in p.get("prediction",""))

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Users", len(all_users)); c2.metric("Total Predictions", total)
    c3.metric("High Risk", high);       c4.metric("Low Risk", total-high)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["All Predictions","All Users","Analytics"])
    with tab1:
        if all_preds:
            df = pd.DataFrame(all_preds)
            st.dataframe(df[["username","predicted_at","age","sex","cp","chol","prediction","confidence"]],
                         use_container_width=True, hide_index=True)
        else: st.info("No predictions.")
    with tab2:
        if all_users: st.dataframe(pd.DataFrame(all_users), use_container_width=True, hide_index=True)
        else: st.info("No users.")
    with tab3:
        if not all_preds: st.info("No data."); return
        df = pd.DataFrame(all_preds)
        col1, col2 = st.columns(2)
        with col1:
            pie = df["prediction"].value_counts().reset_index()
            pie.columns = ["Risk","Count"]
            st.plotly_chart(px.pie(pie, names="Risk", values="Count", hole=0.35),
                            use_container_width=True)
        with col2:
            st.plotly_chart(px.histogram(df, x="age", color="prediction", nbins=20),
                            use_container_width=True)
        st.plotly_chart(px.box(df, x="prediction", y="chol", color="prediction"),
                        use_container_width=True)

def main():
    page = show_heart_nav()
    if   page == "🏠 Dashboard":    show_user_dashboard()
    elif page == "🔬 Prediction":   show_prediction_page()
    elif page == "📊 My History":   show_history_page()
    elif page == "👨‍💼 Admin Panel":
        if st.session_state.role == "admin": show_admin_panel()
        else: st.error("Admin access only.")
