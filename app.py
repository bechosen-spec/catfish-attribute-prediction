"""Database-backed Streamlit entry point; inference modules remain unchanged."""
from __future__ import annotations
import json
import logging
import pandas as pd
import streamlit as st
from sqlalchemy import select
from src.auth import AuthError, authenticate, change_password, initialize_configured_admin, register
from src.config import APP_TITLE, CLASS_CONFIDENCE_WARNING, LOGO_PATH
from src.database import AdminAuditLog, DatabaseUnavailableError, Experiment, User, database_diagnostic, init_database, session_scope
from src.image_validator import ValidationModelLoadError, load_validation_model
from src.model import load_prediction_model
from src.prediction import predict_attributes
from src.services import admin_stats, run_experiment, user_experiments
from src.runtime_secrets import read_secret
from src.ui import apply_styles, render_disclaimer, render_footer, render_hero, render_preview, render_results, render_validation_details

st.set_page_config(page_title=APP_TITLE, page_icon="🐟", layout="wide", initial_sidebar_state="collapsed")
logger = logging.getLogger(__name__)
try:
    init_database()
except DatabaseUnavailableError:
    # The detailed diagnostic is deliberately kept in server logs. Do not show
    # provider URLs, credentials, hostnames, or driver messages to visitors.
    diagnostic = database_diagnostic()
    if diagnostic.status == "external_database_configured":
        st.error("This client-testing prototype is configured for SQLite, but an external database URL is still set.")
        st.info("An operator must remove CATFISH_DATABASE_URL from Streamlit Cloud Secrets, then reboot the app.")
    else:
        st.error("The application SQLite database is temporarily unavailable. Registration, sign-in, and predictions are unavailable until it is restored.")
    st.stop()
apply_styles()


def bootstrap_configured_admin() -> None:
    """Run an idempotent, server-secret-based first-admin setup for this SQLite DB."""
    try:
        with session_scope() as session:
            result = initialize_configured_admin(
                session,
                read_secret("CATFISH_ADMIN_EMAIL", st.secrets),
                read_secret("CATFISH_ADMIN_INITIAL_PASSWORD", st.secrets),
            )
    except Exception as exc:
        # Never include secret values, hashes, or exception text in the log/UI.
        logger.warning("Administrator bootstrap failed: category=database_error exception=%s", type(exc).__name__)
        st.warning("The configured administrator could not be initialized. Existing accounts were left unchanged.")
        return
    logger.info("Administrator bootstrap result: category=%s", result.status)
    messages = {
        "incomplete_configuration": "Administrator setup is incomplete. Configure both administrator secrets.",
        "invalid_email": "Administrator setup has an invalid email configuration.",
        "weak_password": "Administrator setup requires an initial password of at least 8 characters.",
        "email_conflict": "Administrator setup conflicts with an existing account. Existing accounts were left unchanged.",
        "username_conflict": "Administrator setup conflicts with an existing account. Existing accounts were left unchanged.",
        "administrator_conflict": "An administrator already exists. Existing accounts were left unchanged.",
    }
    if result.status in messages:
        st.warning(messages[result.status])


bootstrap_configured_admin()
for k,v in {"auth_user_id":None,"attempts":0}.items(): st.session_state.setdefault(k,v)

def me():
    if not st.session_state.auth_user_id: return None
    with session_scope() as s: return s.get(User,st.session_state.auth_user_id)
def logout(): st.session_state.auth_user_id=None; st.session_state.attempts=0; st.rerun()
def signin():
    render_hero(LOGO_PATH); st.subheader("Sign in")
    with st.form("login"):
        who=st.text_input("Username or email"); password=st.text_input("Password",type="password"); send=st.form_submit_button("Sign in")
    if send:
        if st.session_state.attempts>=5: st.error("Too many attempts in this browser session."); return
        try:
            with session_scope() as s: user=authenticate(s,who,password)
            st.session_state.auth_user_id=user.id; st.session_state.attempts=0; st.rerun()
        except AuthError as exc: st.session_state.attempts+=1; st.error(str(exc))
def signup():
    render_hero(LOGO_PATH); st.subheader("Create account")
    with st.form("register"):
        n=st.text_input("Full name"); u=st.text_input("Username"); e=st.text_input("Email address"); p=st.text_input("Password",type="password"); c=st.text_input("Confirm password",type="password"); send=st.form_submit_button("Create account")
    if send:
        try:
            with session_scope() as s: register(s,n,u,e,p,c)
            st.success("Account created. You can now sign in.")
        except AuthError as exc: st.error(str(exc))
def predict(user):
    st.header("New prediction")
    source=st.radio("Image source",("Upload image","Use webcam"),horizontal=True)
    image=st.file_uploader("JPEG or PNG image",type=("jpg","jpeg","png")) if source=="Upload image" else st.camera_input("Take a fish photograph")
    keep=st.checkbox("Retain this image privately with this record",help="Optional. Retained images are not exposed through public URLs.")
    if image:
        data=image.getvalue(); render_preview(data,getattr(image,"name","Camera image"))
        if st.button("Analyse image",type="primary"):
            try:
                with st.status("Validating and analysing…",expanded=False):
                    with session_scope() as s: exp,val,result=run_experiment(s,user.id,data,validator=load_validation_model(),load_model_fn=load_prediction_model,predict_fn=predict_attributes,retain_image=keep)
                render_validation_details(val)
                if result: render_results(result,CLASS_CONFIDENCE_WARNING)
                elif exp.status=="FAILED": st.error("Inference failed and was recorded without prediction values.")
            except ValidationModelLoadError as exc:
                st.error(str(exc))
def history(user):
    st.header("Experiment history")
    with session_scope() as s: rows=user_experiments(s,user.id)
    data=[{"ID":x.id,"Date":x.submitted_at,"Status":x.status,"Stage":x.prediction.growth_stage if x.prediction else "—","Weight (g)":x.prediction.weight_g if x.prediction else None} for x in rows]
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
    if rows:
        x=next(x for x in rows if x.id==st.selectbox("Open experiment",[x.id for x in rows]))
        st.json({"validation":x.validation.reason if x.validation else None,"prediction":json.loads(x.prediction.probabilities_json) if x.prediction else None,"model":x.prediction.model_version.identifier if x.prediction else None,"processing_ms":x.processing_ms})
def profile(user):
    st.header("My profile")
    with st.form("profile"):
        n=st.text_input("Full name",user.full_name); e=st.text_input("Email",user.email); send=st.form_submit_button("Save profile")
    if send:
        with session_scope() as s: s.get(User,user.id).full_name=n.strip(); s.get(User,user.id).email=e.strip().lower()
        st.success("Profile updated.")
    with st.expander("Change password"):
        old=st.text_input("Current password",type="password"); new=st.text_input("New password",type="password"); conf=st.text_input("Confirm new password",type="password")
        if st.button("Update password"):
            try:
                with session_scope() as s: change_password(s.get(User,user.id),old,new,conf)
                st.success("Password updated.")
            except AuthError as exc: st.error(str(exc))
def admin(user,page):
    if user.role!="ADMIN": st.error("Administrator access required."); return
    with session_scope() as s:
        if page=="Admin overview":
            st.header("Administrator overview"); vals=admin_stats(s)
            for col,(k,v) in zip(st.columns(6),vals.items()): col.metric(k.replace("_"," ").title(),v)
            st.caption("Active means the account signed in during the preceding 30 days.")
        elif page=="Registered users":
            users=s.scalars(select(User).order_by(User.created_at.desc())).all(); frame=pd.DataFrame([{"ID":u.id,"Name":u.full_name,"Username":u.username,"Email":u.email,"Role":u.role,"Active":u.is_active,"Registered":u.created_at,"Experiments":len(u.experiments)} for u in users]); st.dataframe(frame,use_container_width=True,hide_index=True)
            target=st.selectbox("User",[u.id for u in users],format_func=lambda i:next(u.username for u in users if u.id==i)); chosen=s.get(User,target)
            if chosen.role=="USER" and st.button("Disable" if chosen.is_active else "Reactivate"):
                chosen.is_active=not chosen.is_active; s.add(AdminAuditLog(admin_user_id=user.id,action="account_status_changed",target_type="user",target_id=str(chosen.id),details=str(chosen.is_active))); st.success("Account updated.")
        elif page=="All experiments":
            exps=s.scalars(select(Experiment).order_by(Experiment.submitted_at.desc())).all(); q=st.text_input("Search username or experiment ID").lower(); status=st.selectbox("Status",["All","SUCCESS","REJECTED","FAILED"])
            rows=[{"Experiment ID":x.id,"User ID":x.user_id,"Username":x.owner.username,"Date":x.submitted_at,"Status":x.status,"Stage":x.prediction.growth_stage if x.prediction else "—","Weight (g)":x.prediction.weight_g if x.prediction else None,"Model":x.prediction.model_version.identifier if x.prediction else None} for x in exps]
            if q: rows=[r for r in rows if q in str(r["Experiment ID"]).lower() or q in r["Username"].lower()]
            if status!="All": rows=[r for r in rows if r["Status"]==status]
            df=pd.DataFrame(rows); st.dataframe(df,use_container_width=True,hide_index=True); st.download_button("Export CSV",df.to_csv(index=False),"experiments.csv","text/csv")
        elif page=="Experiment analytics":
            exps=s.scalars(select(Experiment).where(Experiment.status=="SUCCESS")).all(); data=[{"date":x.submitted_at.date(),"stage":x.prediction.growth_stage,"weight":x.prediction.weight_g,"user":x.owner.username} for x in exps]
            if not data: st.info("No successful predictions yet.")
            else:
                df=pd.DataFrame(data); st.caption("All values are model-generated estimates."); st.line_chart(df.groupby("date").size()); st.bar_chart(df.groupby("stage").size()); st.bar_chart(df.groupby("stage")["weight"].mean()); st.bar_chart(df.groupby("user").size())
        else:
            logs=s.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())).all(); st.dataframe(pd.DataFrame([{"Date":x.created_at,"Action":x.action,"Target":f"{x.target_type}:{x.target_id}","Details":x.details} for x in logs]),use_container_width=True)
user=me()
if not user:
    page=st.sidebar.radio("Navigation",["Welcome","Sign in","Create account"])
    if page=="Welcome": render_hero(LOGO_PATH); st.write("Sign in to securely run and retain catfish attribute experiments.")
    elif page=="Sign in": signin()
    else: signup()
else:
    if user.must_change_password:
        st.warning("You must change your initial password before accessing the application.")
        pages=["My profile","Logout"]
    else:
        pages=["Dashboard","New prediction","Experiment history","My profile","Logout"] if user.role=="USER" else ["Admin overview","Registered users","All experiments","Experiment analytics","Admin audit logs","My profile","Logout"]
    page=st.sidebar.radio("Navigation",pages)
    if page=="Logout": logout()
    elif page=="Dashboard":
        with session_scope() as s: records=user_experiments(s,user.id)
        st.header(f"Welcome, {user.full_name}"); a,b,c=st.columns(3); a.metric("Experiments",len(records)); b.metric("Member since",user.created_at.date().isoformat()); c.metric("Most recent",records[0].submitted_at.date().isoformat() if records else "—")
    elif page=="New prediction": predict(user)
    elif page=="Experiment history": history(user)
    elif page=="My profile": profile(user)
    else: admin(user,page)
render_disclaimer(); render_footer()
