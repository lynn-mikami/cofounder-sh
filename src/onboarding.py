import asyncio
import os
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller

async def analyze_startup(urls: List[str], llm: ChatOpenAI) -> str:
    """Analyze startup based on webpage content."""
    
    controller = Controller(output_model=None)
    content = []
    
    for url in urls.split(','):
        task = f"Visit {url.strip()} and extract key information about the company"
        agent = Agent(task=task, llm=llm, controller=controller)
        history = await agent.run()
        if history.final_result():
            content.append(history.final_result())
    
    prompt = """
    You are an experienced Venture Capitalist analyzing a startup.
    Based on the following information, create a detailed analysis in markdown format:
    
    CONTENT:
    {content}
    
    Analyze the following aspects:
    1. Product Overview
    2. Market Opportunity
    3. Competitive Differentiation
    4. Traction Indicators
    5. Risks
    6. Investment Considerations
    
    Format as a professional VC analysis document with clear sections and bullet points.
    """
    
    response = await llm.ainvoke(prompt.format(content="\n".join(content)))
    return response.content

async def main():
    load_dotenv()
    
    print("🚀 Welcome to Startup Analyzer!")
    print("\nPlease enter the URLs related to the startup (comma-separated):")
    urls = input("> ")
    
    model = ChatOpenAI(
        model='gpt-4o',
        streaming=True,
        temperature=0.7
    )
    
    print("\n📊 Analyzing startup data...")
    analysis = await analyze_startup(urls, model)
    
    # Save analysis to startup.md
    with open('startup.md', 'w') as f:
        f.write(analysis)
    
    print("\n✅ Analysis complete! Saved to startup.md")
    print("\nNow you can use the main script to analyze trends and generate reports!")

if __name__ == "__main__":
    asyncio.run(main())