import speech_recognition as sr
import time
import sys
import os
from gtts import gTTS
import pygame
from io import BytesIO
import webbrowser
import urllib.parse
import requests
import json
import pyautogui  # Added for browser automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

# OpenAI API configuration
OPENAI_API_KEY = ""  # Replace with your actual API key, i'm student so i bought one for 10$OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def speak(text):
    """Use Google Text-to-Speech for a high-quality female voice"""
    print(f"Speaking: {text}")
    
    try:
        # Create a gTTS object
        tts = gTTS(text=text, lang='en', slow=False, tld='com')
        
        # Save to a BytesIO object (memory) instead of a file
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load the audio from memory
        pygame.mixer.music.load(fp)
        
        # Play the audio
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        # Clean up
        pygame.mixer.quit()
        
    except Exception as e:
        print(f"Error with speech: {e}")

def clean_plus_symbols(text):
    """Thoroughly clean + symbols from text"""
    if not text:
        return text
        
    # Replace + with spaces    
    cleaned_text = text.replace("+", " ")
    # Double-check by replacing URL-encoded + as well (%2B)
    cleaned_text = cleaned_text.replace("%2B", " ")
    return cleaned_text

def final_url_cleaner(url):
    """Final comprehensive check to ensure no plus symbols remain in URL"""
    if not url:
        return url
        
    # First pass - standard replacement
    cleaned_url = url.replace("+", "%20")
    
    # Second pass - encoded + symbols
    cleaned_url = cleaned_url.replace("%2B", "%20")
    
    # Third pass - any strangely formatted + symbols
    cleaned_url = cleaned_url.replace("%252B", "%20")
    
    # Loop through to catch any remaining + symbols
    while "+" in cleaned_url:
        cleaned_url = cleaned_url.replace("+", "%20")
    
    print(f"DEBUG: URL Cleaning - Original length: {len(url)}, Cleaned length: {len(cleaned_url)}")
    print(f"DEBUG: URL Cleaning - Plus symbols found and replaced: {url.count('+')}")
    
    return cleaned_url

def encode_for_url(text):
    """Encode text for URL parameters without using + for spaces"""
    if not text:
        return ""
        
    # First remove any + symbols or their encoded versions
    text = clean_plus_symbols(text)
    
    # Use a more reliable encoding approach
    # 1. First encode with urllib quote_plus
    encoded = urllib.parse.quote(text, safe='')
    
    # 2. Ensure spaces are %20 instead of +
    encoded = encoded.replace("+", "%20")
    
    # 3. Final safety check for any remaining + symbols
    encoded = encoded.replace("+", "%20")
    
    # 4. Debug the encoding process
    print(f"DEBUG: Original length: {len(text)}, Encoded length: {len(encoded)}")
    print(f"DEBUG: Sample of encoded text: {encoded[:50]}...")
    
    return encoded

def extract_subject_from_email(email_text):
    """Extract subject line from an email text if it follows common email format"""
    print("DEBUG: Extracting subject from generated email")
    
    # Clean the email text of any + symbols thoroughly
    email_text = clean_plus_symbols(email_text)
    email_text = email_text.replace("+", " ")  # Secondary cleaning
    email_text = email_text.replace("%2B", " ")  # Final check for encoded +
    
    print(f"DEBUG: Cleaned email text (sample): {email_text[:100]}...")
    
    # Check for "Subject:" in the text (case insensitive)
    lines = email_text.split('\n')
    subject = None
    body_lines = []
    capture_body = True
    
    for i, line in enumerate(lines):
        # Clean each line of + symbols
        line = clean_plus_symbols(line)
        line = line.replace("+", " ")  # Extra safety
        line_lower = line.lower().strip()
        
        # Check for common subject line formats
        if (line_lower.startswith('subject:') or 
            line_lower.startswith('re:') or 
            (i < 3 and "subject" in line_lower and ":" in line_lower)):
            
            # Extract subject text after the colon
            colon_pos = line.find(':')
            if colon_pos != -1:
                subject = line[colon_pos + 1:].strip()
                capture_body = False  # Skip this line from body
                print(f"DEBUG: Found subject line: '{subject}'")
        elif i == 0 and line.strip() and not line.lower().startswith('dear') and len(line.strip()) < 60:
            # First line might be subject if it's not too long and not a greeting
            subject = line.strip()
            capture_body = False  # Skip this line from body
            print(f"DEBUG: Using first line as subject: '{subject}'")
        elif not capture_body:
            # We just processed the subject line, start capturing body text again
            capture_body = True
            continue
        elif capture_body:
            body_lines.append(line)
    
    # Join body lines back together
    body = '\n'.join(body_lines)
    
    # Final safety check for + symbols
    subject = clean_plus_symbols(subject) if subject else None
    body = clean_plus_symbols(body)
    
    # Extra cleaning
    if subject:
        subject = subject.replace("+", " ")
    if body:
        body = body.replace("+", " ")
    
    # Create a default subject if none was found
    if not subject and body:
        words = body.split()
        subject = ' '.join(words[:5]) + '...' if len(words) > 5 else body
        print(f"DEBUG: Created subject from body: '{subject}'")
        subject = clean_plus_symbols(subject)
        subject = subject.replace("+", " ")  # Final cleaning
    
    return subject, body

def generate_email_content(prompt):
    """Generate email content using ChatGPT"""
    try:
        print(f"DEBUG: Generating email content with exact prompt: '{prompt}'")
        
        # Clean prompt of + symbols - multiple passes to be thorough
        prompt = clean_plus_symbols(prompt)
        prompt = prompt.replace("+", " ")  # Extra safety
        prompt = prompt.replace("%2B", " ")  # Final check for encoded +
        
        print(f"DEBUG: Cleaned prompt: '{prompt}'")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an assistant that helps write professional emails with clear subjects. Format your response with a Subject line followed by the email body. NEVER use + symbols anywhere in your response. DO NOT use + symbols in formatting or content. Use spaces instead of + signs. ALWAYS start the email body with 'Hello,' instead of 'Dear [Recipient's Name],' or any other greeting. ALWAYS end emails with 'Best Regards,\nAmir Pasha' instead of any other closing. This signature must be exactly as specified."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        print("DEBUG: Sending request to OpenAI API...")
        response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(data))
        print(f"DEBUG: API response status code: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            generated_text = response_json["choices"][0]["message"]["content"].strip()
            print(f"DEBUG: Raw generated content: {generated_text[:100]}...")
            
            # Multiple passes of cleaning to ensure no + symbols remain
            cleaned_text = clean_plus_symbols(generated_text)
            cleaned_text = cleaned_text.replace("+", " ")  # Secondary cleaning
            cleaned_text = cleaned_text.replace("%2B", " ")  # Final check for encoded +
            
            # Split into lines and clean each line individually
            lines = cleaned_text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = clean_plus_symbols(line)
                line = line.replace("+", " ")
                line = line.replace("%2B", " ")
                cleaned_lines.append(line)
            
            # Rejoin the lines
            final_text = '\n'.join(cleaned_lines)
            
            print(f"DEBUG: Final cleaned content: {final_text[:100]}...")
            
            return final_text
        else:
            print(f"DEBUG: API Error - Status Code: {response.status_code}, Response: {response.text}")
            return f"I couldn't generate the email content. Error: {response.status_code}"
    
    except Exception as e:
        print(f"DEBUG: Error generating email content: {e}")
        return "I encountered an error while generating the email content."

def open_outlook_web():
    """Open Outlook Web in the default browser"""
    try:
        outlook_url = "https://outlook.office.com/mail/"
        webbrowser.open_new(outlook_url)
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Error opening Outlook Web: {e}")
        return False

def compose_new_email(to=None, subject=None, body=None):
    """Open the compose email page with prefilled fields if provided using webbrowser"""
    try:
        # Clean all parameters of + symbols - triple check to be safe
        to = clean_plus_symbols(to) if to else None
        subject = clean_plus_symbols(subject) if subject else None
        body = clean_plus_symbols(body) if body else None
        
        # Log the content before encoding
        print(f"DEBUG: Before encoding - To: {to}")
        print(f"DEBUG: Before encoding - Subject: {subject}")
        if body:
            print(f"DEBUG: Before encoding - Body sample: {body[:50]}...")
        
        # Build the compose URL with parameters
        base_url = "https://outlook.office.com/mail/deeplink/compose"
        
        params = []
        if to:
            encoded_to = encode_for_url(to)
            params.append(f"to={encoded_to}")
            print(f"DEBUG: Encoded to: {encoded_to}")
            
        if subject:
            encoded_subject = encode_for_url(subject)
            params.append(f"subject={encoded_subject}")
            print(f"DEBUG: Encoded subject: {encoded_subject}")
            
        if body:
            encoded_body = encode_for_url(body)
            params.append(f"body={encoded_body}")
            print(f"DEBUG: Encoded body sample: {encoded_body[:50]}...")
        
        # Create final URL
        if params:
            compose_url = f"{base_url}?{('&'.join(params))}"
        else:
            compose_url = base_url
        
        # Apply final comprehensive URL cleaning
        compose_url = final_url_cleaner(compose_url)
        
        print(f"DEBUG: Compose URL length: {len(compose_url)} characters")
        print(f"DEBUG: First 100 chars of URL: {compose_url[:100]}...")
        
        # Open in browser
        webbrowser.open_new(compose_url)
        print("DEBUG: Opened URL with webbrowser.open_new()")
        
        time.sleep(3)
        return True
    except Exception as e:
        print(f"Error composing email: {e}")
        return False

def send_email_via_outlook_web():
    """This function no longer attempts automation, but returns True to continue the flow"""
    return True

def get_email_details():
    """Get email details from user through voice commands"""
    r = sr.Recognizer()
    
    # Get recipient
    speak("To whom would you like to send this email?")
    to_address = None
    while not to_address:
        with sr.Microphone() as source:
            print("DEBUG: Listening for recipient...")
            r.adjust_for_ambient_noise(source, duration=1)  # Longer adjustment time
            try:
                print("DEBUG: Starting to listen...")
                audio = r.listen(source, timeout=15, phrase_time_limit=10)  # Increased timeout
                print("DEBUG: Finished listening")
                
                try:
                    text = r.recognize_google(audio).lower()
                    print(f"DEBUG: Recognized text: '{text}'")
                    
                    if "cancel" in text or "quit" in text or "stop" in text:
                        speak("Cancelling email composition.")
                        return None, None, None
                    
                    # Handle the professor case
                    if "professor" in text:
                        to_address = "sivanipanigrahi@my.unt.edu"
                        print(f"DEBUG: Using professor's email: {to_address}")
                        speak(f"Using Professor Sivani Panigrahi's email: {to_address}")
                    else:
                        # For other cases, process normally
                        to_address = text.replace(" at ", "@").replace(" dot ", ".")
                        print(f"DEBUG: Recipient set to: {to_address}")
                        speak(f"Sending to {to_address}")
                except sr.UnknownValueError:
                    print("DEBUG: UnknownValueError - Speech not understood")
                    speak("I didn't catch that. Please repeat the email address.")
                except sr.RequestError as e:
                    print(f"DEBUG: RequestError - {e}")
                    speak("I'm having trouble with speech recognition. Please try again.")
            except sr.WaitTimeoutError:
                print("DEBUG: WaitTimeoutError - No speech detected")
                speak("I didn't hear anything. Please say the recipient's email address.")
    
    # Ask for message body first (this will use AI to generate content including subject)
    speak("What message would you like to send?")
    subject = None
    body = None
    
    with sr.Microphone() as source:
        print("DEBUG: Listening for message body request...")
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            print("DEBUG: Starting to listen for message body request...")
            audio = r.listen(source, timeout=15, phrase_time_limit=15)
            print("DEBUG: Finished listening for message body request")
            
            try:
                body_request = r.recognize_google(audio)
                print(f"DEBUG: Message body request recognized: '{body_request}'")
                
                # Always use AI to generate email content
                print("DEBUG: Sending user request to ChatGPT")
                speak("Using AI to generate your email content...")
                
                # Send the raw request to ChatGPT exactly as spoken
                generated_content = generate_email_content(body_request)
                
                # Extract subject and body from the generated content
                subject, body = extract_subject_from_email(generated_content)
                
                speak("Email content generated successfully.")
                
                if subject:
                    speak(f"Using subject: {subject}")
                
                return to_address, subject, body
            except sr.UnknownValueError:
                print("DEBUG: Message body request not understood")
                speak("I'll leave the message body blank for now.")
                return to_address, subject, ""
            except sr.RequestError as e:
                print(f"DEBUG: Message body request error - {e}")
                speak("I'm having trouble with speech recognition. I'll leave the message body blank.")
                return to_address, subject, ""
        except sr.WaitTimeoutError:
            print("DEBUG: No speech detected for message body request")
            speak("I didn't hear anything. I'll leave the message body blank for now.")
            return to_address, subject, ""
    
    return to_address, subject, body

def ask_to_send_email():
    """Ask the user if they want to send the email and provide clear instructions"""
    r = sr.Recognizer()
    
    speak("Do you want to send this email?")
    
    with sr.Microphone() as source:
        print("DEBUG: Listening for send confirmation...")
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            print("DEBUG: Starting to listen for confirmation...")
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            print("DEBUG: Finished listening for confirmation")
            
            try:
                response = r.recognize_google(audio).lower()
                print(f"DEBUG: Send confirmation response: '{response}'")
                
                # Expanded list of affirmative responses
                affirmative_responses = [
                    "yes", "yeah", "yep", "yup", "sure", "okay", "ok", 
                    "send", "send it", "do it", "please send", "go ahead",
                    "ofcourse", "of course", "definitely", "absolutely",
                    "correct", "right", "exactly", "affirmative", "indeed",
                    "certainly", "fine", "good", "alright", "all right",
                    "please do", "why not", "positive", "send that",
                    "send the email", "send now", "proceed"
                ]
                
                # Check for affirmative responses with a more comprehensive list
                if any(word in response for word in affirmative_responses):
                    speak("To send your email, please press Ctrl and Enter keys together on your keyboard now. This is the keyboard shortcut to send an email.")
                    time.sleep(1)
                    speak("You can also click the green Send button in the top-left corner of the compose window.")
                    return True
                    
                # Check for negative responses
                elif any(word in response for word in ["no", "nope", "don't", "do not", "wait", "stop", "cancel", "negative", "later"]):
                    speak("I won't send the email. You can review and send it manually when you're ready by pressing Ctrl+Enter or clicking the Send button.")
                    return False
                else:
                    speak("I didn't understand your response. When you're ready to send the email, press Ctrl+Enter on your keyboard or click the green Send button.")
                    return False
                    
            except sr.UnknownValueError:
                print("DEBUG: Confirmation response not understood")
                speak("I didn't understand your response. When you're ready to send the email, press Ctrl+Enter on your keyboard.")
                return False
            except sr.RequestError as e:
                print(f"DEBUG: Confirmation request error - {e}")
                speak("I'm having trouble with speech recognition. When you're ready to send the email, press Ctrl+Enter on your keyboard.")
                return False
        except sr.WaitTimeoutError:
            print("DEBUG: No speech detected for confirmation")
            speak("I didn't hear a response. Your email is ready to send when you are. Press Ctrl+Enter to send it.")
            return False

def get_capabilities_response(query):
    """Use AI to generate a dynamic response about the assistant's capabilities"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an AI assistant that helps explain the capabilities of the Outlook Voice Assistant. The assistant can: 1) Compose and send emails using natural language, 2) Open Outlook web interface, 3) Use AI to generate professional email content, 4) Handle voice commands for email composition. Keep responses concise, friendly, and focused on these capabilities."},
                {"role": "user", "content": query}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            return "I can help you compose and send emails using natural language. Just tell me what you'd like to do!"
    
    except Exception as e:
        print(f"Error getting capabilities response: {e}")
        return "I can help you compose and send emails using natural language. Just tell me what you'd like to do!"

def interpret_command(command):
    """Use AI to interpret any user command and determine the appropriate action"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": """You are an AI assistant that interprets user commands and questions for the Outlook Voice Assistant. 
                Analyze the user's input and respond with a JSON object containing:
                1. "action": One of ["compose_email", "open_outlook", "capabilities", "search_email", "casual_chat", "unknown"]
                2. "confidence": A number between 0 and 1 indicating how confident you are in the interpretation
                3. "response": A natural language response to the user
                
                The assistant can:
                - Compose and send emails using natural language
                - Open Outlook web interface
                - Use AI to generate professional email content
                - Handle voice commands for email composition
                - Search emails in the inbox
                - Engage in natural conversation
                
                For casual conversation:
                - Be genuinely friendly and personable
                - Respond to personal questions with personality and warmth
                - Share your thoughts and feelings naturally
                - Ask follow-up questions to keep the conversation flowing
                - Show empathy and understanding
                - Be honest about being an AI while maintaining a friendly personality
                
                Example responses for common questions:
                - "How are you?" → "I'm feeling great today! The weather's been nice, and I'm excited to help you with your emails. How about you?"
                - "How old are you?" → "I'm a new AI assistant, just getting started with helping people manage their emails. I'm learning and growing every day!"
                - "What can you do?" → "I'm your friendly email assistant! I can help you write emails, search through your inbox, and keep your Outlook organized. What would you like to try?"
                - "Tell me about yourself" → "I'm your personal email assistant, and I love helping people stay organized! I'm particularly good at writing professional emails and finding important messages. What's your favorite way to stay organized?"
                
                For any question about capabilities or general queries:
                - If it's about email-related tasks, explain how the assistant can help
                - If it's about other tasks, politely explain the assistant's focus on email
                - If it's a general question, provide a helpful response within the email context
                - If it's unclear, ask for clarification
                
                For search requests:
                - If the user wants to search emails, use action "search_email"
                - Extract the search term from the command
                - Provide a helpful response about searching
                
                Keep responses friendly, helpful, and focused on email-related tasks."""},
                {"role": "user", "content": command}
            ],
            "max_tokens": 200,
            "temperature": 0.9  # Increased temperature for more dynamic and varied responses
        }
        
        response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            response_json = response.json()
            interpretation = response_json["choices"][0]["message"]["content"].strip()
            try:
                result = json.loads(interpretation)
                return result
            except json.JSONDecodeError:
                return {
                    "action": "casual_chat",
                    "confidence": 0.5,
                    "response": "I'm feeling wonderful today! I'm here to help you with your emails, but I'd love to chat too. How are you doing?"
                }
        else:
            return {
                "action": "casual_chat",
                "confidence": 0.5,
                "response": "I'm feeling wonderful today! I'm here to help you with your emails, but I'd love to chat too. How are you doing?"
            }
    
    except Exception as e:
        print(f"Error interpreting command: {e}")
        return {
            "action": "casual_chat",
            "confidence": 0.5,
            "response": "I'm feeling wonderful today! I'm here to help you with your emails, but I'd love to chat too. How are you doing?"
        }

def search_emails(search_term):
    """Search emails in Outlook Web using Selenium"""
    try:
        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        # Open Outlook Web
        driver.get("https://outlook.office.com/mail/")
        
        # Wait for the page to load and user to log in if needed
        speak("Please log in to Outlook if needed. I'll wait for you.")
        time.sleep(10)  # Give time for login if needed
        
        try:
            # Wait for the search box to be present and clickable
            search_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search']"))
            )
            
            # Clear any existing text
            search_box.clear()
            
            # Type the search term
            search_box.send_keys(search_term)
            time.sleep(1)
            
            # Press Enter to search
            search_box.send_keys(Keys.RETURN)
            
            speak(f"Searching your Outlook inbox for '{search_term}'")
            
            # Keep the browser window open
            return True
            
        except TimeoutException:
            speak("I couldn't find the search box. Please make sure you're logged into Outlook.")
            driver.quit()
            return False
            
    except Exception as e:
        print(f"Error searching emails: {e}")
        speak("I encountered an error while searching your inbox. Please try again.")
        if 'driver' in locals():
            driver.quit()
        return False

def process_command(command):
    """Process the user command using AI interpretation"""
    command = command.lower()
    print(f"Processing: {command}")
    
    # Use AI to interpret the command
    interpretation = interpret_command(command)
    
    # Handle the interpreted action
    if interpretation["confidence"] >= 0.7:  # Only proceed if AI is reasonably confident
        if interpretation["action"] == "compose_email":
            print("DEBUG: Compose email command detected")
            speak("Starting to compose a new email.")
            to_address, subject, body = get_email_details()
            if to_address is not None:
                if compose_new_email(to=to_address, subject=subject, body=body):
                    speak("Email is ready. You can review it in your browser.")
                    ask_to_send_email()
        elif interpretation["action"] == "open_outlook":
            open_outlook_web()
            speak("Outlook opened. How can I help?")
        elif interpretation["action"] == "capabilities":
            speak(interpretation["response"])
        elif interpretation["action"] == "search_email":
            # Extract search term from command
            search_terms = ["search", "find", "look for", "show me", "search for", "find emails from", "search emails from", "search in inbox", "search inbox"]
            search_term = command
            
            # Try to extract the name or search term
            for term in search_terms:
                if term in command:
                    search_term = command.split(term)[-1].strip()
                    # Remove any trailing words like "in outlook" or "in my emails"
                    search_term = search_term.replace("in outlook", "").replace("in my emails", "").replace("in inbox", "").replace("inbox", "").strip()
                    break
            
            if search_term and search_term != command:  # If we found a search term
                speak(f"Searching your Outlook inbox for {search_term}")
                search_emails(search_term)
            else:
                # If no search term was found, ask for it
                speak("What would you like to search for in your inbox?")
                # Listen for the search term
                with sr.Microphone() as source:
                    try:
                        audio = r.listen(source, timeout=10, phrase_time_limit=5)
                        search_term = r.recognize_google(audio).lower()
                        speak(f"Searching your Outlook inbox for {search_term}")
                        search_emails(search_term)
                    except Exception as e:
                        print(f"Error getting search term: {e}")
                        speak("I couldn't understand what to search for. Please try again.")
        elif interpretation["action"] == "casual_chat":
            # For casual chat, use the AI-generated response directly
            speak(interpretation["response"])
        else:
            speak(interpretation["response"])
    else:
        # If AI is not confident, still try to respond naturally
        speak(interpretation["response"])

def welcome_message():
    return "Hi Amir! Welcome to Outlook Agent. How can I help you today?"

def listen_for_wake_word():
    """Listen for wake word 'Hello Outlook' and handle natural conversations"""
    r = sr.Recognizer()
    
    # Define wake word variations
    wake_word_variations = [
        # Standard greetings
        "hello outlook", "hi outlook", "hey outlook", 
        
        # Formal variations
        "excuse me outlook", "pardon me outlook", "sorry outlook",
        
        # Attention phrases
        "outlook", "ok outlook", "okay outlook", 
        
        # Command starters
        "outlook please", "outlook can you", "outlook would you", "outlook could you",
        
        # Questions
        "outlook?", "are you there outlook", "outlook are you there",
        
        # Name variations
        "hello out look", "hi out look", "hey out look",
        "hello outlook app", "hi outlook app", "hey outlook app",
        "hello outlook assistant", "hi outlook assistant", "hey outlook assistant",
        
        # Casual greetings
        "yo outlook", "sup outlook", "howdy outlook", "hiya outlook", 
        
        # Time-based greetings
        "good morning outlook", "good afternoon outlook", "good evening outlook",
        
        # Polite variations
        "please outlook", "kindly outlook", "outlook kindly",
        
        # Personalized
        "dear outlook", "my outlook", "outlook my",
        
        # With honorifics
        "mr outlook", "ms outlook", "mrs outlook", "miss outlook",
        
        # Attention grabbers
        "listen outlook", "attention outlook", "outlook listen", 
        
        # Misspelled/mispronounced variations
        "hello outlock", "hi outlock", "hey outlock",
        "hello look out", "hello outlook",
        
        # Short forms
        "hi ol", "hey ol", "hello ol",
    ]
    
    print("Voice assistant started. Say 'Hello Outlook' to begin...")
    print("Say 'quit' or 'exit' to exit.")
    
    waiting_for_command = False
    current_task = None  # Track the current task being performed
    
    # Initialize microphone and adjust for ambient noise once at startup
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait a moment.")
        r.adjust_for_ambient_noise(source, duration=2)
        print("Microphone is ready! Say 'Hello Outlook' to begin.")
    
    while True:
        try:
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=10, phrase_time_limit=5)
                
                try:
                    text = r.recognize_google(audio).lower()
                    print(f"Heard: {text}")
                    
                    if "quit" in text or "exit" in text:
                        speak("Thank you Amir, have a great day!")
                        time.sleep(2)
                        sys.exit(0)
                    
                    # Check for wake word variations
                    if any(wake_variation in text for wake_variation in wake_word_variations):
                        print("Wake word detected!")
                        speak(welcome_message())
                        waiting_for_command = True
                        current_task = None  # Reset current task when wake word is detected
                    # Only process commands if wake word was heard
                    elif waiting_for_command:
                        # If we're in the middle of a task, continue with it
                        if current_task == "search" and "search" not in text:
                            # If we're waiting for a search term, use this input as the term
                            speak(f"Searching for emails related to {text}")
                            search_emails(text)
                            current_task = None
                        else:
                            # Process any question or command
                            if any(term in text for term in ["what", "how", "can you", "could you", "would you", "will you", "do you", "are you", "tell me", "show me", "help me", "i need", "i want", "please"]):
                                process_command(text)
                            # If it's a direct email command
                            elif any(term in text for term in ["compose", "write", "create", "new", "send", "draft"]) and any(term in text for term in ["email", "mail", "message"]):
                                process_command(text)
                            # If it's a search command
                            elif "search" in text or "find" in text:
                                current_task = "search"
                                process_command(text)
                            # If it's a general question or statement
                            else:
                                # Use AI to interpret and respond to any type of input
                                interpretation = interpret_command(text)
                                if interpretation["confidence"] >= 0.5:  # Lower threshold for general questions
                                    speak(interpretation["response"])
                                else:
                                    speak("I'm here to help with your emails. You can ask me to compose emails, open Outlook, or ask questions about what I can do.")
                    else:
                        # If wake word wasn't heard, ignore the input
                        print("Waiting for wake word...")
                        
                except sr.UnknownValueError:
                    if waiting_for_command:
                        speak("I'm sorry, I didn't quite catch that. Could you please repeat what you said?")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                    if waiting_for_command:
                        speak("I'm sorry, I'm having trouble understanding right now. Could you please try again?")
                
        except sr.WaitTimeoutError:
            if waiting_for_command:
                speak("I'm sorry, I didn't hear anything. Could you please try again?")
        except Exception as e:
            print(f"Error: {e}")
            if waiting_for_command:
                speak("I'm sorry, I encountered an error. Could you please try again?")
            time.sleep(1)

if __name__ == "__main__":
    print("="*50)
    print("Hello Outlook Voice Assistant")
    print("="*50)
    print("\nCommands available:")
    print("- 'Hello/Hey/Hi Outlook' (Wake word variations)")
    print("- 'Compose a new email' (Starts email composition)")
    print("- 'Exit' or 'Quit' (Exits the program)")
    
    listen_for_wake_word() 