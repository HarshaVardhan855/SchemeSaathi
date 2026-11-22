#!/usr/bin/env python3
"""
Quick demo runner for SchemeSaathi.
Supports both direct CLI execution and Streamlit execution on Render.
"""
import os
import sys
import subprocess
from pathlib import Path

# Check if running under Streamlit (e.g., `streamlit run run_demo.py`)
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    _IS_STREAMLIT = get_script_run_ctx() is not None
except Exception:
    _IS_STREAMLIT = False

if _IS_STREAMLIT:
    # Delegate to the Streamlit application UI
    import streamlit_app
    streamlit_app.main()

else:
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
        from eligibility_rag import get_rag
        rag = get_rag()
        rag.initialize()
        print("✅ RAG initialized")

    def run_streamlit():
        """Run the Streamlit app with dynamic port support."""
        port = os.getenv("PORT", os.getenv("STREAMLIT_SERVER_PORT", "8501"))
        print(f"🚀 Starting SchemeSaathi demo on port {port}...")
        print(f"   Open http://localhost:{port} in your browser")
        print("   Press Ctrl+C to stop\n")

        os.chdir(Path(__file__).parent)
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "run_demo.py",
            "--server.port", str(port),
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
