import streamlit as st
import asyncio
from datetime import datetime

from careermate import conversation_agent
from agents import Runner

# Page Config
st.set_page_config(
    page_title="CareerMate",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css("style.css")

# Header
st.markdown(
    '''
    <div class="main-title">
        📚 
        <span class="career-text">CareerMate</span> 
        🎓
    </div>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Jobs • Skills • Courses • Career Growth</div>',
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.title("Career Example Panel")

    # Current Date
    st.markdown("### 📅 Current Date")
    st.info(f"{datetime.now().strftime('%d %B %Y')}")

    st.markdown("---")

    # Example Queries
    st.markdown("### 💡 Example Queries")

    example_queries = [
        "I want to become a Data Engineer and I know Python and SQL",
        "Find jobs for HTML, CSS and JavaScript",
        "Suggest Machine Learning courses under 5000 BDT",
        "What skills do I need for AI Engineer?",
        "I know Flutter, Dart and Firebase. Find me jobs."
    ]

    for query in example_queries:
        st.code(query, language="text")

    st.markdown("---")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display old chats
for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content, unsafe_allow_html=True)

# Chat Input
prompt = st.chat_input("Ask CareerMate anything...")

# Agent Runner
async def run_agent(query):
    result = await Runner.run(conversation_agent, query)
    return result.final_output

# Main Logic
if prompt:
    st.session_state.messages.append(("user", prompt))

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🚀 Building your career roadmap..."):

            try:
                response = asyncio.run(run_agent(prompt))

                # Skill Gap UI
                if hasattr(response, "target_job"):
                    missing = ", ".join(response.missing_skill)
                    required = ", ".join(response.required_skill)

                    skill_html = f"""
                    <div class="glass-card">
                      <h2>🎯 Skill Gap Analysis</h2>
                      <p><b>Target Job:</b> {response.target_job}</p>
                      <p><b>Your Skills:</b> {", ".join(response.user_skill)}</p>
                      <p><b>Required Skills:</b> {required}</p>
                      <p><b>Missing Skills:</b> {missing}</p>
                      <p><b>Summary:</b> {response.recommendation_summary}</p>
                    </div>
                    """

                    st.markdown(skill_html, unsafe_allow_html=True)
                    st.session_state.messages.append(("assistant", skill_html))

                # Job Recommendation UI
                elif hasattr(response, "job_title"):
                    requirements = ", ".join(response.basic_requirements)

                    job_html = f"""
                    <div class="glass-card">
                      <h2>💼 Job Recommendation</h2>
                      <div class="job-card">
                        <h3>{response.job_title}</h3>
                        <hr>
                        <p><b>Company:</b> {response.company_name}</p>
                        <p><b>Location:</b> {response.location}</p>
                        <p><b>Salary:</b> {response.salary}</p>
                        <p><b>Requirements:</b> {requirements}</p>
                        <p><b>Summary:</b> {response.recommendation_summary}</p>
                      </div>
                    </div>
                    """

                    st.markdown(job_html, unsafe_allow_html=True)
                    st.session_state.messages.append(("assistant", job_html))

                # Course Recommendation UI
                elif hasattr(response, "course_title"):
                    skills = ", ".join(response.skill_development)

                    course_html = f"""
                    <div class="glass-card">
                      <h2>📚 Course Recommendation</h2>
                      <div class="course-card">
                        <h3>{response.course_title}</h3>
                        <hr>
                        <p><b>Platform:</b> {response.platform}</p>
                        <p><b>Price:</b> {response.price}</p>
                        <p><b>Skills:</b> {skills}</p>
                        <p><b>Link:</b> {response.link}</p>
                        <p><b>Summary:</b> {response.recommendation_summary}</p>
                      </div>
                    </div>
                    """

                    st.markdown(course_html, unsafe_allow_html=True)
                    st.session_state.messages.append(("assistant", course_html))

                else:
                    st.write(response)
                    st.session_state.messages.append(("assistant", str(response)))

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")