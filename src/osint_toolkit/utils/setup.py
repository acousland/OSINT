#!/usr/bin/env python3
"""
API Key Setup Helper for OSINT Toolkit
"""

import os
from pathlib import Path

def setup_api_key():
    """Interactive API key setup"""
    print("🔑 OSINT Toolkit - API Key Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        with open(env_file, 'r') as f:
            content = f.read()
        
        if "OPENAI_API_KEY=" in content and "your_openai_api_key_here" not in content:
            print("✅ API key appears to be configured")
            print("\nIf you're still having issues, check that your API key is valid.")
            return
    else:
        print("⚠️  .env file not found - creating one now")
    
    print("\n🌟 To use the AI dossier generation feature, you need an OpenAI API key.")
    print("\n📝 Steps to get your API key:")
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Sign in or create an account")
    print("3. Click 'Create new secret key'")
    print("4. Copy the key (it starts with 'sk-')")
    print("5. Paste it below")
    
    print("\n💡 Note: You'll need to add billing information to your OpenAI account")
    print("   to use the API. The cost is typically very low for document analysis.")
    
    while True:
        api_key = input("\n🔑 Enter your OpenAI API key (or 'skip' to configure later): ").strip()
        
        if api_key.lower() == 'skip':
            print("\n⏭️  Skipping API key setup. You can configure it later in the .env file.")
            create_env_template()
            break
        
        if not api_key:
            print("❌ Please enter a valid API key or type 'skip'")
            continue
        
        if not api_key.startswith('sk-'):
            print("⚠️  OpenAI API keys typically start with 'sk-'. Are you sure this is correct?")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
        
        # Create or update .env file
        create_env_file(api_key)
        print("\n✅ API key configured successfully!")
        print("🚀 You can now use the dossier generation feature.")
        break

def create_env_template():
    """Create .env file with template"""
    env_content = """# Configuration for OSINT Toolkit
# Add your API keys below

# OpenAI API Key (required for dossier generation)
OPENAI_API_KEY=your_openai_api_key_here

# Alternative LLM providers (uncomment and configure as needed)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# COHERE_API_KEY=your_cohere_key_here

# Processing settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_TOKENS=4000
MAX_CLUSTERS=8

# Output settings
OUTPUT_DIR=dossiers
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("📄 Created .env file with template")

def create_env_file(api_key):
    """Create or update .env file with API key"""
    env_content = f"""# Configuration for OSINT Toolkit
# API Keys

# OpenAI API Key (configured)
OPENAI_API_KEY={api_key}

# Alternative LLM providers (uncomment and configure as needed)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# COHERE_API_KEY=your_cohere_key_here

# Processing settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_TOKENS=4000
MAX_CLUSTERS=8

# Output settings
OUTPUT_DIR=dossiers
"""
    
    with open(".env", "w") as f:
        f.write(env_content)

def check_current_setup():
    """Check current API configuration"""
    print("🔍 Current Configuration Status")
    print("=" * 35)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("✅ .env file exists")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    if api_key == "your_openai_api_key_here":
        print("⚠️  Placeholder API key detected - needs to be replaced")
        return False
    
    if len(api_key) < 20:
        print("⚠️  API key appears to be too short")
        return False
    
    print("✅ API key configured")
    print(f"   Key starts with: {api_key[:10]}...")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_current_setup()
    else:
        setup_api_key()
