import os
import speech_recognition as sr
import pyttsx3
import string
import re
from groq import Groq
import threading


os.environ["GROQ_API_KEY"] = "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"  # API key

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
        {"role": "system", "content": "You are a helpful assistant."},
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

def start_chatbot():
    print("Krishna Chatbot Started! (Say 'exit' to quit)")
    while True:
        print("\nListening...")
        user_input = listen_for_command()
        print("Processing...")

        if "exit" in user_input:
            speak_response("Goodbye!")
            print("Krishna Bot: Goodbye!")
            break

      
        match = re.match(r"(hey\s*)?(kr[iy]+sh?n[ae]+h*|krishn[ae]+|krsn[ae]+)\s*(.*)", user_input, re.IGNORECASE)

        if match:
            following_input = match.group(3).strip() if match.group(3) else None
            
            if following_input:
                bot_response = get_grok_response(following_input)
                speak_response(bot_response)
                print(f"You: {user_input}")
                print(f"Krishna Bot: {bot_response}")
            else:
                error_msg = "Please provide a command after 'hey krishna'."
                speak_response(error_msg)
                print(f"You: {user_input}")
                print(f"Krishna Bot: {error_msg}")
        else:
            error_msg = "Hey Krishna is not found!"
            speak_response(error_msg)
            print(f"You: {user_input}")
            print(f"Krishna Bot: {error_msg}")

if __name__ == "__main__":
    start_chatbot()
