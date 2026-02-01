#!/usr/bin/env python3
"""
A.R.T.H.U.R. - Advanced Real-Time Helper and Understanding Resource
Main entry point with mode selection

Usage:
    python -m arthur.main [--voice | --gui | --config]

Options:
    --voice     Start in voice-only mode (JARVIS-style)
    --gui       Start in GUI mode (default)
    --config    Run configuration wizard
"""

import argparse
import json
import os
from pathlib import Path


CONFIG_FILE = Path(__file__).parent / "data" / "config.json"


def load_config() -> dict:
    """Load configuration from file"""
    default_config = {
        'model': 'llama3.2:8b',
        'whisper_model': 'base.en',
        'high_quality_voice': False,
        'voice_enabled': True,
        'weather_api_key': '',
        'default_city': '',
        'default_mode': 'gui'
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                default_config.update(saved_config)
        except:
            pass

    return default_config


def save_config(config: dict):
    """Save configuration to file"""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def run_config_wizard():
    """Interactive configuration wizard"""
    print("\n" + "=" * 50)
    print("A.R.T.H.U.R. Configuration Wizard")
    print("=" * 50)

    config = load_config()

    print("\n[1] LLM Model Configuration")
    print(f"    Current: {config['model']}")
    print("    Options: llama3.2:8b (recommended), llama3.2:3b (faster), mistral:7b")
    model = input("    Enter model name (or press Enter to keep current): ").strip()
    if model:
        config['model'] = model

    print("\n[2] Whisper Model for Speech Recognition")
    print(f"    Current: {config['whisper_model']}")
    print("    Options: tiny.en (fastest), base.en (recommended), small.en (better accuracy)")
    whisper = input("    Enter model (or press Enter to keep current): ").strip()
    if whisper:
        config['whisper_model'] = whisper

    print("\n[3] Voice Quality")
    print(f"    Current: {'High quality (edge-tts)' if config['high_quality_voice'] else 'Offline (pyttsx3)'}")
    print("    High quality requires internet but sounds better")
    hq = input("    Use high quality voice? (y/n, or Enter to keep): ").strip().lower()
    if hq == 'y':
        config['high_quality_voice'] = True
    elif hq == 'n':
        config['high_quality_voice'] = False

    print("\n[4] Weather API Key (optional)")
    print(f"    Current: {'Set' if config['weather_api_key'] else 'Not set'}")
    print("    Get a free key at: https://openweathermap.org/api")
    api_key = input("    Enter API key (or press Enter to skip): ").strip()
    if api_key:
        config['weather_api_key'] = api_key

    if config['weather_api_key']:
        print("\n[5] Default City for Weather")
        print(f"    Current: {config['default_city'] or 'Not set'}")
        city = input("    Enter default city (or press Enter to skip): ").strip()
        if city:
            config['default_city'] = city

    print("\n[6] Default Interface Mode")
    print(f"    Current: {config['default_mode']}")
    mode = input("    Enter 'voice' or 'gui' (or press Enter to keep): ").strip().lower()
    if mode in ['voice', 'gui']:
        config['default_mode'] = mode

    save_config(config)
    print("\n" + "=" * 50)
    print("Configuration saved!")
    print("=" * 50)

    return config


def check_prerequisites():
    """Check if required dependencies are available"""
    issues = []

    try:
        import ollama
        models = ollama.list()
        if not models.get('models'):
            issues.append("No Ollama models found. Run: ollama pull llama3.2:8b")
    except:
        issues.append("Ollama not running. Start it with: ollama serve")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        issues.append("faster-whisper not installed. Run: pip install faster-whisper")

    try:
        import customtkinter
    except ImportError:
        issues.append("customtkinter not installed. Run: pip install customtkinter")

    try:
        import pyttsx3
    except ImportError:
        issues.append("pyttsx3 not installed. Run: pip install pyttsx3")

    return issues


def start_voice_mode(config: dict):
    """Start ARTHUR in voice mode"""
    print("\nStarting A.R.T.H.U.R. in Voice Mode...")
    from .interface.voice_mode import VoiceInterface

    interface = VoiceInterface(config)
    interface.start()


def start_gui_mode(config: dict):
    """Start ARTHUR in GUI mode"""
    print("\nStarting A.R.T.H.U.R. in GUI Mode...")
    from .interface.gui_mode import GUIInterface

    app = GUIInterface(config)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="A.R.T.H.U.R. - Advanced Real-Time Helper and Understanding Resource"
    )
    parser.add_argument('--voice', action='store_true', help='Start in voice-only mode')
    parser.add_argument('--gui', action='store_true', help='Start in GUI mode')
    parser.add_argument('--config', action='store_true', help='Run configuration wizard')
    parser.add_argument('--check', action='store_true', help='Check prerequisites')

    args = parser.parse_args()

    print(r"""
    ___    ____  _________  __  ____  ____
   /   |  / __ \/_  __/ / / / / / / / / _ \
  / /| | / /_/ / / / / /_/ / / / / / /  __/
 / ___ |/ _, _/ / / / __  / / /_/ / /\__ \
/_/  |_/_/ |_| /_/ /_/ /_/  \____/  (___/

   Advanced Real-Time Helper & Understanding Resource
    """)

    if args.check:
        print("Checking prerequisites...")
        issues = check_prerequisites()
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\nAll prerequisites satisfied!")
        return

    if args.config:
        run_config_wizard()
        return

    issues = check_prerequisites()
    if issues:
        print("\nWarning: Some prerequisites may be missing:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRun with --check for full diagnostics, or --config to configure.")
        proceed = input("\nTry to continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return

    config = load_config()

    if args.voice:
        start_voice_mode(config)
    elif args.gui:
        start_gui_mode(config)
    else:
        if config['default_mode'] == 'voice':
            start_voice_mode(config)
        else:
            start_gui_mode(config)


if __name__ == '__main__':
    main()
