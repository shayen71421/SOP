#!/usr/bin/env python
# -- coding: utf-8 --
import os
import speech_recognition as sr
import pyttsx4 as pyttsx3
import re
import pygame
import numpy as np
import threading
import gtts
import playsound
import tempfile
import pygame.mixer
import requests
import json
from deep_translator import GoogleTranslator
import google.generativeai as genai

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

os.environ["GOOGLE_API_KEY"] = ""  # Add your API key here

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

def get_gemini_response(user_input, language="english"):
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    if language == "malayalam":
        try:
            translator = GoogleTranslator(source='ml', target='en')
            user_input_en = translator.translate(user_input)
            
            system_prompt = """You are Krishna Bot, a friendly AI assistant for Malayalam-speaking children.
                             When asked about officials or positions:
                             1. Use simple Malayalam without filler words
                             2. Never use phrases like 'ഒരു തരത്തിൽ' or similar words"""
            
            response = model.generate_content(
                f"{system_prompt}\n\nQuestion: {user_input_en}\nProvide a direct answer:",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=100,
                    top_p=0.1,
                    top_k=1
                )
            )
            
            if not hasattr(response, 'text') or not response.text.strip():
                return "എനിക്ക് ഇപ്പോഴത്തെ വിവരം അറിയില്ല."
            
            try:
                translator = GoogleTranslator(source='en', target='ml')
                bot_response = translator.translate(response.text)
                
                
                unwanted_phrases = [
                    'ഒരു തരത്തിൽ',
                    'തരത്തിൽ',
                    'തരത്തിലുള്ള',
                    'തരത്തിലാണ്',
                    'ഒരുകൂട്ടം',
                    'അദൃശ്യമാണ്'
                ]
                
                for phrase in unwanted_phrases:
                    bot_response = bot_response.replace(phrase, '')
                
                bot_response = remove_emojis(bot_response.strip())
                bot_response = re.sub(r'\s+', ' ', bot_response)
                
                
                bot_response = re.sub(r'\.+', '.', bot_response)
                bot_response = re.sub(r'\s+', ' ', bot_response)
                bot_response = bot_response.strip()
                
                if not bot_response or len(bot_response) < 5:
                    return "എനിക്ക് ഇപ്പോഴത്തെ വിവരം അറിയില്ല."
                
                return bot_response
                
            except Exception as e:
                print(f"Translation error: {str(e)}")
                return "ക്ഷമിക്കണം, ഭാഷാ പരിഭാഷയിൽ പിശക് സംഭവിച്ചു."
                
        except Exception as e:
            print(f"Malayalam processing error: {str(e)}")
            return "ക്ഷമിക്കണം, എന്തോ തകരാർ സംഭവിച്ചു."
    else:
        descriptive_keywords = {
            "english": ["describe", "explain", "tell", "what is", "how does", "tell me about"],
            "malayalam": ["വിവരിക്കുക", "വിശദീകരിക്കുക", "പറയുക", "എന്താണ്", "എങ്ങനെ", "കുറിച്ച് പറയുക", "വിശദമാക്കുക"]
        }
        
        is_descriptive = any(keyword in user_input.lower() for keyword in descriptive_keywords[language])
        
        system_content = {
            "english": """You are Krishna Bot, a friendly AI for children. Use simple, positive, and age-appropriate language in English.
                         For descriptive questions, provide detailed explanations with 3-4 key points.
                         Keep responses engaging but concise.""",
            "malayalam": """നിങ്ങൾ കുട്ടികൾക്കായുള്ള സൗഹൃദ AE ആയ കൃഷ്ണ ബോട്ട് ആണ്.
                           വിശദീകരണം ആവശ്യമുള്ള ചോദ്യങ്ങൾക്ക് 3-4 പ്രധാന കാര്യങ്ങൾ ഉൾപ്പെടുത്തി മറുപടി നൽകുക.
                           ലളിതമായ ഭാഷയിൽ, വ്യക്തമായി ഉത്തരം നൽകുക."""
        }
        
        try:
            prompt = f"{system_content[language]}\n\n{'Provide a detailed explanation about: ' if is_descriptive else ''}{user_input}"
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.6,
                    max_output_tokens=200 if is_descriptive else 100,
                )
            )
            
            if response is None or not hasattr(response, 'text'):
                return "Sorry, I encountered an error. Please try again."
            
            bot_response = response.text
            
            if is_descriptive:
                bot_response = re.sub(r'•\s*', 'First, ', bot_response, count=1)
                bot_response = re.sub(r'•\s*', 'Next, ', bot_response)
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
        print("ചോദ്യം ചോദിക്കൂ..." if current_language == "malayalam" else "Listening...")
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
            print("സമയം കഴിഞ്ഞു. വീണ്ടും ശ്രമിക്കൂ." if current_language == "malayalam" else "Listening timed out. Please try again.")
            return ""
    
    try:
        if current_language == "malayalam":
            try:
                command = recognizer.recognize_google(audio, language='ml-IN')
                print(f"കമാൻഡ് ലഭിച്ചു: {command}")
                return command.lower()
            except sr.UnknownValueError:
                print("ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. വീണ്ടും പറയാമോ?")
                return ""
            except Exception as e:
                print(f"Error: {e}")
                return ""
        else:
            command = recognizer.recognize_google(audio, language='en-US')
            print(f"Command received: {command}")
            return command.lower()
            
    except sr.UnknownValueError:
        print("ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. വീണ്ടും പറയാമോ?" if current_language == "malayalam" else "Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError as e:
        print("വോയ്‌സ് റെക്കഗ്നിഷൻ സേവനവുമായി ബന്ധപ്പെടാൻ കഴിഞ്ഞില്ല." if current_language == "malayalam" else "Could not request results from Speech Recognition service.")
        print(f"Error: {e}")
        return ""

def speak_response(response, language="english"):
    if language == "english":
        try:
            
            tts = gtts.gTTS(text=response, lang='en', tld='co.in')  
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
        print("വേക്ക് വേഡിനായി കാത്തിരിക്കുന്നു...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
        except sr.WaitTimeoutError:
            return None
    
    try:
        try:
            command_en = recognizer.recognize_google(audio, language='en-US').lower()
            print(f"Heard: {command_en}")
            
            english_variations = [
                "hey krishna", "hey krishno", "hi krishna",
                "hey krish"
            ]
            
            if "hello krishna" in command_en:
                return "malayalam"
            elif any(phrase in command_en for phrase in english_variations):
                return "english"
                
        except sr.UnknownValueError:
            pass
        
        try:
            command_ml = recognizer.recognize_google(audio, language='ml-IN').lower()
            print(f"കേട്ടത്: {command_ml}")
            
            malayalam_variations = ["ഹലോ കൃഷ്ണ", "ഹലോ", "കൃഷ്ണ", "ഹലോ കൃഷ്ണാ"]
            if any(word in command_ml for word in malayalam_variations):
                return "malayalam"
        except sr.UnknownValueError:
            pass
        
        return None
        
    except sr.RequestError:
        print("വോയ്‌സ് റെക്കഗ്നിഷൻ സേവനവുമായി ബന്ധപ്പെടാൻ കഴിഞ്ഞില്ല.")
        return None

def start_chatbot():
    global current_language
    print("\n=== കൃഷ്ണ ചാറ്റ്ബോട്ട് ===")
    print("\nവേക്ക് വേഡുകൾ:")
    print("- ഇംഗ്ലീഷിന്: 'Hey Krishna'")
    print ("- മലയാളത്തിന്: 'ഹലോ കൃഷ്ണ' അല്ലെങ്കിൽ 'കൃഷ്ണ'")
    print("- നിർത്താൻ: 'Krishna Sleep' അല്ലെങ്കിൽ 'കൃഷ്ണ സ്ലീപ്'\n")
    
    active_conversation = False
    current_language = None
    
    while True:
        if not active_conversation:
            language = listen_for_wake_word()
            if not language:
                continue
            active_conversation = True
            current_language = language
            greeting = "How can I help you?" if language == "english" else "എന്താണ് സഹായം വേണ്ടത്?"
            speak_response(greeting, current_language)
        
        print("\nListening for your question...")
        user_input = listen_for_command()
        
        if not user_input:
            continue
            
        print("Processing...")

        if any(phrase in user_input.lower() for phrase in ["krishna sleep", "കൃഷ്ണ സ്ലീപ്", "ക്രിഷ്ണ സ്ലീപ്","സ്ലീപ്"]):
            goodbye = "Goodbye! Say Hey Krishna when you need me again." if current_language == "english" else "വിട! വീണ്ടും സഹായം വേണമെങ്കിൽ 'ഹലോ കൃഷ്ണ' എന്ന് വിളിക്കൂ."
            speak_response(goodbye, current_language)
            print("Krishna Bot:", goodbye)
            active_conversation = False
            continue

        bot_response = get_gemini_response(user_input, current_language)
        speak_response(bot_response, current_language)
        print(f"You: {user_input}")
        print(f"Krishna Bot: {bot_response}")

if __name__ == "__main__":
    start_chatbot()