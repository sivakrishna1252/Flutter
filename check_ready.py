"""
Verification script to check if the project is ready for Git push and deployment
"""
import os
from pathlib import Path

def check_file_exists(filepath, should_exist=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists == should_exist else "❌"
    action = "exists" if should_exist else "does not exist"
    print(f"{status} {filepath} {action}")
    return exists == should_exist

def check_gitignore():
    """Check if .gitignore has necessary entries"""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("❌ .gitignore does not exist")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_entries = ['.env', 'venv/', 'db.sqlite3', '__pycache__/']
    all_present = True
    
    for entry in required_entries:
        if entry in content:
            print(f"✅ .gitignore contains '{entry}'")
        else:
            print(f"❌ .gitignore missing '{entry}'")
            all_present = False
    
    return all_present

def check_env_example():
    """Check if .env.example exists and has content"""
    env_example = Path(".env.example")
    if not env_example.exists():
        print("❌ .env.example does not exist")
        return False
    
    with open(env_example, 'r') as f:
        content = f.read()
    
    required_vars = ['SECRET_KEY', 'DEBUG', 'OPENAI_API_KEY']
    all_present = True
    
    for var in required_vars:
        if var in content:
            print(f"✅ .env.example contains '{var}'")
        else:
            print(f"❌ .env.example missing '{var}'")
            all_present = False
    
    return all_present

def check_settings_py():
    """Check if settings.py uses environment variables"""
    settings_path = Path("config/settings.py")
    if not settings_path.exists():
        print("❌ config/settings.py does not exist")
        return False
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("os.getenv('SECRET_KEY'", "SECRET_KEY uses environment variable"),
        ("os.getenv('DEBUG'", "DEBUG uses environment variable"),
        ("os.getenv('OPENAI_API_KEY'", "OPENAI_API_KEY uses environment variable"),
    ]
    
    all_present = True
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - NOT FOUND")
            all_present = False
    
    return all_present

def main():
    print("=" * 60)
    print("🔍 DIET PLANNER - GIT PUSH READINESS CHECK")
    print("=" * 60)
    print()
    
    print("📁 Checking required files...")
    print("-" * 60)
    files_ok = all([
        check_file_exists(".gitignore"),
        check_file_exists(".env.example"),
        check_file_exists("README.md"),
        check_file_exists("DEPLOYMENT.md"),
        check_file_exists("requirements.txt"),
        check_file_exists("config/settings.py"),
    ])
    print()
    
    print("🔒 Checking .gitignore...")
    print("-" * 60)
    gitignore_ok = check_gitignore()
    print()
    
    print("📝 Checking .env.example...")
    print("-" * 60)
    env_example_ok = check_env_example()
    print()
    
    print("⚙️  Checking settings.py...")
    print("-" * 60)
    settings_ok = check_settings_py()
    print()
    
    print("🔐 Checking sensitive files are protected...")
    print("-" * 60)
    env_exists = Path("config/.env").exists()
    if env_exists:
        print("✅ config/.env exists (should be in .gitignore)")
    else:
        print("⚠️  config/.env does not exist (you may need to create it)")
    print()
    
    print("=" * 60)
    if all([files_ok, gitignore_ok, env_example_ok, settings_ok]):
        print("✅ ALL CHECKS PASSED! Your project is ready for Git push!")
        print()
        print("Next steps:")
        print("1. git add .")
        print("2. git commit -m 'Prepare project for deployment'")
        print("3. git push origin main")
    else:
        print("❌ Some checks failed. Please review the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
