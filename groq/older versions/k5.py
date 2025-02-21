import os
import speech_recognition as sr
import pyttsx4 as pyttsx3
import re
import pygame
import numpy as np
import threading
import gtts
from playsound import playsound
import tempfile
import pygame.mixer
import requests
import json
from deep_translator import GoogleTranslator

pygame.mixer.init(44100, -16, 2, 2048)

current_language = "english"

def play_notification():
    sample_rate = 44100
    duration = 0.1  
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 1000  
    samples = np.sin(2 * np.pi * frequency * t)
    stereo_samples = np.vstack((samples, samples)).T
    sound_array = np.ascontiguousarray((32767 * stereo_samples).astype(np.int16))
    sound = pygame.sndarray.make_sound(sound_array)
    sound.play()
    pygame.time.wait(int(duration * 1000))

os.environ["GROQ_API_KEY"] = "" # Add your API key here

# engine = pyttsx3.init()
# engine.setProperty('rate', 150)

def remove_emojis(text):
    
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  
        "\U0001F300-\U0001F5FF"  
        "\U0001F680-\U0001F6FF"  
        "\U0001F700-\U0001F77F"  
        "\U0001F780-\U0001F7FF" 
        "\U0001F800-\U0001F8FF"  
        "\U0001F900-\U0001F9FF"  
        "\U0001FA00-\U0001FA6F"  
        "\U0001FA70-\U0001FAFF"  
        "\U00002600-\U000027BF"  
        "]+", flags=re.UNICODE
    )
    
    text = emoji_pattern.sub(r'', text)
  
    text = re.sub(r'\*+', '', text)
    
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def add_pauses(response):
    response = re.sub(r'([.?!])', r'\1\n', response)
    return response

def get_grok_response(user_input, language="english"):
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if language == "malayalam":
        try:
            # Check for elaborate/detailed request keywords
            elaborate_keywords = ["????????", "??????????", "?????????????", "?????? ????"]
            is_elaborate = any(keyword in user_input.lower() for keyword in elaborate_keywords)
            
            # Translate to English
            translator = GoogleTranslator(source='ml', target='en')
            user_input_en = translator.translate(user_input)
            
            system_prompt = """You are Krishna Bot, a friendly AI assistant for Malayalam-speaking children.
                             Keep responses natural and child-friendly.
                             Answer mathematical questions directly.
                             Answer all questions directly
                             Never add words like 'pathanam' or unnecessary text at the end.
                             Give direct, clear answers."""
            
            data = {
                "model": "gemma2-9b-it",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input_en}
                ],
                "temperature": 0.3,
                "max_tokens": 150 if is_elaborate else 100
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            english_response = result['choices'][0]['message']['content']
            
            # Translate back to Malayalam
            translator = GoogleTranslator(source='en', target='ml')
            bot_response = translator.translate(english_response)
            
            # Clean up response
            bot_response = remove_emojis(bot_response.strip())
            bot_response = bot_response.replace('  ', ' ')
            bot_response = bot_response.replace('????', '')  # Remove "pathanam" if present
            
            return bot_response.strip()
            
        except Exception as e:
            print(f"Error in Malayalam processing: {e}")
            return "??????????, ????? ????? ?????????. ??????? ????????????"

    else:
        # Rest of the English handling code remains the same
        descriptive_keywords = {
            "english": ["oi"],
            "malayalam": ["??????????", "?????????????", "?????", "???????", "??????", "???????? ?????", "???????????"]
        }
        
        
        is_descriptive = any(keyword in user_input.lower() for keyword in descriptive_keywords[language])
        
        system_content = {
            "english": """You are Krishna Bot, a friendly AI for children. Use simple, positive, and age-appropriate language in English.
                         For descriptive questions, provide detailed explanations with 3-4 key points.
                         Keep responses engaging but concise.""",
            "malayalam": """?????? ????????????????? ????? AE ?? ????? ?????? ???.
                           ????????? ?????????? ????????????? 3-4 ?????? ????????? ???????????? ?????? ?????.
                           ??????? ??????, ?????????? ?????? ?????."""
        }
        
        max_tokens = 600 if is_descriptive else 300
        data = {
            "model": "gemma2-9b-it",
            "messages": [
                {"role": "system", "content": system_content[language]},
                {"role": "user", "content": f"{'Provide a detailed explanation about: ' if is_descriptive else ''}{user_input}"}
            ],
            "temperature": 0.6,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            bot_response = result['choices'][0]['message']['content']
            
            
            if is_descriptive:
                
                bot_response = re.sub(r'?\s*', 'First, ', bot_response, count=1)
                bot_response = re.sub(r'?\s*', 'Next, ', bot_response)
                bot_response = re.sub(r'(\d+)\.\s*', r'Point \1: ', bot_response)
                bot_response = bot_response.replace('. ', '.\n')
            
            bot_response = remove_emojis(bot_response)
            return bot_response
        except Exception as e:
            print(f"API Error: {e}")
            return "Sorry, I encountered an error. Please try again."

recognizer = sr.Recognizer()
microphone = sr.Microphone()

def listen_for_command():
    with microphone as source:
        print("?????? ????????..." if current_language == "malayalam" else "Listening...")
        play_notification()
        recognizer.adjust_for_ambient_noise(source, duration=2)
        
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 2.0
        recognizer.phrase_threshold = 0.2
        recognizer.dynamic_energy_threshold = True
        
        try:
            audio = recognizer.listen(
                source, 
                timeout=10.0,
                phrase_time_limit=10.0,
                snowboy_configuration=None
            )
        except sr.WaitTimeoutError:
            print("???? ???????. ??????? ?????????." if current_language == "malayalam" else "Listening timed out. Please try again.")
            return ""
    
    try:
        if current_language == "malayalam":
            try:
                command = recognizer.recognize_google(audio, language='ml-IN')
                print(f"?????? ???????: {command}")
                return command.lower()
            except sr.UnknownValueError:
                print("??????????, ??????? ?????????????. ??????? ???????")
                return ""
            except Exception as e:
                print(f"Error: {e}")
                return ""
        else:
            command = recognizer.recognize_google(audio, language='en-US')
            print(f"Command received: {command}")
            return command.lower()
            
    except sr.UnknownValueError:
        print("??????????, ??????? ?????????????. ??????? ???????" if current_language == "malayalam" else "Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError:
        print("??????? ??????????? ?????????? ??????????? ??????????." if current_language == "malayalam" else "Could not request results from Speech Recognition service.")
        return ""

def speak_response(response, language="english"):
    if language == "english":
        try:
            # Use Google TTS with Indian English accent
            tts = gtts.gTTS(text=response, lang='en', tld='co.in')  # tld='co.in' for Indian English
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, 'temp_audio.mp3')
            tts.save(temp_file)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            try:
                os.remove(temp_file)
            except:
                pass
        except Exception as e:
            print(f"English TTS Error: {str(e)}")
            return
    else:
        try:
            tts = gtts.gTTS(text=response, lang='ml', slow=False)
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, 'temp_audio.mp3')
            tts.save(temp_file)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            try:
                os.remove(temp_file)
            except:
                pass
        except Exception as e:
            print(f"Malayalam TTS Error: {str(e)}")
            return

def listen_for_wake_word():
    with microphone as source:
        print("?????? ???????? ????????????????...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        try:
            command_en = recognizer.recognize_google(audio, language='en-US').lower()
            print(f"Heard: {command_en}")
            
            english_variations = [
                "hey krishna", "hey krishno", "hi krishna",
                "hey krish", "hi krish"
            ]
            
            if "hello krishna" in command_en:
                return "malayalam"
            elif any(phrase in command_en for phrase in english_variations):
                return "english"
                
        except sr.UnknownValueError:
            pass
        
        try:
            command_ml = recognizer.recognize_google(audio, language='ml-IN').lower()
            print(f"???????: {command_ml}")
            
            malayalam_variations = ["??? ?????", "???", "?????", "??? ??????"]
            if any(word in command_ml for word in malayalam_variations):
                return "malayalam"
        except:
            pass
        
        return None
        
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("??????? ??????????? ?????????? ??????????? ??????????.")
        return None

def start_chatbot():
    global current_language
    print("\n=== ????? ???????????? ===")
    print("\n?????? ??????:")
    print("- ??????????: 'Hey Krishna'")
    print ("- ???????????: '??? ?????' ?????????? '?????'")
    print("- ????????: 'Krishna Sleep' ?????????? '????? ??????'\n")
    
    active_conversation = False
    current_language = None
    
    while True:
        if not active_conversation:
            language = listen_for_wake_word()
            if not language:
                continue
            active_conversation = True
            current_language = language
            greeting = "How can I help you?" if language == "english" else "??????? ????? ????????"
            speak_response(greeting, current_language)
        
        print("\nListening for your question...")
        user_input = listen_for_command()
        
        if not user_input:
            continue
            
        print("Processing...")

        if any(phrase in user_input.lower() for phrase in ["krishna sleep", "????? ??????", "??????? ??????","??????"]):
            goodbye = "Goodbye! Say Hey Krishna when you need me again." if current_language == "english" else "???! ??????? ????? ?????????? '??? ?????' ????? ????????."
            speak_response(goodbye, current_language)
            print("Krishna Bot:", goodbye)
            active_conversation = False
            continue

        bot_response = get_grok_response(user_input, current_language)
        speak_response(bot_response, current_language)
        print(f"You: {user_input}")
        print(f"Krishna Bot: {bot_response}")

if __name__ == "__main__":
    start_chatbot()

