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

os.environ["GROQ_API_KEY"] = ""  # API key

engine = pyttsx3.init()


engine.setProperty('rate', 150) 


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
    return emoji_pattern.sub(r'', text)


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
    
    system_content = {
        "english": "You are Krishh Bot, a friendly AI for children. Use simple, positive, and age-appropriate language in English.",
        "malayalam": "നിങ്ങൾ കുട്ടികൾക്കായുള്ള സൗഹൃദ AI ആയ കൃഷ്ണ ബോട്ട് ആണ്. മലയാളത്തിൽ മാത്രം സംസാരിക്കുക. ലളിതവും അനുയോജ്യവുമായ ഭാഷ ഉപയോഗിക്കുക."
    }
    
    
    if language == "malayalam":
        try:
            translator = GoogleTranslator(source='ml', target='en')
            user_input = translator.translate(user_input)
        except:
            print("Translation error, using original input")
    
    data = {
        "model": "gemma2-9b-it",
        "messages": [
            {"role": "system", "content": system_content[language]},
            {"role": "user", "content": user_input}
        ]
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        bot_response = result['choices'][0]['message']['content']
        
       
        if language == "malayalam":
            try:
                translator = GoogleTranslator(source='en', target='ml')
                bot_response = translator.translate(bot_response)
            except:
                print("Translation error, using original response")
        
        bot_response = remove_emojis(bot_response)
        bot_response = add_pauses(bot_response)
        return bot_response
    except Exception as e:
        print(f"API Error: {e}")
        return "Sorry, I encountered an error. Please try again."

recognizer = sr.Recognizer()
microphone = sr.Microphone()

def listen_for_command():
    with microphone as source:
        print("Listening...")
        play_notification() 
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio)
        print(f"Command received: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return ""

def speak_response(response, language="english"):
    if language == "english":
        engine.setProperty('rate', 150)
        engine.say(response)
        engine.runAndWait()
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
        print("Waiting for wake word ('Hey Krishna' for English, 'Hello Krishna' for Malayalam)...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Heard: {command}")
        if "hey krishna" in command:
            return "english"
        elif "hello krishna" in command:
            return "malayalam"
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

def start_chatbot():
    print("Krishna Chatbot Started!")
    print("Say 'Hey Krishna' for English")
    print("Say 'Hello Krishna' for Malayalam")
    print("Say 'Krishna Sleep' to quit")
    
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

        if "krishna sleep" in user_input.lower():
            goodbye = "Goodbye! Say Hey Krishna or Hello Krishna when you need me again."
            speak_response(goodbye, current_language)
            print("Krishna Bot: Goodbye!")
            active_conversation = False
            continue

        bot_response = get_grok_response(user_input, current_language)
        speak_response(bot_response, current_language)
        print(f"You: {user_input}")
        print(f"Krishna Bot: {bot_response}")

if __name__ == "__main__":
    start_chatbot()
