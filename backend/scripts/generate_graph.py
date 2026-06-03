import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import create_graph


def main():
    print("Compiling LangGraph workflow...")
    app = create_graph()

    # Get the Mermaid representation
    mermaid_code = app.get_graph().draw_mermaid()

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "docs",
        "graph_topology.md"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# LangGraph Workflow Topology\n\n")
        f.write("Below is the compiled graph structure extracted programmatically from the backend code:\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```\n")

    print(f"Workflow topology written successfully to: {output_path}")

if __name__ == "__main__":
    main()
