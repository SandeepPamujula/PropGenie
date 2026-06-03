import os
import shutil
import subprocess

def prepare():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(backend_dir, "dist")
    requirements_file = os.path.join(backend_dir, "requirements.txt")

    print(f"Preparing backend dist in: {dist_dir}")

    # 1. Clean dist
    if os.path.exists(dist_dir):
        print("Cleaning up old dist directory...")
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            # Handle potential file lock issues by renaming first
            print(f"Failed to remove dist directory: {e}. Attempting rename and clean...")
            temp_old_dist = dist_dir + "_old"
            if os.path.exists(temp_old_dist):
                shutil.rmtree(temp_old_dist, ignore_errors=True)
            os.rename(dist_dir, temp_old_dist)
            shutil.rmtree(temp_old_dist, ignore_errors=True)

    os.makedirs(dist_dir, exist_ok=True)

    # 2. Run pip install targeting Linux Python 3.12
    print("Installing dependencies...")
    cmd = [
        "pip", "install",
        "-r", requirements_file,
        "--platform", "manylinux2014_x86_64",
        "--only-binary=:all:",
        "--python-version", "3.12",
        "-t", dist_dir
    ]
    subprocess.run(cmd, check=True)

    # 3. Copy code files and directories to dist/
    code_files = ["handler.py", "graph.py"]
    code_dirs = ["agents", "db", "models", "observability", "portal_configs", "utils"]

    print("Copying code files...")
    for file in code_files:
        src = os.path.join(backend_dir, file)
        dst = os.path.join(dist_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied {file}")

    print("Copying code directories...")
    for folder in code_dirs:
        src = os.path.join(backend_dir, folder)
        dst = os.path.join(dist_dir, folder)
        if os.path.exists(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print(f"  Copied directory {folder}")

    print("Dist directory prepared successfully!")

if __name__ == "__main__":
    prepare()
