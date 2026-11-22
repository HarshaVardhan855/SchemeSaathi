#!/usr/bin/env python3
"""
Quick demo runner for SchemeSaathi.
Runs the Streamlit app with proper environment setup.
"""
import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """Check if required environment variables are set."""
    required = ["GROQ_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nCreate a .env file from .env.example and add your Groq API key.")
        print("Get free key at: https://console.groq.com")
        return False
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    # Install Playwright browsers
    print("🌐 Installing Playwright browsers...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

    # Download Piper voices (happens on first use, but we can trigger)
    print("🔊 Piper voices will download on first TTS use")


def initialize_rag():
    """Initialize the RAG engine with scheme data."""
    print("🧠 Initializing RAG engine...")
    sys.path.insert(0, str(Path(__file__).parent))
    from eligibility_rag import initialize_rag
    initialize_rag()
    print("✅ RAG initialized")


def run_streamlit():
    """Run the Streamlit app."""
    print("🚀 Starting SchemeSaathi demo...")
    print("   Open http://localhost:8501 in your browser")
    print("   Press Ctrl+C to stop\n")

    os.chdir(Path(__file__).parent)
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false",
    ])


def main():
    print("=" * 50)
    print("  SchemeSaathi — Voice-First Scheme Eligibility")
    print("  Hackathon Demo Runner")
    print("=" * 50)

    # Load .env if exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ Loaded .env file")

    if not check_environment():
        sys.exit(1)

    # Install deps if needed
    if "--install" in sys.argv or "--full" in sys.argv:
        install_dependencies()

    # Initialize RAG
    if "--init-rag" in sys.argv or "--full" in sys.argv:
        initialize_rag()

    # Run app
    run_streamlit()


if __name__ == "__main__":
    main()