#!/usr/bin/env python3
"""
Haggle Service Marketplace - Interactive CLI

Run with: 
  python cli.py              # Interactive mode
  python cli.py --demo       # Demo mode (no input required)
"""

import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint

from services.grok_llm import infer_task, generate_clarifying_questions
from services.grok_search import search_providers
from schemas import Job, JobStatus, ClarifyingQuestion
from db.models import init_db, SessionLocal, Provider
import uuid

console = Console()

# Demo mode flag
DEMO_MODE = "--demo" in sys.argv


async def main():
    """Interactive CLI for the Haggle Service Marketplace."""
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🔧 HAGGLE SERVICE MARKETPLACE[/bold cyan]\n"
        "[dim]Find the best service providers for your needs[/dim]",
        border_style="cyan"
    ))
    console.print("\n")
    
    if DEMO_MODE:
        console.print("[bold magenta]🎬 RUNNING IN DEMO MODE[/bold magenta]\n")
    
    # Initialize database
    init_db()
    
    # ========== STEP 1: Get user input ==========
    console.print("[bold yellow]📝 STEP 1: Tell us what you need[/bold yellow]\n")
    
    if DEMO_MODE:
        query = "fix my leaky faucet"
        zip_code = "95126"
        price_input = "200"
        date_needed = "2025-12-15"
        console.print(f"[cyan]Query:[/cyan] {query}")
        console.print(f"[cyan]ZIP Code:[/cyan] {zip_code}")
        console.print(f"[cyan]Budget:[/cyan] ${price_input}")
        console.print(f"[cyan]Date Needed:[/cyan] {date_needed}")
    else:
        query = Prompt.ask("[cyan]What do you need help with?[/cyan]")
        zip_code = Prompt.ask("[cyan]Your ZIP code[/cyan]", default="95126")
        price_input = Prompt.ask("[cyan]Your budget (dollar amount or 'no_limit')[/cyan]", default="250")
        date_needed = Prompt.ask("[cyan]When do you need this done? (YYYY-MM-DD)[/cyan]", default="2025-12-15")
    
    # Parse price
    price_limit = "no_limit" if price_input.lower() == "no_limit" else float(price_input)
    
    console.print("\n" + "─" * 50 + "\n")
    
    # ========== STEP 2: Infer task ==========
    console.print("[bold yellow]🧠 STEP 2: Analyzing your request...[/bold yellow]\n")
    
    with console.status("[cyan]Calling Grok LLM to infer task type...[/cyan]"):
        task = await infer_task(query)
    
    console.print(f"[green]✓ Task identified:[/green] [bold white]{task}[/bold white]\n")
    
    console.print("─" * 50 + "\n")
    
    # ========== STEP 3: Generate questions ==========
    console.print("[bold yellow]❓ STEP 3: Generating clarifying questions...[/bold yellow]\n")
    
    with console.status("[cyan]Calling Grok LLM to generate questions...[/cyan]"):
        questions_data = await generate_clarifying_questions(
            task=task,
            query=query,
            zip_code=zip_code,
            date_needed=date_needed,
            price_limit=price_limit
        )
    
    questions = [
        ClarifyingQuestion(id=q["id"], question=q["question"])
        for q in questions_data
    ]
    
    console.print("[green]✓ Generated questions:[/green]\n")
    for i, q in enumerate(questions, 1):
        console.print(f"  [dim]{i}.[/dim] {q.question}")
    
    console.print("\n" + "─" * 50 + "\n")
    
    # ========== STEP 4: Collect answers ==========
    console.print("[bold yellow]💬 STEP 4: Please answer the questions[/bold yellow]\n")
    
    # Demo answers for common tasks
    demo_answers = {
        "plumber": [
            "The kitchen faucet is dripping constantly",
            "No, just a slow drip",
            "About 5 years old",
            "I tried tightening it but didn't help",
            "No, just this one faucet"
        ],
        "electrician": [
            "Outlet stopped working",
            "Repair - outlet is dead",
            "Just this one outlet",
            "No, breaker is fine",
            "House is about 20 years old"
        ],
        "painter": [
            "About 12x15 feet",
            "Light blue, eggshell finish",
            "Some nail holes to patch",
            "Yes, needs to be moved",
            "Just the walls"
        ],
        "default": [
            "It needs to be fixed ASAP",
            "Yes, somewhat urgent",
            "First time having this issue",
            "No special requirements",
            "That's all the info I have"
        ]
    }
    
    answers = {}
    if DEMO_MODE:
        task_answers = demo_answers.get(task.lower(), demo_answers["default"])
        for i, q in enumerate(questions):
            answer = task_answers[i] if i < len(task_answers) else "No additional info"
            answers[q.id] = answer
            console.print(f"[dim]Q: {q.question}[/dim]")
            console.print(f"[white]A: {answer}[/white]\n")
    else:
        for q in questions:
            answer = Prompt.ask(f"[cyan]{q.question}[/cyan]")
            answers[q.id] = answer
    
    console.print("\n" + "─" * 50 + "\n")
    
    # ========== STEP 5: Create Job object ==========
    console.print("[bold yellow]📋 STEP 5: Creating job object...[/bold yellow]\n")
    
    job = Job(
        id=str(uuid.uuid4()),
        original_query=query,
        task=task,
        zip_code=zip_code,
        date_needed=date_needed,
        price_limit=price_limit,
        questions=questions,
        clarifications=answers,
        status=JobStatus.READY_FOR_SEARCH
    )
    
    # Print job object
    job_table = Table(title="Job Object", show_header=True, header_style="bold magenta")
    job_table.add_column("Field", style="cyan")
    job_table.add_column("Value", style="white")
    
    job_table.add_row("ID", job.id)
    job_table.add_row("Query", job.original_query)
    job_table.add_row("Task", job.task)
    job_table.add_row("ZIP Code", job.zip_code)
    job_table.add_row("Date Needed", job.date_needed)
    job_table.add_row("Price Limit", str(job.price_limit))
    job_table.add_row("Status", job.status.value)
    
    console.print(job_table)
    console.print()
    
    # Print clarifications
    clarif_table = Table(title="Clarifications", show_header=True, header_style="bold magenta")
    clarif_table.add_column("Question", style="cyan")
    clarif_table.add_column("Answer", style="white")
    
    for q in questions:
        clarif_table.add_row(q.question[:50] + "..." if len(q.question) > 50 else q.question, 
                           answers.get(q.id, "N/A"))
    
    console.print(clarif_table)
    
    console.print("\n" + "─" * 50 + "\n")
    
    # ========== STEP 6: Search for providers ==========
    console.print("[bold yellow]🔍 STEP 6: Searching for providers...[/bold yellow]\n")
    
    with console.status("[cyan]Calling Grok Fast Search (Google Maps)...[/cyan]"):
        provider_creates = await search_providers(job)
    
    console.print(f"[green]✓ Found {len(provider_creates)} providers![/green]\n")
    
    # ========== STEP 7: Save to database ==========
    console.print("[bold yellow]💾 STEP 7: Saving providers to database...[/bold yellow]\n")
    
    db = SessionLocal()
    saved_providers = []
    
    try:
        for pc in provider_creates:
            db_provider = Provider(
                job_id=pc.job_id,
                name=pc.name,
                phone=pc.phone,
                estimated_price=pc.estimated_price,
                raw_result=pc.raw_result
            )
            db.add(db_provider)
            db.commit()
            db.refresh(db_provider)
            # Extract data while session is open
            saved_providers.append({
                "id": db_provider.id,
                "name": db_provider.name,
                "phone": db_provider.phone,
                "estimated_price": db_provider.estimated_price,
                "job_id": db_provider.job_id
            })
        
        console.print(f"[green]✓ Saved {len(saved_providers)} providers to database[/green]\n")
    finally:
        db.close()
    
    console.print("─" * 50 + "\n")
    
    # ========== STEP 8: Display results ==========
    console.print("[bold yellow]📊 STEP 8: Results[/bold yellow]\n")
    
    provider_table = Table(title="Service Providers Found", show_header=True, header_style="bold green")
    provider_table.add_column("#", style="dim", width=3)
    provider_table.add_column("Name", style="cyan")
    provider_table.add_column("Phone", style="white")
    provider_table.add_column("Est. Price", style="yellow")
    provider_table.add_column("DB ID", style="dim")
    
    for i, p in enumerate(saved_providers, 1):
        price_str = f"${p['estimated_price']:.0f}" if p['estimated_price'] else "Unknown"
        provider_table.add_row(
            str(i),
            p['name'],
            p['phone'] or "N/A",
            price_str,
            str(p['id'])
        )
    
    console.print(provider_table)
    
    # ========== Summary ==========
    console.print("\n" + "─" * 50 + "\n")
    console.print(Panel.fit(
        f"[bold green]✅ COMPLETE![/bold green]\n\n"
        f"[cyan]Job ID:[/cyan] {job.id}\n"
        f"[cyan]Task:[/cyan] {task}\n"
        f"[cyan]Providers found:[/cyan] {len(saved_providers)}\n"
        f"[cyan]Status:[/cyan] Ready for Phase 2 (Voice Agent)",
        title="Summary",
        border_style="green"
    ))
    console.print("\n")
    
    # Print JSON output for Phase 2
    console.print("[bold yellow]📤 JSON Output (for Phase 2 Voice Agent):[/bold yellow]\n")
    
    import json
    output = {
        "job": {
            "id": job.id,
            "original_query": job.original_query,
            "task": job.task,
            "zip_code": job.zip_code,
            "date_needed": job.date_needed,
            "price_limit": job.price_limit,
            "clarifications": job.clarifications
        },
        "providers": [
            {
                "id": p['id'],
                "name": p['name'],
                "phone": p['phone'],
                "estimated_price": p['estimated_price']
            }
            for p in saved_providers
        ]
    }
    
    console.print(json.dumps(output, indent=2))
    console.print("\n")


if __name__ == "__main__":
    asyncio.run(main())

