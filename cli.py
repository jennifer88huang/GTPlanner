import argparse
import asyncio
import os

from cli_flow import requirement_engine_flow
from filename_flow import create_filename_flow
from short_planner_flow import create_short_planner_flow


async def process_input(natural_language="", markdown_files=None):
    """
    Process user input to generate requirements documentation.

    Args:
        natural_language (str): Natural language description of requirements
        markdown_files (list): List of paths to markdown files to include

    Returns:
        dict: Final state of the shared memory
    """
    # First, run short_planner_flow
    shared_short_planner = {
        "history": [],
        "version": 1,
        "requirement": natural_language,
    }
    short_planner_instance = create_short_planner_flow()
    await short_planner_instance.run_async(shared_short_planner)

    short_flow_steps = shared_short_planner.get("final_steps", "")

    # Initialize shared memory structure for requirement_engine_flow
    shared = {
        "user_input": {"natural_language": natural_language, "markdown_documents": []},
        "short_flow_steps": short_flow_steps,
        "conversation_history": [],
        "requirements": {"functional": [], "non_functional": [], "constraints": []},
        "optimizations": [],
        "documentation": "",
        "feedback": "",
        "current_iteration": 1,
    }

    # Load markdown documents if provided
    if markdown_files:
        for file_path in markdown_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    shared["user_input"]["markdown_documents"].append(f.read())
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    # Run the main flow
    await requirement_engine_flow.run_async(shared)

    # Return the final state
    return shared


async def interactive_mode():
    """
    Run the application in interactive mode, allowing for iterative feedback.
    """
    print("=== Requirements Generation Engine ===")
    print(
        "This tool will help you analyze requirements and generate technical documentation."
    )

    # Get initial input
    natural_language = input("Please describe your project requirements: ")

    # # Ask for markdown files (optional, all at once)
    # print(
    #     "(Optional) Enter markdown file paths, one per line. Press Enter on empty line to finish:"
    # )
    # markdown_files = []
    # while True:
    #     file_path = input("")
    #     if not file_path:
    #         break
    #     if os.path.exists(file_path):
    #         markdown_files.append(file_path)
    #     else:
    #         print(f"File not found: {file_path}")

    # Process initial input (which now includes running short_planner_flow first)
    shared = await process_input(natural_language, None)

    # Display the documentation
    print("\n=== Generated Documentation ===\n")
    print(shared["documentation"])

    # Simplified feedback loop
    while True:
        feedback = input("\nPlease provide feedback for refinement ('q' to quit): ")
        if feedback.strip().lower() == "q":
            print("Process complete. Final documentation has been generated.")
            # 自动生成文件名并保存到 ./output/{filename}
            filename_flow = create_filename_flow()
            filename_flow.run(shared)
            filename = shared.get("generated_filename", "documentation.md")
            output_dir = "output"
            output_path = os.path.join(output_dir, filename)
            os.makedirs(output_dir, exist_ok=True)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(shared["documentation"])
                print(f"Documentation automatically saved to {output_path}")
            except Exception as e:
                print(f"Error saving documentation: {e}")
            break
        # Process feedback
        shared["feedback"] = feedback
        await requirement_engine_flow.run_async(shared)
        # Display updated documentation
        print("\n=== Updated Documentation ===\n")
        print(shared["documentation"])


def main():
    """
    Main entry point with command-line argument handling.
    """
    parser = argparse.ArgumentParser(
        description="Requirements Generation and Optimization Engine"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument("--input", type=str, help="Natural language input string")
    parser.add_argument("--files", nargs="*", help="Markdown files to process")
    parser.add_argument("--output", type=str, help="Output file for documentation")

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.input:
        # Process input and files (which now includes running short_planner_flow first)
        shared = asyncio.run(process_input(args.input, args.files))

        # Output results
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(shared["documentation"])
                print(f"Documentation saved to {args.output}")
            except Exception as e:
                print(f"Error saving documentation: {e}")
                print(shared["documentation"])
        else:
            print(shared["documentation"])
    else:
        # Default to interactive mode if no arguments provided
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
