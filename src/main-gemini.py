#src/main-gemini.py

import os
import sys
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr

from browser_use import ActionResult, Agent, Controller

load_dotenv()

# Validate and get API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GEMINI_API_KEY is not set')

class TaskBreakdown(BaseModel):
    steps: List[str]

class ExecutionReport(BaseModel):
    task: str
    steps_completed: List[Dict[str, Any]]
    summary: str
    success: bool
    recommendations: List[str]

class UniversalController(Controller):
    def __init__(self):
        super().__init__(output_model=None)

async def break_down_task(task: str, llm: ChatGoogleGenerativeAI) -> List[str]:
    """Use Gemini to break down the main task into smaller steps."""
    prompt = f"""
    Break down the following task into specific, executable steps:
    "{task}"
    
    Provide the steps as a simple JSON array of strings. Each step should be clear and actionable.
    Example: ["Open browser", "Navigate to website", "Click login"]
    """
    
    response = await llm.ainvoke(prompt)
    try:
        steps = json.loads(response.content)
        steps = [str(step) if isinstance(step, str) else step.get('step', str(step)) for step in steps]
        return steps
    except:
        return [task]  # Fallback to single task if parsing fails

async def generate_report(task: str, steps_completed: List[Dict[str, Any]], llm: ChatGoogleGenerativeAI) -> str:
    """Generate context-aware reports using dynamic prompting."""
    
    analysis_prompt = f"""
    TASK: {task}
    DATA: {json.dumps(steps_completed, indent=2)}

    1. What type of analysis is needed here?
    2. What are the most important aspects to focus on?
    3. How should the information be structured for maximum value?

    Provide a reporting framework specifically designed for this task.
    Include section headers and what each section should contain.
    """
    
    structure = await llm.ainvoke(analysis_prompt)
    
    report_prompt = f"""
    TASK: {task}
    DATA: {json.dumps(steps_completed, indent=2)}
    STRUCTURE: {structure.content}

    Generate a detailed report following this exact structure.
    Focus on concrete findings and actual data.
    Use → for bullet points, no markdown formatting.
    Include real numbers and specific examples.
    """
    
    response = ""
    async for chunk in llm.astream(report_prompt):
        print(chunk.content, end="", flush=True)
        response += chunk.content
    print("\n")
    return response

async def main():
    # Get task from command line arguments
    if len(sys.argv) < 2:
        task = input("Please enter your task: ")
    else:
        task = sys.argv[1]
    
    # Initialize Gemini model
    model = ChatGoogleGenerativeAI(
        model='gemini-2.0-flash-exp',
        api_key=SecretStr(api_key),
        temperature=0.7
    )
    controller = UniversalController()
    
    # Break down the task
    print("\n🔄 Breaking down the task...")
    steps = await break_down_task(task, model)
    print("\n📝 Task breakdown:")
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")
    
    # Execute each step
    steps_completed = []
    print("\n⚡ Executing steps...")
    for i, step in enumerate(steps, 1):
        print(f"\n▶️ Step {i}: {step}")
        agent = Agent(task=step, llm=model, controller=controller)
        history = await agent.run()
        
        step_result = {
            "step": step,
            "result": history.final_result(),
            "success": history.final_result() is not None
        }
        steps_completed.append(step_result)
        
        # Show immediate feedback
        status = "✅" if step_result["success"] else "❌"
        print(f"{status} Completed")
    
    # Generate report
    print("\n📊 Generating execution report...\n")
    report = await generate_report(task, steps_completed, model)

if __name__ == '__main__':
    asyncio.run(main())