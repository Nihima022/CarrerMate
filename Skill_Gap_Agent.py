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
class Skill_Gap_Recommendation(BaseModel):
    target_job:str
    user_skill:List[str]
    required_skill:List[str]
    missing_skill:List[str]
    recommendation_summary:str

@function_tool
def get_missing_skill(skill:str,job:str)->str:
    """Compare user skills with required skills for a target job and return missing skills in a simple readable format."""
    job_database={
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
    if target_job not in job_database:
        return "Job not found"

    required_skill=job_database[target_job]

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
     """,
    tools=[get_missing_skill],
    model= structured_model,
    output_type= Skill_Gap_Recommendation
)

async def main():
    queries=["I want to become Data engineer and I only know Python and SQL.Can you suggest me for improvement on this field?"]

    for query in queries:
        print("="*100)
        print("Query:",query)
        print("="*100)

        result=await Runner.run(skill_gap_agent,query)
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

        else:
            print("Failed")

set_tracing_disabled(True)

if __name__=="__main__":
    asyncio.run(main())