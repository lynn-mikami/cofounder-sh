import os
import sys
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from browser_use import Agent, Controller

load_dotenv()

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

async def break_down_task(task: str, llm: ChatOllama) -> List[str]:
    """Use AI to break down the main task into smaller steps."""
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
        return [task]

async def generate_report(task: str, steps_completed: List[Dict[str, Any]], llm: ChatOllama) -> str:
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
    # Optional: Disable telemetry
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    
    # Optional: Set custom Ollama host
    if ollama_host := os.getenv('OLLAMA_HOST'):
        os.environ["OLLAMA_HOST"] = ollama_host

    if len(sys.argv) < 2:
        task = input("Please enter your task: ")
    else:
        task = " ".join(sys.argv[1:])

    # Initialize Ollama model
    model = ChatOllama(
        model="qwen2.5:32b-instruct-q4_K_M",  # You can change this to any available model
        num_ctx=32000,
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
        
        agent = Agent(
            task=step, 
            llm=model, 
            controller=controller
        )
        
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
    
    # Save report to file
    with open("execution_report.txt", "w") as f:
        f.write(report)
    print("\n✅ Report saved to execution_report.txt")

if __name__ == '__main__':
    asyncio.run(main())