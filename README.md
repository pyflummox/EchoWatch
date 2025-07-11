🎵 EchoWatch Emergency Monitor
Real-time emergency radio monitoring and AI-powered analysis system that monitors Broadcastify streams, transcribes audio calls, and provides intelligent analysis of emergency communications.
🚨 Features

Real-time Monitoring: Continuously monitors Broadcastify emergency radio streams
Automatic Download: Downloads new MP3 calls as they become available
Speech Recognition: Transcribes audio using OpenAI Whisper
AI Analysis: Uses GPT models to analyze transcripts for severity and importance
Intelligent Batching: Groups transcripts every 60 seconds for contextual analysis
Alert System: Sends alerts for high-severity events
Organized Storage: Systematic file organization and archival

📁 Project Structure
EchoWatch/
├── src/
│   ├── broadcastify_monitor.py     # Downloads MP3s from Broadcastify
│   ├── audio_processor.py          # Whisper transcription
│   ├── llm_analyzer.py             # GPT analysis and alerting
│   ├── file_manager.py             # File organization
│   └── config.py                   # Configuration settings
├── Media/
│   ├── Inbound/                    # New MP3 downloads
│   ├── InProgress/                 # Files being processed
│   ├── Transcribing/               # Individual transcripts
│   └── Archive/
│       ├── Processed/              # Archived MP3s
│       └── Transcriptions/         # Batch transcripts & analysis
├── logs/                           # Application logs
├── main.py                         # Main orchestrator
└── requirements.txt
⚙️ Setup
1. Install Dependencies
bashpip install -r requirements.txt
2. Download ChromeDriver

Download ChromeDriver from chromedriver.chromium.org
Update the path in src/config.py

3. Configure Settings
Edit src/config.py:
python# Broadcastify Configuration
UUID = "your-broadcastify-uuid-here"
CHROMEDRIVER_PATH = r"path\to\chromedriver.exe"
BRAVE_BINARY_PATH = r"path\to\brave.exe"  # Or Chrome

# OpenAI API Key
OPENAI_API_KEY = "your-openai-api-key"

# Processing Settings
WHISPER_MODEL = "medium"  # base, small, medium, large
BATCH_INTERVAL = 60       # seconds between LLM analysis
SEVERITY_THRESHOLD = 2    # Alert threshold (0-5)
🚀 Usage
Start EchoWatch
bashpython main.py
Components
The system runs four main components in parallel:

Broadcastify Monitor: Downloads new MP3 calls
Audio Processor: Transcribes MP3s using Whisper
LLM Analyzer: Analyzes transcript batches every 60 seconds
File Manager: Organizes files through the pipeline

Workflow
MP3 Download → Media/Inbound 
           → Media/InProgress (transcribing)
           → Media/Transcribing (individual .txt files)
           → Batch Analysis (every 60s)
           → Media/Archive/