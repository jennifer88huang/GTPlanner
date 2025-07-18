import asyncio
import datetime
import os
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from api.v1.planning import ShortPlanningRequest, LongPlanningRequest, short_planning_stream, long_planning_stream

# 创建全局console对象
console = Console()


async def process_input_stream(natural_language="", language="en"):
    """
    Process user input to generate requirements documentation using streaming.

    Args:
        natural_language (str): Natural language description of requirements
        language (str): Language preference ("en" or "zh")

    Returns:
        dict: Final state with generated documentation
    """
    # Step 1: Generate short planning flow
    step1_title = "🚀 生成步骤化流程" if language == "zh" else "🚀 Generating Step-by-Step Flow"
    console.print(Panel(step1_title, style="bold blue"))

    short_request = ShortPlanningRequest(
        requirement=natural_language,
        language=language
    )

    short_flow_content = ""
    # 不使用status，直接显示内容
    async for chunk in short_planning_stream(short_request):
        if chunk.startswith("data: "):
            content = chunk[6:].strip()
            if content.startswith("[") and content.endswith("]"):
                # Skip control messages
                continue
            # Replace protected newlines back to actual newlines
            content = content.replace('<|newline|>', '\n')
            console.print(content, end='')
            short_flow_content += content

    console.print()

    # Step 2: Generate detailed documentation
    step2_title = "📝 生成详细文档" if language == "zh" else "📝 Generating Detailed Documentation"
    console.print(Panel(step2_title, style="bold green"))

    long_request = LongPlanningRequest(
        requirement=natural_language,
        previous_flow=short_flow_content,
        language=language
    )

    documentation = ""
    # 处理流式内容并美化状态显示
    async for chunk in long_planning_stream(long_request):
        if chunk.startswith("data: "):
            content = chunk[6:].strip()
            if content.startswith("[") and content.endswith("]"):
                # Skip control messages like [STATUS_START], [LONG_DOC_START], etc.
                continue

            # 检查是否是状态信息并美化显示
            if content.startswith("🔍 正在分析需求") or content.startswith("🔍 Analyzing requirements"):
                if language == "zh":
                    console.print(Panel(
                        "🔍 [bold blue]需求分析中[/bold blue] [dim]Analyzing Requirements[/dim]",
                        style="blue",
                        border_style="blue"
                    ))
                else:
                    console.print(Panel(
                        "🔍 [bold blue]Analyzing Requirements[/bold blue] [dim]需求分析中[/dim]",
                        style="blue",
                        border_style="blue"
                    ))
                continue
            elif content.startswith("📝 开始生成设计文档") or content.startswith("📝 Generating design document"):
                if language == "zh":
                    console.print(Panel(
                        "📝 [bold green]生成设计文档[/bold green] [dim]Generating Design Document[/dim]",
                        style="green",
                        border_style="green"
                    ))
                else:
                    console.print(Panel(
                        "📝 [bold green]Generating Design Document[/bold green] [dim]生成设计文档[/dim]",
                        style="green",
                        border_style="green"
                    ))
                continue

            # Replace protected newlines back to actual newlines
            content = content.replace('<|newline|>', '\n')
            console.print(content, end='')
            documentation += content

    console.print()

    return {
        "short_flow_steps": short_flow_content,
        "documentation": documentation,
        "language": language
    }


def render_logo():
    """
    Render the ASCII logo from ASCII.txt file.
    """
    try:
        with open("ASCII.txt", "r", encoding="utf-8") as f:
            logo = f.read()
        console.print(logo, style="bold cyan")
    except FileNotFoundError:
        # Fallback if ASCII.txt is not found
        console.print("GTPlanner", style="bold cyan", justify="center")
    console.print()


async def interactive_mode():
    """
    Run the application in interactive mode, allowing for iterative feedback.
    """
    # 显示ASCII logo
    render_logo()

    # 显示欢迎界面
    welcome_text = Text("GTPlanner", style="bold magenta")
    welcome_text.append(" - Requirements Generation Engine", style="bold blue")

    console.print(Panel(
        welcome_text,
        subtitle="Generate technical documentation from natural language requirements",
        style="bold",
        border_style="blue"
    ))

    console.print("This tool will help you analyze requirements and generate technical documentation.", style="dim")
    console.print()

    # Ask for language preference
    console.print("🌍 [bold]Language / 语言:[/bold]")
    console.print("  [green]1.[/green] English (default)")
    console.print("  [green]2.[/green] 中文")

    lang_choice = Prompt.ask("Choose language", choices=["1", "2"], default="1")

    if lang_choice == "2":
        language = "zh"
        natural_language = Prompt.ask("\n[bold blue]请描述您的项目需求[/bold blue]")
        default_output_dir = "PRD"
        output_dir = Prompt.ask(f"[dim](可选) 输入输出目录[/dim]", default=default_output_dir)
    else:
        language = "en"
        natural_language = Prompt.ask("\n[bold blue]Please describe your project requirements[/bold blue]")
        default_output_dir = "PRD"
        output_dir = Prompt.ask(f"[dim](Optional) Enter output directory[/dim]", default=default_output_dir)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    console.print(f"✅ Output directory: [green]{output_dir}[/green]")

    # Process initial input using streaming
    shared = await process_input_stream(natural_language, language)
    shared["output_directory"] = output_dir  # Store output directory in shared state

    # Auto-save the documentation
    await save_documentation(shared, natural_language, language)


async def save_documentation(shared, natural_language, language):
    """
    Save the generated documentation with beautiful UI feedback.
    """
    save_title = "💾 保存文档" if language == "zh" else "💾 Saving Documentation"
    console.print(Panel(save_title, style="bold yellow"))

    # 自动生成文件名
    filename = generate_filename(natural_language)

    # 使用用户指定的输出目录或默认目录
    output_dir = shared.get("output_directory", "PRD")
    output_path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)

    with console.status("[bold green]正在保存..." if language == "zh" else "[bold green]Saving...", spinner="dots"):
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(shared["documentation"])

            # 美化完成提示
            if language == "zh":
                console.print(Panel(
                    f"✅ [bold green]文档生成完成！[/bold green]\n\n📁 保存位置: [cyan]{output_path}[/cyan]\n\n🚀 [dim]感谢使用 GTPlanner！[/dim]",
                    title="🎉 完成",
                    style="green",
                    border_style="green"
                ))
                # 添加结束横幅
                console.print()
                console.print("=" * 80, style="dim")
                console.print("🎯 [bold blue]GTPlanner[/bold blue] - 让需求分析更简单！", justify="center", style="bold")
                console.print("💡 [dim]如有问题或建议，欢迎反馈[/dim]", justify="center")
                console.print("=" * 80, style="dim")
            else:
                console.print(Panel(
                    f"✅ [bold green]Documentation Generated Successfully![/bold green]\n\n📁 Saved to: [cyan]{output_path}[/cyan]\n\n🚀 [dim]Thank you for using GTPlanner![/dim]",
                    title="🎉 Complete",
                    style="green",
                    border_style="green"
                ))
                # 添加结束横幅
                console.print()
                console.print("=" * 80, style="dim")
                console.print("🎯 [bold blue]GTPlanner[/bold blue] - Making Requirements Analysis Easier!", justify="center", style="bold")
                console.print("💡 [dim]Feedback and suggestions are welcome[/dim]", justify="center")
                console.print("=" * 80, style="dim")

        except Exception as e:
            error_msg = f"❌ 保存文档时出错: {e}" if language == "zh" else f"❌ Error saving documentation: {e}"
            console.print(Panel(error_msg, style="red", border_style="red"))


def generate_filename(natural_language):
    """
    Generate a filename from natural language input.
    """
    # 简单 slugify: 只保留中文字符、字母数字和空格，空格转横线，小写
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5 ]", "", natural_language)
    slug = slug.strip().lower().replace(" ", "-")[:20]
    if not slug:
        slug = "documentation"

    today = datetime.datetime.now().strftime("%Y%m%d")
    return f"{slug}-{today}.md"