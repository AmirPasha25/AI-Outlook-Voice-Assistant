# Hello Outlook Voice Assistant

A Python-based voice assistant that continuously listens for the wake word "Hello Outlook" and responds with a greeting.

## Setup

1. Make sure you have Python 3.6 or later installed.

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

   Or install them individually:
   ```
   pip install SpeechRecognition pyttsx3 pyaudio
   ```

   Note: PyAudio installation might require additional steps depending on your OS:
   - On Windows: `pip install pyaudio` should work directly
   - On macOS: You might need to install portaudio first with `brew install portaudio` 
   - On Linux: You might need to install portaudio and python-dev packages first

## Usage

Simply run the Python script and it will start listening immediately:

```
python voice_assistant.py
```

When the assistant hears "Hello Outlook", it will respond with "Hi there, how are you? How can I help you today?"

Press Ctrl+C to exit the program. 