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

        if match_count > 0:
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

async def main():
    queries=["I want to become Data engineer and I only know Python and SQL.Can you suggest me for improvement on this field?",
             "I have strong skill of CSS,HTML and JavaScript. can you suggest me similar job based on these skills?"]

    for query in queries:
        print("="*100)
        print("Query:",query)
        print("="*100)

        result=await Runner.run(course_recommendation_agent,query)
        response=result.final_output
        print(response)
        print("="*100)
        print("Final Output:\n")

        if hasattr(response, "skill_development"):
            print(f"Course Title: {response.course_title}")
            print(f"Platform: {response.platform}")
            print(f"Link: {response.link}")
            print(f"Price: {response.price}")
            print("Gained Knowledge:")

            for i, skills in enumerate(response.skill_development, 1):
                print(f" {i}.{skills}")

            print(f"Recommendation Summary:{response.recommendation_summary}")

        else:
            print("Failed")

set_tracing_disabled(True)

if __name__ == "__main__":
    asyncio.run(main())