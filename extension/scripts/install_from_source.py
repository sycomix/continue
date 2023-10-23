# Run from extension/scripts directory

import os
import subprocess


def run(cmd: str):
    return subprocess.run(cmd, shell=True, capture_output=False)

def get_latest_version() -> str:
    # Ensure build directory exists
    if not os.path.exists("../build"):
        os.mkdir("../build")

    def version_tuple(filename):
        version = filename.split("-")[1].split(".vsix")[0]
        return tuple(map(int, version.split(".")))

    versions = [file for file in os.listdir("../build") if file.endswith(".vsix")]

    # Ensure we have at least one version
    return None if not versions else max(versions, key=version_tuple)

def main():
    # Clear out old stuff
    run(f"rm -rf ../build/{get_latest_version()}")
    run("rm ../server/continuedev-0.1.2-py3-none-any.whl")

    # Check for Python and Node - we won't install them, but will warn
    resp1 = run("python --version")
    resp2 = run("python3 --version")
    if resp1.stderr and resp2.stderr:
        print("Python is required for Continue but is not installed on your machine. See https://www.python.org/downloads/ to download the latest version, then try again.")
        return

    resp = run("node --version")
    if resp.stderr:
        print("Node is required for Continue but is not installed on your machine. See https://nodejs.org/en/download/ to download the latest version, then try again.")
        return

    resp = run("npm --version")
    if resp.stderr:
        print("NPM is required for Continue but is not installed on your machine. See https://nodejs.org/en/download/ to download the latest version, then try again.")
        return

    resp = run("poetry --version")
    if resp.stderr:
        print("Poetry is required for Continue but is not installed on your machine. See https://python-poetry.org/docs/#installation to download the latest version, then try again.")
        return

    resp = run("cd ../../continuedev; poetry install; poetry run typegen")

    resp = run(
        "cd ..; npm i; cd react-app; npm i; cd ..; npm run package")

    if resp.stderr:
        print("Error packaging the extension. Please try again.")
        print("This was the error: ", resp.stderr)
        return

    latest = get_latest_version()
    resp = run(f"cd ..; code --install-extension ./build/{latest}")
    
    print("Continue VS Code extension installed successfully. Please restart VS Code to use it.")


if __name__ == "__main__":
    main()
