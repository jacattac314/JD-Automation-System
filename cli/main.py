"""
Command-line interface for JD Automation System.
"""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from core.orchestrator import Orchestrator


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Local-First Job Description Automation System.
    
    Transform job descriptions into fully implemented projects.
    """
    pass


@cli.command()
@click.option("--jd", "-j", help="Job description text")
@click.option("--jd-file", "-f", type=click.Path(exists=True), help="Path to JD text file")
@click.option("--auto", "-a", is_flag=True, default=True, help="Auto-confirm project ideas")
@click.option("--no-linkedin", is_flag=True, help="Skip LinkedIn integration")
def run(jd, jd_file, auto, no_linkedin):
    """Run the automation pipeline."""
    
    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        console.print("[red]Configuration errors:[/red]")
        for error in errors:
            console.print(f"  [red]✗[/red] {error}")
        console.print("\n[yellow]Please configure your .env file or use setup command[/yellow]")
        sys.exit(1)
    
    # Get job description
    if jd_file:
        jd_text = Path(jd_file).read_text()
    elif jd:
        jd_text = jd
    else:
        console.print("[red]Please provide job description via --jd or --jd-file[/red]")
        sys.exit(1)
    
    # Override LinkedIn setting
    if no_linkedin:
        config.enable_linkedin = False
    
    console.print(Panel.fit(
        "[bold cyan]JD Automation System[/bold cyan]\n"
        "Starting automation pipeline...",
        border_style="cyan"
    ))
    
    # Run orchestrator
    orchestrator = Orchestrator()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Running automation...", total=None)
            
            result = orchestrator.run(jd_text, auto_confirm=auto)
            
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n[bold green]✓ Automation Complete![/bold green]\n")
        
        console.print(f"[cyan]Project:[/cyan] {result.get('project_idea', {}).get('title', 'N/A')}")
        console.print(f"[cyan]Repository:[/cyan] {result.get('repo', {}).get('url', 'N/A')}")
        console.print(f"[cyan]Time:[/cyan] {result.get('elapsed_time', 0):.1f}s")
        
        if result.get('linkedin'):
            console.print(f"[cyan]LinkedIn:[/cyan] Project added to profile")
        
        console.print(f"\n[green]Run ID:[/green] {result.get('run_id')}")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")
        logger.exception("Run failed")
        sys.exit(1)


@cli.command()
def setup():
    """Configure API keys and settings."""
    console.print(Panel.fit(
        "[bold cyan]Setup Wizard[/bold cyan]\n"
        "Configure your API keys",
        border_style="cyan"
    ))
    
    # Gemini API Key
    gemini_key = click.prompt("Gemini API Key", default=config.gemini_api_key or "", hide_input=True)
    if gemini_key:
        config.set_secret("GEMINI_API_KEY", gemini_key)
    
    # GitHub Token
    github_token = click.prompt("GitHub Personal Access Token", default=config.github_token or "", hide_input=True)
    if github_token:
        config.set_secret("GITHUB_TOKEN", github_token)
    
    github_username = click.prompt("GitHub Username", default=config.github_username or "")
    
    # Anthropic Key
    anthropic_key = click.prompt("Anthropic API Key", default=config.anthropic_api_key or "", hide_input=True)
    if anthropic_key:
        config.set_secret("ANTHROPIC_API_KEY", anthropic_key)
    
    # LinkedIn (optional)
    use_linkedin = click.confirm("Enable LinkedIn integration?", default=False)
    if use_linkedin:
        linkedin_token = click.prompt("LinkedIn Access Token", hide_input=True)
        config.set_secret("LINKEDIN_ACCESS_TOKEN", linkedin_token)
    
    # Update .env file
    env_path = Path(".env")
    env_content = f"""# JD Automation System Configuration

# API Keys (stored in keyring)
GEMINI_API_KEY=<stored_in_keyring>
GITHUB_TOKEN=<stored_in_keyring>
ANTHROPIC_API_KEY=<stored_in_keyring>

# GitHub
GITHUB_USERNAME={github_username}

# LinkedIn
ENABLE_LINKEDIN_INTEGRATION={'true' if use_linkedin else 'false'}

# Settings
DEFAULT_REPO_VISIBILITY=private
PROJECT_STORAGE_PATH=./projects
LOG_LEVEL=INFO
"""
    
    env_path.write_text(env_content)
    
    console.print("\n[green]✓ Configuration saved![/green]")


@cli.command()
def history():
    """View run history."""
    history_file = config.data_dir / "runs.json"
    
    if not history_file.exists():
        console.print("[yellow]No runs found[/yellow]")
        return
    
    import json
    runs = json.loads(history_file.read_text())
    
    console.print(Panel.fit("[bold cyan]Run History[/bold cyan]", border_style="cyan"))
    console.print()
    
    for run in reversed(runs[-10:]):  # Show last 10
        status_icon = "✓" if run['status'] == 'success' else "✗"
        status_color = "green" if run['status'] == 'success' else "red"
        
        console.print(f"[{status_color}]{status_icon}[/{status_color}] {run['timestamp']}")
        console.print(f"   Project: {run.get('project', 'N/A')}")
        console.print(f"   Repo: {run.get('repo_url', 'N/A')}")
        console.print(f"   Time: {run.get('elapsed_time', 0):.1f}s")
        console.print()


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=config.log_level
    )
    logger.add(
        config.logs_dir / "jd_automation_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    cli()
