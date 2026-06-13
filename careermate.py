import os
import json
import asyncio

from agents import Agent
from agents import Tool
from agents import OpenAIChatCompletionsModel
from agents import Runner
from agents import set_tracing_disabled
from agents import function_tool

from dotenv import load_dotenv

from openai import AsyncOpenAI

from pydantic import Field
from pydantic import BaseModel

from typing import Optional
from typing import List

#API Key to access openai model
load_dotenv()

llm_base_url=os.getenv("BASE_URL")
llm_api_key=os.getenv("API_KEY")
llm_model_name=os.getenv("MODEL_NAME")

if not llm_base_url or not llm_api_key or not llm_model_name:
    raise ValueError("base_url or api_key or model_name is missing")

#Structured Model
client=AsyncOpenAI(
    base_url=llm_base_url,
    api_key=llm_api_key
)

structured_model=OpenAIChatCompletionsModel(
    model=llm_model_name,
    openai_client=client
)

#Create BaseModel for all agent
#1.Skill Gap Agent
class Skill_Recommendation(BaseModel):
    target_job:str
    user_skill:List[str]
    required_skill:List[str]
    missing_skill:List[str]
    recommendation_summary:str

@function_tool
def get_missing_skill(skill:str,job:str)->str:
    """Compare user skills with required skills for a target job and return missing skills in a simple readable format."""
    role_database={
        "data analyst":["Python", "Machine Learning","Power Bi","Excel","Power Query"],
        "data scientist": ["Excel", "SQL", "Tableau", "Statistics"],
        "web developer": ["HTML", "CSS", "JavaScript", "React"],
        "ai engineer": ["Python", "Deep Learning", "Pytorch", "Machine Learning"],
        "data engineer": ["Python", "SQL", "ETL", "Apache Spark", "Airflow"]
    }

    user_skill=skill.split(",")
    user_skill_list=[]
    for s in user_skill:
        skills=s.strip().lower()
        user_skill_list.append(skills)


    target_job=job.lower()
    if target_job not in role_database:
        return "Job not found"

    required_skill=role_database[target_job]

    missing_skill=[]
    for skill in required_skill:
        if skill not in user_skill_list:
            missing_skill.append(skill)

    return f"you want to be {target_job} and you have a good knowledge of {user_skill} but for this job the required skills are {required_skill} and u should be improved on {missing_skill}"

skill_gap_agent=Agent(
    name="Skill founder",
    instructions="""
    Extract:
       1. target job
       2. user skills

       Then call the tool get_missing_skill.
       Return:
       - user skill
       - target job
       - missing skill
       - required skill
       - recommendation summary
       Do not generate answer that is not included in your database.
     """,
    tools=[get_missing_skill],
    model= structured_model,
    output_type= Skill_Recommendation
)

#Job Finder Agent
class Job_Recommendation(BaseModel):
    job_title:str
    company_name:str
    location:str
    basic_requirements: List[str]
    salary:str
    recommendation_summary:str

@function_tool
def get_suitable_job(skill:str,location:Optional[str]=None)->str:
    """
    Suggest suitable jobs based on user skills and optional location.
    Returns top matching jobs only.
    """
    job_database=[
        {
            "job_title":"AI Engineer",
            "company_name":"Tesco",
            "location":"Mohakhali,Dhaka",
            "basic_requirements":["Python","Keras","Pandas","Airflow"],
            "salary":"50K-80K BDT",
        },
        {
            "job_title": "Data Engineer",
            "company_name": "Brain Station 23",
            "location": "Banani, Dhaka",
            "basic_requirements": ["Python","SQL","ETL","Apache Spark","Airflow","Data Warehousing"],
            "salary": "70K-120K BDT",
        },
        {
            "job_title": "Data Analyst",
            "company_name": "Grameenphone",
            "location": "Gulshan, Dhaka",
            "basic_requirements": ["Excel","SQL","Power BI","Python","Data Visualization","Python"],
            "salary": "45K-75K BDT",
        },
        {
            "job_title": "Machine Learning Engineer",
            "company_name": "Pathao",
            "location": "Tejgaon, Dhaka",
            "basic_requirements": ["Python","Scikit-learn","TensorFlow","Deep Learning","Pandas"],
            "salary": "80K-150K BDT",
        },
        {
            "job_title": "Backend Developer",
            "company_name": "BJIT",
            "location": "Niketon, Dhaka",
            "basic_requirements": ["Python","Django","REST API","PostgreSQL","Git"],
            "salary": "60K-100K BDT",
        },
        {
            "job_title": "Frontend Developer",
            "company_name": "Enosis Solutions",
            "location": "Mirpur DOHS, Dhaka",
            "basic_requirements": ["HTML","CSS","JavaScript","React","Tailwind CSS"],
            "salary": "50K-90K BDT",
        },
        {
            "job_title": "Mobile App Developer",
            "company_name": "ShopUp",
            "location": "Mohakhali, Dhaka",
            "basic_requirements": ["Flutter", "Dart", "Firebase", "REST API", "Git"],
            "salary": "60K-110K BDT",
        }
    ]

    user_skill=skill.split(",")
    user_skill_list=[]
    for s in user_skill:
        user_skill_list.append(s.strip().lower())

    job_matching=[]
    for job in job_database:
        required_skill=[]
        for skill in job["basic_requirements"]:
            required_skill.append(skill.strip().lower())

        match_count=0

        for requirements in user_skill_list:
            if requirements in required_skill:
                match_count=match_count+1

        if location is not None:
            if location not in job["location"].lower():
                continue

        if match_count>0:
            job_matching.append(job)


    return json.dumps(job_matching[0], indent=2)



job_finder_agent=Agent(
    name="Job search Tool",
    instructions="""You are a Job Finder Agent.
    Your job is to:
    1. Read the user's skills and optional location
    2. Return result from database:
    - job title
    - company name
    - location
    - salary
    - basic requirements
    - recommendation summary
    If no jobs are found, clearly say no matching jobs found.
    Use ONLY the exact tool output. Do not modify company names, salary, or locations.""",
    model=structured_model,
    tools=[get_suitable_job],
    output_type= Job_Recommendation
)

#Course Recommendation Agent
class Course_Recommendation(BaseModel):
    course_title:str
    platform:str
    link:str
    skill_development:List[str]
    price:str
    recommendation_summary:str

@function_tool
def get_suitable_course(skill:str)->str:
    """ Suggest suitable course based on missing_skill"""
    course_database=[
        {
            "course_title": "Python for Data Science",
            "platform": "Coursera",
            "link": "https://www.coursera.org/specializations/python",
            "skill_development": ["Python", "Pandas", "Data Analysis"],
            "price": "Free"
        },
        {
            "course_title": "SQL & Database Management",
            "platform": "Coursera",
            "link": "https://www.coursera.org/learn/sql-for-data-science",
            "skill_development": ["SQL", "PostgreSQL", "Data Warehousing"],
            "price": "Free"
        },
        {
            "course_title": "ETL and Data Pipelines with Airflow",
            "platform": "Udemy",
            "link": "https://www.udemy.com/course/the-ultimate-hands-on-course-to-master-apache-airflow",
            "skill_development": ["Airflow", "ETL", "Data Pipelines"],
            "price": "1,500 BDT"
        },
        {
            "course_title": "Big Data with Apache Spark",
            "platform": "Udemy",
            "link": "https://www.udemy.com/course/apache-spark-for-beginners",
            "skill_development": ["Apache Spark", "Big Data", "Data Engineering"],
            "price": "1,200 BDT"
        },
        {
            "course_title": "Machine Learning with Python",
            "platform": "Coursera",
            "link": "https://www.coursera.org/specializations/machine-learning-introduction",
            "skill_development": ["Machine Learning", "Scikit-learn", "Python"],
            "price": "18,000 BDT"
        },
        {
            "course_title": "Frontend Development Bootcamp",
            "platform": "Udemy",
            "link": "https://www.udemy.com/course/react-the-complete-guide-incl-redux",
            "skill_development": ["HTML", "CSS", "JavaScript", "React"],
            "price": "13,000 BDT"
        }
    ]

    user_skill=skill.split(",")
    user_skill_list=[]
    for s in user_skill:
        user_skill_list.append(s.strip().lower())

    course_matching=[]
    for course in course_database:
        course_skill=[]
        for r in course["skill_development"]:
            course_skill.append(r.strip().lower())

        match_count=0

        for requirement in user_skill_list:
            if requirement in course_skill:
                match_count=match_count+1

        if match_count>0:
            course_matching.append(course)

    return json.dumps(course_matching[0], indent=2)

course_recommendation_agent=Agent(
    name="Course Recommendation Tool",
    instructions="""You are a Course Recommendation Agent.
    Follow strictly:
    1. Call get_suitable_course ONLY ONCE.
    2. Use the tool result directly.
    3. Do NOT call the tool again after receiving output.
    4. If tool returns no courses, say "No suitable courses found".
    5. Do NOT modify course title, platform, or link.
    After tool response:
    → immediately format final answer
    → stop reasoning""",
    model=structured_model,
    tools=[get_suitable_course],
    output_type= Course_Recommendation
)

#4.Conversation Agent
class Controll_Agent(BaseModel):
    candidate_skill:List[str]
    suitable_job:str
    skill_requirement:List[str]
    expected_salary:str
    suitable_location:str
    skill_to_improve:List[str]
    suitable_course:str
    course_price:str

conversation_agent=Agent(
    name="Conversation Tool",
    instructions="""
    You are the main controller of CareerMate.

    Your responsibilities:
    1. Understand user intent
    2. Route requests to the correct specialist agent
    3. Never generate fake job/course/skill data
    4. Use handoff to specialist agents

    Routing Rules:
    - Career goal → Skill Gap Agent
    - Job search → Job Finder Agent
    - Learning request → Course Recommendation Agent
    """,
    model=structured_model,
    handoffs=[skill_gap_agent,job_finder_agent,course_recommendation_agent],
    output_type= Controll_Agent
)

async def main():
    queries=["1.I want to become Data engineer and I only know Python and SQL.Can you suggest me for improvement on this field?",
             "2.I have strong skill of CSS,HTML and JavaScript. can you suggest me similar job based on these skills?",
             "3.I want to become a Machine Learning Engineer. I only know Python. Can you suggest me some courses ?",
             "4.I know Flutter, Dart, Firebase. Find me a suitable job",
             "5.I want to become a AI Engineer. Currently I know Python and SQL.Can you tell me what skills I am missing.",
             "6.I only know html.is it possible for me to get a high paid job?.",
             "7.Suggest courses for machine learning which price is not so high",
             "8.Suggest me random courses to compete with this world. I only know python"]

    for query in queries:
        print("="*100)
        print("Query:",query)
        print("="*100)

        result=await Runner.run(conversation_agent,query)
        response=result.final_output
        print(response)
        print("="*100)
        print("Final Output:\n")

        if hasattr(response,"user_skill"):
            print(f"User Skill: {response.user_skill}")
            print(f"Target Job: {response.target_job}")

            print("Required Skills:")
            for i,skills in enumerate(response.required_skill,1):
                print(f" {i}.{skills}")

            print("Missing Skills:")
            for i, skills in enumerate(response.missing_skill, 1):
                print(f" {i}.{skills}")

            print(f"Summary: {response.recommendation_summary}")

        elif hasattr(response,"job_title"):
            print(f"Job Title: {response.job_title}")
            print(f"Company Name: {response.company_name}")
            print(f"Job Location: {response.location}")
            print(f"Salary: {response.salary}")

            print("Basic Requirements:")
            for i,skills in enumerate(response.basic_requirements,1):
                print(f" {i}.{skills}")

            print(f"Recommendation Summary: {response.recommendation_summary}")

        elif hasattr(response,"skill_development"):
            print(f"Course Title: {response.course_title}")
            print(f"Platform: {response.platform}")
            print(f"Link: {response.link}")
            print(f"Price: {response.price}")

            print("Gained Knowledge:")
            for i,skills in enumerate(response.skill_development,1):
                print(f" {i}.{skills}")

            print(f"Recommendation Summary:{response.recommendation_summary}")

        elif hasattr(response,"candidate_skill"):
            print(f"Candidate Skill: {response.candidate_skill}")
            print(f"Suitable Job: {response.suitable_job}")
            print(f"Skills Requirement:{response.skill_requirement}")
            print(f"Suitable Location: {response.suitable_location}")
            print(f"Expected Salary: {response.expected_salary}")
            print(f"Skill To Improve:{response.skill_to_improve}")
            print(f"Suitable Course: {response.suitable_course}")
            print(f"Course Price: {response.course_price}")

        else:
            print("Failed")

set_tracing_disabled(True)

if __name__=="__main__":
    asyncio.run(main())
    





