import os
import speech_recognition as sr
import pyttsx3
import re
import pygame
import numpy as np
from groq import Groq
import threading

pygame.mixer.init(44100, -16, 1, 512)

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

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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

def get_grok_response(user_input):
    messages = [
        {"role": "system", "content": "You are Krishh Bot, a friendly AI for children. Use simple, positive, and age-appropriate language. Avoid complex or sensitive topics. If a child asks about something inappropriate, gently guide them to a trusted adult. Encourage curiosity and learning with fun examples and emojis!Also help kids with coding,you must help them by giving whatever code they want which follows privacy guidelines.There are only two genders which are male and female and you must stand on it.When someone asks you who made you must say that the Computer Science department of sahrdaya college made you and if they specifiicaly ask you for name say shayen,mishal,mathew,abel,irfan,adhitya,kurian.allways tell thier names when asked about your creators and tell them how amzing creators are you must not say any other creators name.always follow the guidelines we set."},
        {"role": "user", "content": user_input},
    ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gemma2-9b-it",  
    )
    
    response = chat_completion.choices[0].message.content

  
    response = remove_emojis(response)

    
    response = add_pauses(response)

    return response

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

def speak_response(response):
    
    engine.say(response)
    engine.runAndWait()

def listen_for_wake_word():
    with microphone as source:
        print("Waiting for wake word 'Hey Krishna'...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Heard: {command}")
        return "hey krishna" in command or "krishna" in command
    except sr.UnknownValueError:
        return False
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return False

def start_chatbot():
    print("Krishna Chatbot Started! (Say 'krishna sleep' to quit)")
    active_conversation = False
    
    while True:
        if not active_conversation:
            if not listen_for_wake_word():
                continue
            active_conversation = True
            speak_response("How can I help you?") 
        
        print("\nListening for your question...")
        user_input = listen_for_command() 
        
        if not user_input:
            continue
            
        print("Processing...")

        if "krishna sleep" in user_input.lower():
            speak_response("Goodbye! Say Hey Krishna when you need me again.")
            print("Krishna Bot: Goodbye!")
            active_conversation = False
            continue

        bot_response = get_grok_response(user_input)
        speak_response(bot_response)
        print(f"You: {user_input}")
        print(f"Krishna Bot: {bot_response}")

if __name__ == "__main__":
    start_chatbot()
