from flask import Flask, request, jsonify
from flask_cors import CORS
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
import pyttsx3
import requests
import json
import base64
import io

app = Flask(__name__)
CORS(app)

def record_audio(duration=5, sample_rate=44100, device_index=3):
    print("Recording... Speak now!")
    sd.default.device = device_index
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    return audio_data, sample_rate

def save_audio(audio_data, sample_rate, file_name="input_audio.wav"):
    wav.write(file_name, sample_rate, audio_data)

def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            print("Could not understand the audio!")
            return None
        except sr.RequestError as e:
            print(f"Error with the speech recognition service: {e}")
            return None

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()

def generate_response(input_text, api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": input_text}]}]
    }

    try:
        response = requests.post(f"{url}?key={api_key}", headers=headers, json=payload)
        response_data = response.json()
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
            return response_text
        else:
            return "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate a response."

@app.route('/api/record', methods=['POST'])
def start_recording():
    try:
        # Record audio
        audio_data, sample_rate = record_audio()
        
        # Save audio temporarily
        audio_file = "temp_input.wav"
        save_audio(audio_data, sample_rate, audio_file)
        
        # Convert speech to text
        input_text = speech_to_text(audio_file)
        if input_text is None:
            return jsonify({"error": "Could not understand the audio"}), 400
            
        # Generate response using Gemini
        api_key = "AIzaSyBKVs8yxnUId1Nq3RtzkID66ha1iXW_Ib4"  # Replace with your actual API key
        prompt = f"You are an advanced conversational AI. Current User Input: {input_text}"
        response_text = generate_response(prompt, api_key)
        
        # Convert response to speech
        text_to_speech(response_text)
        
        return jsonify({
            "userText": input_text,
            "botResponse": response_text
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

