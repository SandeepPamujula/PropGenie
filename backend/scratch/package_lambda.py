import os
import shutil
import zipfile
import subprocess

def package():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(backend_dir, "dist")
    zip_filepath = os.path.join(backend_dir, "lambda.zip")
    requirements_file = os.path.join(backend_dir, "requirements.txt")

    print(f"Backend directory: {backend_dir}")
    print(f"Dist directory: {dist_dir}")
    print(f"Zip file path: {zip_filepath}")

    # 1. Clean dist and zip
    if os.path.exists(dist_dir):
        print("Cleaning up old dist directory...")
        shutil.rmtree(dist_dir)
    if os.path.exists(zip_filepath):
        print("Cleaning up old zip file...")
        os.remove(zip_filepath)

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

    # 3. Create zip archive
    print("Creating zip archive...")
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all dependencies from dist/
        print("Adding dependencies to zip...")
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, dist_dir)
                zipf.write(filepath, arcname)

        # Add code files and directories
        code_files = ["handler.py", "graph.py"]
        code_dirs = ["agents", "db", "models", "observability", "portal_configs", "utils"]

        print("Adding code files to zip...")
        for file in code_files:
            file_path = os.path.join(backend_dir, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
                print(f"  Added {file}")

        print("Adding code directories to zip...")
        for folder in code_dirs:
            folder_path = os.path.join(backend_dir, folder)
            if os.path.exists(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    # Skip __pycache__
                    if "__pycache__" in root:
                        continue
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, backend_dir)
                        zipf.write(filepath, arcname)
                print(f"  Added directory {folder}")

    zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
    print(f"Deployment package created successfully at {zip_filepath} ({zip_size_mb:.2f} MB)")

if __name__ == "__main__":
    package()
