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
            if location.lower() not in job["location"].lower():
                continue

        if match_count>0:
            job_matching.append(job)

    if len(job_matching) == 0:
        return "No matching jobs found"

    return json.dumps(job_matching[0], indent=2)



job_finder_agent=Agent(
    name="Job search Tool",
    instructions="""You are a Job Finder Agent.
    1. Extract user skills from the query.
    2. Extract optional location if provided.
    3. Call the tool get_suitable_job ONLY ONCE.
    4. Use the tool result to generate the final answer.
    5. Do not create fake jobs.

    Return:
    - job title
    - company name
    - location
    - salary
    - basic requirements
    - recommendation summary""",
    model=structured_model,
    tools=[get_suitable_job],
    output_type= Job_Recommendation
)

async def main():
    queries=["I only know Python and SQL.Can you suggest me for this field.i am currently live in gulshan?",
             "I have strong skill of CSS,HTML and JavaScript. can you suggest me similar job based on these skills?"]

    for query in queries:
        print("="*100)
        print("Query:",query)
        print("="*100)

        result=await Runner.run(job_finder_agent,query)
        response=result.final_output
        print(response)
        print("="*100)
        print("Final Output:\n")

        if hasattr(response, "job_title"):
            print(f"Job Title: {response.job_title}")
            print(f"Company Name: {response.company_name}")
            print(f"Job Location: {response.location}")
            print(f"Salary: {response.salary}")

            print("Basic Requirements:")
            for i, skills in enumerate(response.basic_requirements, 1):
                print(f" {i}.{skills}")

            print(f"Recommendation Summary: {response.recommendation_summary}")

        else:
            print("Failed")

set_tracing_disabled(True)

if __name__ == "__main__":
    asyncio.run(main())
