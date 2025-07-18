import argparse
import asyncio
import os

from cli import process_input_stream, interactive_mode, save_documentation, generate_filename, render_logo
from rich.console import Console

console = Console()


def main():
    """
    Main entry point with command-line argument handling.
    """
    parser = argparse.ArgumentParser(
        description="Requirements Generation and Optimization Engine"
    )
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--input", type=str, help="Natural language input string")
    parser.add_argument("--output-dir", type=str, default="PRD", help="Output directory for documentation (default: PRD)")
    parser.add_argument("--output", type=str, help="Specific output file path (overrides --output-dir)")
    parser.add_argument("--lang", type=str, choices=["en", "zh"], default="en", help="Language preference (en or zh, default: en)")

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.input:
        # Show logo for command line mode too
        render_logo()

        # Process input using streaming
        shared = asyncio.run(process_input_stream(args.input, args.lang))

        # Output results
        if args.output:
            # Use specific output file path
            try:
                output_dir = os.path.dirname(args.output)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(shared["documentation"])
                print(f"Documentation saved to {args.output}")
            except Exception as e:
                print(f"Error saving documentation: {e}")
                print(shared["documentation"])
        else:
            # Auto-generate filename and save to output directory
            filename = generate_filename(args.input)
            
            output_dir = args.output_dir
            output_path = os.path.join(output_dir, filename)
            os.makedirs(output_dir, exist_ok=True)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(shared["documentation"])

                if args.lang == "zh":
                    console.print(f"\n✅ 文档已自动保存到: [green]{output_path}[/green]")
                    console.print("\n🎯 [bold blue]GTPlanner[/bold blue] - 让需求分析更简单！", justify="center")
                else:
                    console.print(f"\n✅ Documentation automatically saved to: [green]{output_path}[/green]")
                    console.print("\n🎯 [bold blue]GTPlanner[/bold blue] - Making Requirements Analysis Easier!", justify="center")

            except Exception as e:
                console.print(f"❌ Error saving documentation: {e}", style="red")
                print(shared["documentation"])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
