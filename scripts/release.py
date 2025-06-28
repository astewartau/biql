#!/usr/bin/env python3
"""
Release helper script for BIQL
"""

import subprocess
import sys
import re
from pathlib import Path

def get_current_version():
    """Get current version from setup.py"""
    setup_py = Path("setup.py").read_text()
    match = re.search(r'version="([^"]+)"', setup_py)
    if match:
        return match.group(1)
    
    # Try pyproject.toml
    pyproject = Path("pyproject.toml").read_text()
    match = re.search(r'version = "([^"]+)"', pyproject)
    if match:
        return match.group(1)
    
    raise ValueError("Could not find version")

def update_version(new_version):
    """Update version in setup.py and pyproject.toml"""
    # Update setup.py
    setup_py = Path("setup.py")
    content = setup_py.read_text()
    content = re.sub(r'version="[^"]+"', f'version="{new_version}"', content)
    setup_py.write_text(content)
    
    # Update pyproject.toml
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject.write_text(content)

def run_tests():
    """Run the test suite"""
    print("Running tests...")
    result = subprocess.run(["python", "-m", "pytest", "tests/"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    print("✅ Tests passed!")
    return True

def build_package():
    """Build the package"""
    print("Building package...")
    result = subprocess.run(["python", "-m", "build"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Build failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    print("✅ Package built!")
    return True

def create_git_tag(version):
    """Create a git tag for the release"""
    print(f"Creating git tag v{version}...")
    subprocess.run(["git", "add", "setup.py", "pyproject.toml"])
    subprocess.run(["git", "commit", "-m", f"Bump version to {version}"])
    subprocess.run(["git", "tag", f"v{version}"])
    print("✅ Git tag created!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <version>")
        print("Example: python scripts/release.py 0.2.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    current_version = get_current_version()
    
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Confirm
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        sys.exit(1)
    
    # Update version
    update_version(new_version)
    print(f"✅ Version updated to {new_version}")
    
    # Build package
    if not build_package():
        sys.exit(1)
    
    # Create git tag
    create_git_tag(new_version)
    
    print("\n🎉 Release prepared!")
    print("Next steps:")
    print("1. Push to GitHub: git push && git push --tags")
    print("2. Create a GitHub release at: https://github.com/astewartau/biql/releases/new")
    print("3. The GitHub Action will automatically publish to PyPI")

if __name__ == "__main__":
    main()