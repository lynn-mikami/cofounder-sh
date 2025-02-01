import os
import sys
import asyncio
import json
from typing import List, Dict, Any
from typing_extensions import Annotated

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from browser_use import ActionResult, Agent, Controller

load_dotenv()

console = Console()

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

async def with_progress(description: str, coro):
    """Wrapper to show animated progress during async operations"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)
        result = await coro
        progress.update(task, completed=True)
        return result

async def break_down_task(task: str, llm: ChatOpenAI) -> List[str]:
    """Use AI to break down the main task into smaller steps."""
    prompt = f"""
    TASK ANALYSIS FRAMEWORK:
    Analyze and break down: "{task}"

    RULES FOR BREAKING DOWN TASKS:
    1. Each step must target ONE website and visit it ONLY ONCE
    2. Combine ALL actions for a website into single step (navigation, clicks, etc.)
    3. If task can be completed on one website, use SINGLE STEP
    4. Never split actions for same website across multiple steps
    5. Include all necessary actions for target site in one step
    6. Remove redundant navigation (assume browser is already open)
    7. Maximum 3 steps unless absolutely necessary

    GOOD EXAMPLE for "What's trending on Hacker News today":
    ["Navigate to news.ycombinator.com, click 'newest' link, collect first 10 headlines"]

    BAD EXAMPLE (multiple site visits):
    ["Go to Hacker News", "Return to Google", "Check Reddit"]

    OUTPUT FORMAT: 
    ["step 1", "step 2", ...]
    """
    
    # Create a panel for the breakdown process
    breakdown_panel = Panel("", title="🧠 Breaking Down Task", border_style="blue")
    response = ""
    
    # Use Live display for dynamic updates
    with Live(breakdown_panel, refresh_per_second=4) as live:
        async for chunk in llm.astream(prompt):
            response += chunk.content
            # Update panel content with accumulated response
            breakdown_panel.renderable = Text(response, style="cyan")
    
    try:
        steps = json.loads(response)
        steps = [str(step) if isinstance(step, str) else step.get('step', str(step)) for step in steps]
        return steps
    except:
        return [task]

async def generate_report(task: str, steps_completed: List[Dict[str, Any]], llm: ChatOpenAI) -> str:
    """Generate focused task report with actionable insights."""
    
    report_prompt = f"""
    TASK: {task}
    RAW_DATA: {json.dumps(steps_completed, indent=2)}

    CREATE 3-PART REPORT THAT IS 1000 WORDS MINIMIUM:
    
    1. TRENDS SUMMARY: 
    - Bullet list of key findings
    - Top 3-5 notable items
    
    2. STARTUP RELEVANCE:
    - 1 paragraph: Why this matters for cofounder.sh
    - Potential opportunities/threats
    
    3. MARKETING STRATEGIES:
    - 3 actionable tactics to leverage trends
    - 2 conversation starters for social media
    - 1 quick win implementation idea

    FORMATTING RULES:
    - No markdown or section headers
    - Maximum 15 lines total
    - Plain text with • bullets
    - Startup context: We automate technical tasks
    - Keep language casual but professional
    """

    report_panel = Panel("", title="🔍 Trend Analysis", border_style="blue")
    response = ""
    
    with Live(report_panel, refresh_per_second=10) as live:
        async for chunk in llm.astream(report_prompt):
            response += chunk.content
            report_panel.renderable = Text(response, style="cyan")
    
    return response

async def main():
    # Show welcome banner
    console.print(Panel.fit(
        "[bold blue]Welcome to Cofounder.sh AI Assistant[/]\n"
        "[cyan]Let me help you accomplish your task![/]",
        border_style="blue"
    ))

    # Get task from command line arguments
    if len(sys.argv) < 2:
        console.print("\n🤖 Please enter your task:", style="cyan")
        task = input()
    else:
        task = sys.argv[1]
    
    # Initialize AI model
    model = ChatOpenAI(
        model='gpt-4o',
        streaming=True,
        temperature=0.7
    )
    controller = UniversalController()
    
    # Break down the task
    steps = await break_down_task(task, model)
    
    console.print("\n📋 Task Breakdown:", style="bold blue")
    for i, step in enumerate(steps, 1):
        console.print(f"{i}. {step}", style="cyan")
    
    # Execute each step
    steps_completed = []
    console.print("\n⚡ Executing steps...", style="bold blue")
    
    for i, step in enumerate(steps, 1):
        console.print(f"\n▶️ Step {i}: {step}", style="yellow")
        agent = Agent(task=step, llm=model, controller=controller)
        
        history = await with_progress(f"Executing step {i}...", agent.run())
        
        step_result = {
            "step": step,
            "result": history.final_result(),
            "success": history.final_result() is not None
        }
        steps_completed.append(step_result)
        
        # Show immediate feedback with emoji
        status = "✅" if step_result["success"] else "❌"
        style = "green" if step_result["success"] else "red"
        console.print(f"{status} Step {i} completed", style=style)
    
    # Generate report
    console.print("\n📊 Final Report", style="bold blue")
    report = await generate_report(task, steps_completed, model)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n❌ Operation cancelled by user", style="red")
    except Exception as e:
        console.print(f"\n\n❌ Error: {str(e)}", style="red")
    finally:
        console.print("\n👋 Thank you for using Cofounder.sh!", style="cyan")