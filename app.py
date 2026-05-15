import streamlit as st
from PIL import Image
import openai
import os
import json
import base64
import datetime
import io
from dotenv import load_dotenv
from supabase import create_client
import plotly.graph_objects as go
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer

load_dotenv()

st.set_page_config(
    page_title="MistakeMentor AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Styling ---
st.markdown("""
<style>
 .stApp {background: linear-gradient(180deg, #0F1117 0%, #1A1D24 100%); color: white;}
 .main-card {background: #1A1D24; padding: 20px; border-radius: 16px; border: 1px solid #2D3139; margin: 10px 0;}
 .stButton>button {background: linear-gradient(90deg, #7C3AED, #3B82F6); color: white; border-radius: 12px; padding: 12px 24px; border: none; font-weight: bold; width: 100%;}
 .stButton>button:hover {transform: scale(1.02);}
 .concept-tag {background: #7C3AED; padding: 6px 12px; border-radius: 20px; display: inline-block; font-size: 12px;}
 .difficulty-easy {color: #10B981;}.difficulty-med {color: #F59E0B;}.difficulty-hard {color: #EF4444;}
 .streak-fire {font-size: 48px; text-align: center;}
</style>
""", unsafe_allow_html=True)

# --- Clients ---
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# --- Session State ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'practice_qs' not in st.session_state:
    st.session_state.practice_qs = []
if 'practice_idx' not in st.session_state:
    st.session_state.practice_idx = 0

# --- Helpers ---
def get_user_profile(user_id):
    if not supabase: return None
    res = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
    return res.data if res.data else None

def update_streak(user_id):
    if not supabase: return 0
    profile = get_user_profile(user_id)
    today = datetime.date.today()

    if not profile:
        supabase.table('profiles').insert({
            'id': user_id,
            'streak': 1,
            'last_checkin': today.isoformat()
        }).execute()
        return 1

    last_checkin = datetime.date.fromisoformat(profile['last_checkin']) if profile['last_checkin'] else None

    if last_checkin == today:
        return profile['streak']
    elif last_checkin == today - datetime.timedelta(days=1):
        new_streak = profile['streak'] + 1
        supabase.table('profiles').update({
            'streak': new_streak,
            'last_checkin': today.isoformat()
        }).eq('id', user_id).execute()
        return new_streak
    else:
        supabase.table('profiles').update({
            'streak': 1,
            'last_checkin': today.isoformat()
        }).eq('id', user_id).execute()
        return 1

def get_streak(user_id):
    profile = get_user_profile(user_id)
    return profile['streak'] if profile else 0

def sm2_interval(repetitions, interval, ease_factor, quality):
    if quality < 3:
        repetitions = 0; interval = 1
    else:
        if repetitions == 0: interval = 1
        elif repetitions == 1: interval = 6
        else: interval = int(interval * ease_factor)
        repetitions += 1
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_review = datetime.date.today() + datetime.timedelta(days=interval)
    return repetitions, interval, ease_factor, next_review

def get_user_mistakes(user_id):
    if not supabase: return []
    res = supabase.table('mistakes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
    return res.data

def add_mistake(user_id, data):
    if not supabase: return
    supabase.table('mistakes').insert({
        'user_id': user_id,
        'image_url': data.get('image_url'),
        'question_text': data.get('question_text'),
        'explanation': data.get('explanation'),
        'concept': data.get('concept'),
        'difficulty': data.get('difficulty', 'medium'),
        'repetitions': 0,
        'interval': 1,
        'ease_factor': 2.5,
        'next_review': datetime.date.today().isoformat()
    }).execute()

def update_review(mistake_id, quality):
    if not supabase: return
    mistake = supabase.table('mistakes').select('*').eq('id', mistake_id).single().execute().data
    reps, interval, ef, next_review = sm2_interval(
        mistake['repetitions'], mistake['interval'], mistake['ease_factor'], quality
    )
    supabase.table('mistakes').update({
        'repetitions': reps, 'interval': interval, 'ease_factor': ef,
        'next_review': next_review.isoformat()
    }).eq('id', mistake_id).execute()

def get_due_reviews(user_id):
    if not supabase: return []
    today = datetime.date.today().isoformat()
    res = supabase.table('mistakes').select('*').eq('user_id', user_id).lte('next_review', today).execute()
    return res.data

def generate_practice_questions(concept, difficulty, count=5):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Generate {count} {difficulty} multiple choice questions for concept '{concept}'. Return JSON with key 'questions' containing array of objects with keys: question, options, answer, explanation"
            }],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)['questions']
    except Exception as e:
        st.error(f"GPT Error: {e}")
        return []

def generate_pdf(mistakes):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "MistakeMentor AI - Mistake Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated on: {datetime.date.today().strftime('%Y-%m-%d')}")
    y -= 30

    styles = getSampleStyleSheet()

    for i, m in enumerate(mistakes[:20], 1):
        if y < 100:
            c.showPage()
            y = height - 50

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{i}. Concept: {m['concept']}")
        y -= 20

        p = Paragraph(f"<b>Explanation:</b> {m['explanation']}", styles['Normal'])
        p.wrapOn(c, width - 100, height)
        p.drawOn(c, 50, y - 15)
        y -= p.height + 15

        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"Difficulty: {m['difficulty']} | Created: {m['created_at'][:10]}")
        y -= 25
        c.line(50, y, width - 50, y)
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer

# --- Auth ---
def login_signup():
    st.title("📚 MistakeMentor AI")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = user.user
                update_streak(user.user.id) # Daily check-in on login
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            try:
                user = supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created! Check email to verify.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

# --- Pages ---
def home_page():
    st.title("MistakeMentor AI")

    # Daily streak check-in
    current_streak = get_streak(st.session_state.user.id)
    if current_streak > 0:
        st.markdown(f'<div class="streak-fire">🔥 {current_streak} Day Streak!</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    due_count = len(get_due_reviews(st.session_state.user.id))
    mistakes = get_user_mistakes(st.session_state.user.id)

    with col1:
        top_concept = max(set([m['concept'] for m in mistakes]), key=[m['concept'] for m in mistakes].count) if mistakes else "N/A"
        st.markdown(f"""
        <div class="main-card">
            <p style="color: #9CA3AF; font-size: 12px;">Today's Focus</p>
            <h3>{top_concept}</h3>
            <p style="color: #EF4444;">{len(mistakes)} total mistakes</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("🔥 Streak", f"{current_streak} days")
    with col3:
        st.metric("📅 Due Reviews", due_count)

    if st.button("Scan Mistake"):
        st.session_state.page = "Scan"
        st.rerun()

    if due_count > 0:
        if st.button(f"Review {due_count} Due Mistakes"):
            st.session_state.page = "Review"
            st.rerun()

def scan_page():
    st.title("Scan Your Mistake")
    uploaded_file = st.camera_input("Take a photo of the wrong answer")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Scanned Question", use_column_width=True)

        if st.button("Analyze with AI"):
            with st.spinner("AI is analyzing..."):
                try:
                    buffered = uploaded_file.getvalue()
                    img_b64 = base64.b64encode(buffered).decode()

                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Explain why this answer is wrong in 2 lines, name the concept, and return JSON with keys: explanation, concept, difficulty"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                        }],
                        max_tokens=300
                    )

                    result = json.loads(response.choices[0].message.content)
                    st.session_state.last_scan = result

                    st.markdown(f"""
                    <div class="main-card">
                        <p style="color: #9CA3AF;">AI Explanation</p>
                        <p>{result['explanation']}</p>
                        <span class="concept-tag">Concept: {result['concept']}</span>
                        <span class="difficulty-{result['difficulty']}"> {result['difficulty'].title()}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    if col1.button("Save Mistake"):
                        add_mistake(st.session_state.user.id, {
                            'image_url': uploaded_file.name,
                            'question_text': 'Scanned from image',
                            'explanation': result['explanation'],
                            'concept': result['concept'],
                            'difficulty': result['difficulty']
                        })
                        st.success("Saved! Added to your review queue.")
                        update_streak(st.session_state.user.id)
                    if col2.button("Practice More"):
                        st.session_state.practice_qs = generate_practice_questions(
                            result['concept'], result['difficulty']
                        )
                        st.session_state.practice_idx = 0
                        st.session_state.page = "Practice"
                        st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Add OPENAI_API_KEY in secrets to enable AI")

def practice_page():
    st.title("Practice Mode")

    if not st.session_state.practice_qs:
        st.warning("No practice questions loaded")
        return

    q = st.session_state.practice_qs[st.session_state.practice_idx]
    st.subheader(f"Q{st.session_state.practice_idx + 1}/{len(st.session_state.practice_qs)}")
    st.write(q['question'])

    choice = st.radio("Choose answer:", q['options'], key=f"q_{st.session_state.practice_idx}")

    if st.button("Submit"):
        if choice == q['answer']:
            st.success("Correct!")
            st.write(f"**Explanation:** {q['explanation']}")
            if st.session_state.practice_idx < len(st.session_state.practice_qs) - 1:
                st.session_state.practice_idx += 1
                st.rerun()
            else:
                st.balloons()
                st.success("Practice set complete!")
                update_streak(st.session_state.user.id)
                st.session_state.practice_idx = 0
        else:
            st.error(f"Wrong. Correct answer: {q['answer']}")
            st.write(f"**Explanation:** {q['explanation']}")

def review_page():
    st.title("Spaced Repetition Reviews")
    due_mistakes = get_due_reviews(st.session_state.user.id)

    if not due_mistakes:
        st.success("No reviews due today! 🎉")
        return

    mistake = due_mistakes[0]
    st.subheader(f"Concept: {mistake['concept']}")
    st.write(mistake['explanation'])

    st.write("How well did you remember this?")
    col1, col2, col3, col4 = st.columns(4)

    if col1.button("0 - Forgot"):
        update_review(mistake['id'], 0); st.rerun()
    if col2.button("2 - Hard"):
        update_review(mistake['id'], 2); st.rerun()
    if col3.button("4 - Easy"):
        update_review(mistake['id'], 4); st.rerun()
    if col4.button("5 - Perfect"):
        update_review(mistake['id'], 5); st.rerun()

def dashboard_page():
    st.title("Weak Spot Map")
    mistakes = get_user_mistakes(st.session_state.user.id)

    if not mistakes:
        st.info("No mistakes yet. Start scanning!")
        return

    concepts = {}
    for m in mistakes:
        c = m['concept']
        concepts[c] = concepts.get(c, 0) + 1

    fig = go.Figure(data=[go.Pie(labels=list(concepts.keys()), values=list(concepts.values()),
                                 hole=.3, marker_colors=['#7C3AED', '#3B82F6', '#EF4444', '#F59E0B', '#10B981'])])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)

    for concept, count in sorted(concepts.items(), key=lambda x: x[1], reverse=True):
        rate = min(100, count * 10)
        color = "#EF4444" if rate > 70 else "#F59E0B" if rate > 40 else "#10B981"
        st.markdown(f"""
        <div class="main-card">
            <h4>{concept}</h4>
            <div style="background: #2D3139; height: 8px; border-radius: 4px;">
                <div style="background: {color}; width: {rate}%; height: 8px; border-radius: 4px;"></div>
            </div>
            <p style="color: {color}; margin-top: 8px;">{count} mistakes • {rate}% error rate</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export to CSV"):
            df = pd.DataFrame(mistakes)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "mistakes.csv", "text/csv")

    with col2:
        if st.button("Export to PDF"):
            pdf_buffer = generate_pdf(mistakes)
            st.download_button("Download PDF", pdf_buffer, "mistakes_report.pdf", "application/pdf")

# --- Main App ---
if not st.session_state.user and supabase:
    login_signup()
else:
    if not supabase:
        st.warning("Running in demo mode. Add SUPABASE_URL and SUPABASE_KEY to enable persistence.")

    st.sidebar.title("📚 MistakeMentor AI")
    if st.session_state.user:
        streak = get_streak(st.session_state.user.id)
        st.sidebar.write(f"Logged in as: {st.session_state.user.email}")
        st.sidebar.write(f"🔥 Streak: {streak} days")
        if st.sidebar.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    if 'page' not in st.session_state:
        st.session_state.page = "Home"

    page = st.sidebar.radio("Navigate", ["Home", "Scan", "Practice", "Review", "Dashboard"],
                            index=["Home", "Scan", "Practice", "Review", "Dashboard"].index(st.session_state.page))

    if page == "Home": home_page()
    elif page == "Scan": scan_page()
    elif page == "Practice": practice_page()
    elif page == "Review": review_page()
    elif page == "Dashboard": dashboard_page()
