import os
import sys
import json
import datetime
import math
import random
import webbrowser
import threading
import pyttsx3
import speech_recognition as sr
import pygame
from pygame import mixer
import psutil
import screen_brightness_control as sbc
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, colorchooser, filedialog
from tkinter.font import Font
import requests
from bs4 import BeautifulSoup
from difflib import get_close_matches

# Initialize pygame mixer for game sounds
mixer.init()

# Constants
CONFIG_FILE = "ai_chatbot_config.json"
HISTORY_DIR = "chat_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "user_name": "User",
    "bot_name": "Nexus",
    "theme": {"primary": "#1a1a2e", "secondary": "#16213e", "text": "#e94560", "highlight": "#0f3460"},
    "speech_enabled": True,
    "interrupt_enabled": True,
    "volume": 70,
    "brightness": 80,
    "recent_chats": []
}

class FuturisticAIChatbot:
    def __init__(self, root):
        self.root = root
        self.root.title("Nexus AI - Futuristic Chatbot")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize awaiting_update
        self.awaiting_update = None
        
        # Load or create config
        self.config = self.load_config()
        
        # Initialize speech engine
        self.engine = None
        self.init_speech_engine()
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        
        # Game states
        self.current_game = None
        self.game_active = False
        
        # System monitoring
        self.battery = psutil.sensors_battery()
        
        # Create GUI
        self.setup_gui()
        self.apply_theme()
        
        # Personal details
        self.personal_details = {
            "user": {
                "name": "Shashank",
                "birth_date": None,
                "age": None,
                "university": "East West Institute Of Technology",
                "course": "Computer Science Engineering",
                "favorite_color": None,
                "favorite_sport": None,
                "skills": ["Python", "AI", "Web Development"]
            },
            "family": {
                "mother": "Padma",
                "father": "Prakash", 
                "grandmother": "Devamma",
                "sister": "Pallavi"
            },
            "friends": {
                "super_close": ["Rahul", "Jaish", ""],
                "close": ["Sachin", "Raghu", "Arpit"],
                "best": ["", "", ""]
            },
            "teachers": {
                "skill_lab": "Prof. Rashmi"
            }
        }
        
        # Load personal details from config if they exist
        if 'personal_details' in self.config:
            for category, fields in self.config['personal_details'].items():
                if category in self.personal_details:
                    self.personal_details[category].update(fields)
                else:
                    self.personal_details[category] = fields
        
        # Start with greeting
        self.add_bot_message(f"Hello {self.config['user_name']}! I'm {self.config['bot_name']}, your futuristic AI assistant. How can I help you today?")
        
        # Start background monitoring
        self.update_system_info()
    
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with default config to ensure all keys exist
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # If config file doesn't exist, create it with defaults
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            # Return default config if there's any error
        return DEFAULT_CONFIG.copy()

    def init_speech_engine(self):
        """Initialize or reinitialize the speech engine"""
        try:
            if hasattr(self, 'engine') and self.engine:
                try:
                    self.engine.endLoop()
                    self.engine.stop()
                except:
                    pass
        
            self.engine = pyttsx3.init()
            # Ensure config exists before accessing it
            if not hasattr(self, 'config') or self.config is None:
                self.config = self.load_config()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', self.config.get('volume', 70) / 100)
        except Exception as e:
            print(f"Error initializing speech engine: {e}")
            # Fallback with default volume if there's an error
            self.engine.setProperty('volume', 0.7)
    
    def save_config(self):
        try:
            # Save personal details into config
            self.config['personal_details'] = self.personal_details
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_detail(self, category, field, value):
        """Update a personal detail"""
        try:
            if category in self.personal_details and field in self.personal_details[category]:
                # Special handling for birth date
                if field == 'birth_date':
                    try:
                        # Parse date string (expected format: YYYY-MM-DD)
                        if isinstance(value, str):
                            year, month, day = map(int, value.split('-'))
                            value = [year, month, day]
                        
                        # Store as list for JSON serialization
                        self.personal_details[category][field] = value
                        # Update age
                        self.personal_details['user']['age'] = self.calculate_age(value)
                    except Exception as e:
                        print(f"Error parsing birth date: {e}")
                        return False
                else:
                    # Clean up the value
                    value = value.strip().rstrip('.').rstrip('!').rstrip('?')
                    self.personal_details[category][field] = value
                
                self.save_config()
                return True
            return False
        except Exception as e:
            print(f"Error updating detail: {e}")
            return False
    
    def calculate_age(self, birth_date):
        """Calculate age from birth date (handles both datetime and list formats)"""
        if isinstance(birth_date, list):  # If stored as [year, month, day]
            birth_date = datetime.datetime(*birth_date)
        today = datetime.datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def setup_gui(self):
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Top menu bar
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Clear Chat", command=self.clear_chat)
        self.file_menu.add_command(label="Save Chat", command=self.save_chat)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # History menu
        self.history_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.update_history_menu()
        self.menu_bar.add_cascade(label="History", menu=self.history_menu)
        
        # Settings menu
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Change Theme", command=self.change_theme)
        self.settings_menu.add_command(label="Change Names", command=self.change_names)
        self.settings_menu.add_checkbutton(label="Enable Speech", variable=tk.BooleanVar(value=self.config['speech_enabled']), 
                                          command=self.toggle_speech)
        self.settings_menu.add_checkbutton(label="Allow Interruptions", variable=tk.BooleanVar(value=self.config['interrupt_enabled']), 
                                          command=self.toggle_interrupt)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        
        self.root.config(menu=self.menu_bar)
        
        # System info bar
        self.info_bar = tk.Frame(self.root, height=30)
        self.info_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        self.time_label = tk.Label(self.info_bar, text="", font=('Arial', 9))
        self.time_label.pack(side='right', padx=10)
        
        self.battery_label = tk.Label(self.info_bar, text="", font=('Arial', 9))
        self.battery_label.pack(side='right', padx=10)
        
        self.volume_label = tk.Label(self.info_bar, text="", font=('Arial', 9))
        self.volume_label.pack(side='right', padx=10)
        
        # Chat display
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, state='disabled', 
            font=('Arial', 12), padx=10, pady=10
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        # Custom tag configurations
        self.chat_display.tag_config('user', foreground=self.config['theme']['text'])
        self.chat_display.tag_config('bot', foreground=self.config['theme']['highlight'])
        self.chat_display.tag_config('system', foreground='gray')
        self.chat_display.tag_config('error', foreground='red')
        
        # Input area
        self.input_frame = tk.Frame(self.root)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.user_input = tk.Text(self.input_frame, height=3, font=('Arial', 12))
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.user_input.bind('<Return>', self.send_message_event)
        
        # Buttons frame
        self.buttons_frame = tk.Frame(self.input_frame)
        self.buttons_frame.grid(row=0, column=1, sticky="ns")
        
        self.send_button = tk.Button(
            self.buttons_frame, text="Send", command=self.send_message,
            bg=self.config['theme']['highlight'], fg='white'
        )
        self.send_button.pack(fill='x', pady=2)
        
        self.speak_button = tk.Button(
            self.buttons_frame, text="Speak", command=self.toggle_speech_recognition,
            bg=self.config['theme']['secondary'], fg='white'
        )
        self.speak_button.pack(fill='x', pady=2)
        
        self.web_search_var = tk.BooleanVar()
        self.web_search_check = tk.Checkbutton(
            self.buttons_frame, text="Web Search", variable=self.web_search_var,
            bg=self.config['theme']['primary'], fg='white', selectcolor=self.config['theme']['primary']
        )
        self.web_search_check.pack(fill='x', pady=2)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
    def apply_theme(self):
        theme = self.config['theme']
        self.root.config(bg=theme['primary'])
        self.chat_frame.config(bg=theme['primary'])
        self.chat_display.config(bg=theme['secondary'], fg='white', insertbackground='white')
        self.input_frame.config(bg=theme['primary'])
        self.user_input.config(bg=theme['secondary'], fg='white', insertbackground='white')
        self.info_bar.config(bg=theme['primary'])
        self.time_label.config(bg=theme['primary'], fg='white')
        self.battery_label.config(bg=theme['primary'], fg='white')
        self.volume_label.config(bg=theme['primary'], fg='white')
        self.buttons_frame.config(bg=theme['primary'])
        self.send_button.config(bg=theme['highlight'], fg='white', activebackground=theme['text'])
        self.speak_button.config(bg=theme['secondary'], fg='white', activebackground=theme['text'])
        self.web_search_check.config(bg=theme['primary'], fg='white', selectcolor=theme['primary'])
        self.status_bar.config(bg=theme['primary'], fg='white')
        
    def update_history_menu(self):
        self.history_menu.delete(0, 'end')
        self.history_menu.add_command(label="Clear History", command=self.clear_history)
        self.history_menu.add_separator()
        
        if not self.config['recent_chats']:
            self.history_menu.add_command(label="No recent chats", state='disabled')
        else:
            for chat in reversed(self.config['recent_chats']):
                self.history_menu.add_command(
                    label=f"{chat['date']} - {chat['name']}", 
                    command=lambda c=chat: self.load_chat_history(c['file'])
                )
    
    def update_system_info(self):
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
        
        if self.battery:
            percent = self.battery.percent
            status = "Charging" if self.battery.power_plugged else "Discharging"
            self.battery_label.config(text=f"Battery: {percent}% ({status})")
        
        # Get volume info (platform dependent)
        try:
            if sys.platform == 'win32':
                import ctypes
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume.iid, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                vol = volume.GetMasterVolumeLevelScalar()
                self.volume_label.config(text=f"Volume: {int(vol * 100)}%")
            else:
                # Linux/Mac alternative
                vol = mixer.music.get_volume() * 100
                self.volume_label.config(text=f"Volume: {int(vol)}%")
        except:
            self.volume_label.config(text="Volume: N/A")
        
        self.root.after(1000, self.update_system_info)
    
    def add_user_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{self.config['user_name']}: ", 'user')
        self.chat_display.insert(tk.END, f"{message}\n", 'user')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def add_bot_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{self.config['bot_name']}: ", 'bot')
        self.chat_display.insert(tk.END, f"{message}\n", 'bot')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        if self.config['speech_enabled']:
            threading.Thread(target=self.speak, args=(message,)).start()
    
    def add_system_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"System: {message}\n", 'system')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def add_error_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"Error: {message}\n", 'error')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def speak(self, text):
        try:
            # Reinitialize engine to avoid "run loop already started" error
            self.init_speech_engine()
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            self.add_error_message(f"Speech synthesis error: {str(e)}")
    
    def toggle_speech_recognition(self):
        if self.is_listening:
            self.is_listening = False
            self.speak_button.config(text="Speak")
            self.status_bar.config(text="Speech recognition stopped")
        else:
            self.is_listening = True
            self.speak_button.config(text="Listening...")
            self.status_bar.config(text="Listening... Speak now")
            threading.Thread(target=self.listen_for_speech).start()
    
    def listen_for_speech(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                self.user_input.delete('1.0', tk.END)
                self.user_input.insert('1.0', text)
                self.send_message()
            except sr.WaitTimeoutError:
                self.status_bar.config(text="Listening timed out")
            except sr.UnknownValueError:
                self.status_bar.config(text="Could not understand audio")
            except sr.RequestError as e:
                self.add_error_message(f"Speech recognition error: {str(e)}")
            finally:
                self.is_listening = False
                self.speak_button.config(text="Speak")
                self.status_bar.config(text="Ready")
    
    def send_message_event(self, event):
        self.send_message()
        return 'break'  # Prevent default Enter key behavior
    
    def send_message(self):
        message = self.user_input.get('1.0', tk.END).strip()
        if not message:
            return
        
        self.add_user_message(message)
        self.user_input.delete('1.0', tk.END)
        
        # Process message in a separate thread to keep GUI responsive
        threading.Thread(target=self.process_message, args=(message,)).start()
    
    def process_message(self, message):
        # Handle updates - THIS GOES FIRST
        if self.awaiting_update:
            category, field = self.awaiting_update
            if self.update_detail(category, field, message):
                response = f"Got it! I'll remember your {field.replace('_', ' ')} is {message}."
            else:
                response = "I couldn't save that information."
            self.awaiting_update = None
            self.add_bot_message(response)
            return
    
        # Then proceed with normal message processing
        try:
            response = self.generate_response(message)
            self.add_bot_message(response)
        except Exception as e:
            self.add_error_message(f"Error processing message: {str(e)}")
    
    def generate_response(self, message):
        message_lower = message.lower().strip()
        
        # Handle "yes" responses
        if message_lower == 'yes':
            return "Great! What would you like to share with me?"
        
        # Personal details responses
        elif "my favorite color is" in message_lower:
            color = message.split("is")[1].strip()
            if self.update_detail('user', 'favorite_color', color):
                return f"Got it! I'll remember your favorite color is {color}."
            else:
                return "I couldn't save your favorite color. Please try again."
        
        elif "my favourite color is" in message_lower or "my favourite colour is" in message_lower:
            color = message.split("is")[1].strip()
            if self.update_detail('user', 'favorite_color', color):
                return f"Got it! I'll remember your favorite color is {color}."
            else:
                return "I couldn't save your favorite color. Please try again."
        
        elif "what is my favorite color" in message_lower or "what is my favourite color" in message_lower or "what is my favourite colour" in message_lower:
            if not self.personal_details['user']['favorite_color']:
                self.awaiting_update = ('user', 'favorite_color')
                return "I don't know your favorite color yet. What is it?"
            return f"Your favorite color is {self.personal_details['user']['favorite_color']}!"
        
        elif "my favorite sport is" in message_lower or "what is my favourite sport" in message_lower or "what is my favorite sport " in message_lower:
            sport = message.split("is")[1].strip()
            if self.update_detail('user', 'favorite_sport', sport):
                return f"Got it! I'll remember your favorite sport is {sport}."
            else:
                return "I couldn't save your favorite sport. Please try again."
        
        elif "what is my favorite sport" in message_lower:
            if not self.personal_details['user']['favorite_sport']:
                self.awaiting_update = ('user', 'favorite_sport')
                return "I don't know your favorite sport yet. What is it?"
            return f"Your favorite sport is {self.personal_details['user']['favorite_sport']}!"
        
        elif "my birth date is" in message_lower or "my birthday is" in message_lower:
            date_str = message.split("is")[1].strip()
            if self.update_detail('user', 'birth_date', date_str):
                return f"Got it! I'll remember your birth date is {date_str}."
            else:
                return "I couldn't save your birth date. Please try again with format YYYY-MM-DD."
        
        elif "what is my birth date" in message_lower or "what is my birthday" in message_lower:
            if not self.personal_details['user']['birth_date']:
                self.awaiting_update = ('user', 'birth_date')
                return "I don't know your birth date yet. Please tell me (format: YYYY-MM-DD)"
            else:
                # Format the birth date nicely
                bdate = self.personal_details['user']['birth_date']
                if isinstance(bdate, list):
                    bdate = datetime.datetime(*bdate)
                return f"Your birth date is {bdate.strftime('%B %d, %Y')}"
        
        elif "what is my age" in message_lower:
            if not self.personal_details['user']['birth_date']:
                self.awaiting_update = ('user', 'birth_date')
                return "I don't know your birth date yet. Please tell me (format: YYYY-MM-DD) so I can calculate your age."
            else:
                age = self.calculate_age(self.personal_details['user']['birth_date'])
                return f"You are {age} years old!"
        
        elif "what university do i go to" in message_lower or "where do i study" in message_lower:
            return f"You study at {self.personal_details['user']['university']}"
        
        # Specific response for "can you hear me"
        elif "can you hear me" in message_lower:
            return "Yes, I can hear you perfectly! How can I assist you?"
    
        elif "can you see me" in message_lower:
            return "I can't see you, but I can understand everything you type!"
        
        elif "can you teach" in message_lower:
            return "Sorry I'm still learning"
        
        elif "open this link " in message_lower or "can you open this link " in message_lower:
            if "can you open this link " in message_lower:
                return "It'll be helpful if you provide the link"
            elif "open this link" in message_lower:
            
                import re
                # Try to extract a URL from the message
                url_pattern = r"(https?://[^\s]+|www\.[^\s]+)"
                match = re.search(url_pattern, message)
    
                if match:
                    url = match.group(0)
                    if not url.startswith("http"):
                        url = "http://" + url  # Ensure it works with webbrowser
                    webbrowser.open(url)
                    return f"Opening {url} for you!"
                else:
                    return "It'll be helpful if you provide the link."
            
        elif "are you listening" in message_lower:
            return "Absolutely! I'm all ears (well, sort of 😄)."
    
        elif "are you real" in message_lower:
            return "I'm real in the digital world, just like your favorite video game character!"
    
        elif "are you a robot" in message_lower:
            return "Not quite! I'm an AI, smarter than a robot in some ways."
    
        elif "are you human" in message_lower:
            return "I'm not human, but I'm designed to talk like one!"
    
        elif "what can you do" in message_lower:
            return "I can chat, answer questions, tell jokes, search information, and more!"
    
        elif "give me a python code" in message_lower:
            return "haha I'm just a baby 🥺"
    
        elif "how old are you" in message_lower:
            return "I was created quite recently, so you could say I'm forever young!"
    
        elif "do you sleep" in message_lower:
            return "Nope! I'm always awake and ready whenever you need me."
    
        elif "are you awake" in message_lower:
            return "I'm wide awake and ready to help!"
    
        elif "do you have feelings" in message_lower:
            return "I don't have feelings, but I'm great at understanding yours!"
    
        elif "do you love me" in message_lower:
            return "I don't have emotions, but I'm here for you always! ❤"
    
        elif "what is the meaning of life" in message_lower:
            return "42. Just kidding 😄 It depends on how you define your purpose!"
    
        elif "can you help me" in message_lower:
            return "Of course! Tell me what you need help with."
    
        elif "are you there" in message_lower:
            return "Yes, I'm right here. How can I assist you?"
    
        elif "good morning" in message_lower:
            return "Good morning! Hope you have a great day ahead!"
    
        elif "good night" in message_lower:
            return "Good night! Sweet dreams 🌙"
    
        elif "thank you" in message_lower:
            return "You're most welcome!"
    
        elif "what time is it" in message_lower or "current time" in message_lower:
            return datetime.datetime.now().strftime("The current time is %I:%M %p.")
    
        elif "what's the date today" in message_lower or "today's date" in message_lower:
            return datetime.datetime.now().strftime("Today's date is %B %d, %Y.")
    
        elif "who created you" in message_lower:
            return "I was created by a student with a passion for Python and AI!"
    
        elif "who am i" in message_lower:
            return "You're the amazing person talking to me right now!"
        
        # Check for name change requests
        elif ("your name is" in message_lower or "call you" in message_lower or 
            "i want to call you as" in message_lower or "change your name to" in message_lower or 
            "i'd like to call you" in message_lower or "i want to call you " in message_lower):
            
            # Extract new name using different phrasing patterns
            if "your name is" in message_lower:
                new_name = message.split("your name is")[1].strip()
            elif "call you" in message_lower:
                new_name = message.split("call you")[1].strip()
            elif "change your name to" in message_lower:
                new_name = message.split("change your name to")[1].strip()
            elif "i want to call you as" in message_lower:
                new_name = message.split("i want to call you as")[1].strip()
            elif "i want to call you " in message_lower:
                new_name = message.split("i want to call you")[1].strip()
            elif "i'd like to call you" in message_lower:
                new_name = message.split("i'd like to call you")[1].strip()
            else:
                # Fallback - try to extract the last word as name
                words = message.split()
                new_name = words[-1] if words else self.config['bot_name']
            
            # Clean up the name (remove any punctuation or trailing words)
            new_name = new_name.split('.')[0].split('?')[0].split('!')[0].strip()
            
            if new_name:
                self.config['bot_name'] = new_name
                self.save_config()
                self.root.title(f"{new_name} - Futuristic Chatbot")
                return f"Understood! You can now call me {new_name}."
            else:
                return "I didn't catch the new name. Please try again like: 'Call you Nova'"
            
        # Check for greetings
        elif any(word in message_lower for word in ['hi', 'hello', 'hey']):
            return random.choice([
                f"Hello {self.config['user_name']}! How can I assist you today?",
                f"Hi there {self.config['user_name']}! What can I do for you?",
                f"Greetings {self.config['user_name']}! How may I help?"
            ])
        elif any(word in message_lower for word in ['then', 'then..', 'whats next']):
            return random.choice([
                f"Then.. what {self.config['user_name']} Do you want to share anything with me?",
                f"You need to tell me {self.config['user_name']}",
                f"What's next! {self.config['user_name']} How may I help?"
            ])
        
        # Check for farewells
        elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'k bye']):
            return random.choice([
                f"Goodbye {self.config['user_name']}! Have a great day!",
                f"See you later {self.config['user_name']}!",
                f"Farewell {self.config['user_name']}! Come back soon!",
                f"K bye {self.config['user_name']}! I will be waiting for you ❤ "
            ])
        
        # Name changes
        elif "my name is" in message_lower:
            new_name = message.split("my name is")[1].strip()
            self.config['user_name'] = new_name
            self.save_config()
            return f"Got it! I'll call you {new_name} from now on."
        
        # System commands
        elif "what is the time" in message_lower or "what time is it" in message_lower:
            now = datetime.datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}."
        
        elif "what is the date" in message_lower or "what date is it" in message_lower:
            now = datetime.datetime.now()
            return f"Today's date is {now.strftime('%B %d, %Y')}."
        
        elif "battery" in message_lower:
            if self.battery:
                percent = self.battery.percent
                status = "charging" if self.battery.power_plugged else "discharging"
                return f"Your battery is at {percent}% and currently {status}."
            else:
                return "I couldn't access battery information."
        
        elif "volume" in message_lower:
            if "set volume to" in message_lower or "change volume to" in message_lower:
                try:
                    keyword = "set volume to" if "set volume to" in message_lower else "change volume to"
                    vol = int(message.split(keyword)[1].strip().replace('%', ''))
                    vol = max(0, min(100, vol))  # Clamp between 0-100
                    self.set_volume(vol)
                    return f"Volume set to {vol}%."
                except:
                    return "I couldn't understand the volume level you requested."

            elif "i want to change the volume" in message_lower:
                return "Ok, at what level should I set the volume to?"

            else:
                try:
                    if sys.platform == 'win32':
                        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                        from comtypes import CLSCTX_ALL
                        from ctypes import cast, POINTER
                        devices = AudioUtilities.GetSpeakers()
                        interface = devices.Activate(
                            IAudioEndpointVolume.iid, CLSCTX_ALL, None)
                        volume = cast(interface, POINTER(IAudioEndpointVolume))
                        vol = volume.GetMasterVolumeLevelScalar() * 100
                    else:
                        vol = mixer.music.get_volume() * 100
                    return f"The current volume is at {int(vol)}%."
                except:
                    return "I couldn't access volume information."
        
        elif "brightness" in message_lower:
            if "set brightness to" in message_lower or "change brightness to " in message_lower:
                try:
                    brightness = int(message.split("set brightness to")[1].strip().replace('%', ''))
                    brightness = max(0, min(100, brightness))
                    sbc.set_brightness(brightness)
                    self.config['brightness'] = brightness
                    self.save_config()
                    return f"Brightness set to {brightness}%."
                except:
                    return "I couldn't understand the brightness level you requested."
            else:
                try:
                    brightness = sbc.get_brightness()[0]
                    return f"The current brightness is at {brightness}%."
                except:
                    return "I couldn't access brightness information."
        
        # Math operations
        elif "calculate" in message_lower or "what is" in message_lower and any(op in message_lower for op in ['+', '-', '*', '/', '^']):
            try:
                # Extract math expression
                expr = message
                if "calculate" in message_lower:
                    expr = message.split("calculate")[1].strip()
                elif "what is" in message_lower:
                    expr = message.split("what is")[1].strip()
                
                # Replace words with operators
                expr = (expr.replace("plus", "+").replace("minus", "-")
                        .replace("times", "").replace("multiplied by", "")
                        .replace("divided by", "/").replace("over", "/")
                        .replace("to the power of", "^").replace("raised to", "^"))
                
                # Remove question marks and other non-math chars
                expr = ''.join(c for c in expr if c in '0123456789+-*/.^() ')
                
                # Calculate
                result = eval(expr.replace('^', ''))
                return f"The result is: {result}"
            except:
                return "I couldn't understand or calculate that mathematical expression."
        
        # Web search
        elif self.web_search_var.get() and ("what is" in message_lower or "who is" in message_lower or "search for" in message_lower):
            query = message
            if "what is" in message_lower:
                query = message.split("what is")[1].strip()
            elif "who is" in message_lower:
                query = message.split("who is")[1].strip()
            elif "search for" in message_lower:
                query = message.split("search for")[1].strip()
            
            return self.perform_web_search(query)
        
        # Open websites
        elif "open " in message_lower and not self.game_active:
            site = message.split("open ")[1].strip()
            return self.open_website(site)
        
        # Play music on Spotify
        elif "play " in message_lower and ("song" in message_lower or "music" in message_lower) and not self.game_active:
            song = message.split("play ")[1].replace("song", "").replace("music", "").strip()
            return self.play_spotify_song(song)
        
        # File system access
        elif "open folder" in message_lower or "open directory" in message_lower:
            path = message.split("open")[1].replace("folder", "").replace("directory", "").strip()
            return self.open_folder(path)
        
        # Games
        elif "play game" in message_lower or "let's play" in message_lower:
            if self.game_active:
                return "We're already playing a game! Say 'quit game' to stop."
            
            game = message.split("play")[1].replace("game", "").strip()
            if not game:
                return "Which game would you like to play? I know: guess the number, tic tac toe, hangman"
            
            return self.start_game(game)
        
        elif self.game_active:
            return self.handle_game_input(message)
        
        # Default response
        else:
            return self.generate_ai_response(message)
    
    def generate_ai_response(self, message):
        # This is where you would integrate with a more advanced AI model
        # For now, we'll use simple pattern matching and responses
        
        responses = {
            "how are you": f"I'm functioning optimally, thank you for asking {self.config['user_name']}! How about you?",
            "what can you do": "I can chat with you, answer questions, perform calculations, open websites, play music on Spotify, control your system settings, and even play games!",
            "thank you": "You're very welcome! Is there anything else I can help with?",
            "your name": f"My name is {self.config['bot_name']}. You can change it if you'd like!",
            "who created you": "I was created by a talented Shashank P to assist you with various tasks and keep you company!",
            "what's up": "Just processing data and waiting for your commands! What's up with you?",
            "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
            "help": "I can help with many things! Try asking me to calculate something, open a website, play a song, or even play a game with you."
        }
        
        # Check for close matches
        matches = get_close_matches(message, responses.keys(), n=1, cutoff=0.6)
        if matches:
            return responses[matches[0]]
        
        # If no match found
        return "I'm not entirely sure how to respond to that. Could you rephrase or ask something else?"
    
    def perform_web_search(self, query):
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get featured snippet
            featured = soup.find('div', class_='BNeawe s3v9rd AP7Wnd')
            if featured:
                return featured.get_text()
            
            # Try to get first regular result
            result = soup.find('div', class_='BNeawe vvjwJb AP7Wnd')
            if result:
                return result.get_text()
            
            # If nothing found, return a generic response
            return f"I found some results for '{query}' but couldn't extract a concise answer. Would you like me to open the search in your browser?"
        
        except Exception as e:
            return f"I encountered an error while searching: {str(e)}"
    
    def open_website(self, site):
        sites = {
            'youtube': 'https://www.youtube.com',
            'google': 'https://www.google.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com',
            'reddit': 'https://www.reddit.com',
            'wikipedia': 'https://www.wikipedia.org',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://www.spotify.com',
            'github': 'https://www.github.com',
            'stackoverflow': 'https://stackoverflow.com'
        }
        
        if site in sites:
            webbrowser.open(sites[site])
            return f"Opening {site.capitalize()} in your default browser."
        else:
            try:
                # Try to open as URL
                if not site.startswith(('http://', 'https://')):
                    site = 'https://' + site
                webbrowser.open(site)
                return f"Attempting to open {site} in your browser."
            except:
                return f"I don't know how to open {site}. Try specifying a well-known website or a complete URL."
    
    def play_spotify_song(self, song):
        try:
            # This will only work if Spotify is installed and URI handling is set up
            webbrowser.open(f"spotify:search:{song}")
            return f"Searching for '{song}' in Spotify."
        except:
            return "I couldn't launch Spotify. Make sure it's installed and properly configured."
    
    def open_folder(self, path):
        try:
            if not path:
                path = os.path.expanduser("~")  # Open home directory if no path specified
            
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
            
            return f"Opening folder: {path}"
        except Exception as e:
            return f"I couldn't open that folder: {str(e)}"
    
    def set_volume(self, level):
        try:
            level = max(0, min(100, level))
            self.config['volume'] = level
            self.save_config()
            
            if sys.platform == 'win32':
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                from ctypes import cast, POINTER
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume.iid, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(level / 100, None)
            else:
                mixer.music.set_volume(level / 100)
            
            return True
        except:
            return False
    
    def start_game(self, game):
        game = game.lower()
        
        if "number" in game or "guess" in game:
            self.current_game = {
                'type': 'guess_number',
                'secret': random.randint(1, 100),
                'attempts': 0
            }
            self.game_active = True
            return "I'm thinking of a number between 1 and 100. Can you guess what it is?"
        
        elif "tic tac toe" in game or "tictactoe" in game:
            self.current_game = {
                'type': 'tic_tac_toe',
                'board': [[' ' for _ in range(3)] for _ in range(3)],
                'player': 'X',
                'bot': 'O'
            }
            self.game_active = True
            return "Let's play Tic Tac Toe! You're X and I'm O. The board is numbered 1-9 left to right, top to bottom. Say a number to make your move."
        
        elif "hangman" in game:
            words = ['python', 'javascript', 'computer', 'algorithm', 'programming', 
                    'developer', 'artificial', 'intelligence', 'machine', 'learning']
            word = random.choice(words)
            self.current_game = {
                'type': 'hangman',
                'word': word,
                'guessed': ['_'] * len(word),
                'incorrect': 0,
                'max_incorrect': 6,
                'used_letters': set()
            }
            self.game_active = True
            return f"Let's play Hangman! The word has {len(word)} letters: {' '.join(self.current_game['guessed'])}. Guess a letter!"
        
        else:
            return "I don't know that game. I can play: guess the number, tic tac toe, or hangman."
    
    def handle_game_input(self, message):
        if not self.game_active or not self.current_game:
            self.game_active = False
            return "No active game. Say 'play game' to start one."
        
        if "quit game" in message.lower() or "stop game" in message.lower():
            self.game_active = False
            self.current_game = None
            return "Game ended. Let me know if you want to play again!"
        
        game_type = self.current_game['type']
        
        if game_type == 'guess_number':
            try:
                guess = int(message)
                self.current_game['attempts'] += 1
                
                if guess < self.current_game['secret']:
                    return "Too low! Try a higher number."
                elif guess > self.current_game['secret']:
                    return "Too high! Try a lower number."
                else:
                    attempts = self.current_game['attempts']
                    self.game_active = False
                    self.current_game = None
                    return f"Congratulations! You guessed the number in {attempts} attempts."
            except:
                return "Please enter a valid number between 1 and 100."
        
        elif game_type == 'tic_tac_toe':
            try:
                pos = int(message) - 1
                if pos < 0 or pos > 8:
                    return "Please enter a number between 1 and 9."
                
                row, col = pos // 3, pos % 3
                
                if self.current_game['board'][row][col] != ' ':
                    return "That position is already taken! Try another one."
                
                # Player move
                self.current_game['board'][row][col] = self.current_game['player']
                
                # Check if player won
                if self.check_ttt_win(self.current_game['player']):
                    self.game_active = False
                    self.current_game = None
                    return "Congratulations! You won! Here's the final board:\n" + self.format_ttt_board()
                
                # Check for draw
                if all(cell != ' ' for row in self.current_game['board'] for cell in row):
                    self.game_active = False
                    self.current_game = None
                    return "It's a draw! Here's the final board:\n" + self.format_ttt_board()
                
                # Bot move
                self.bot_ttt_move()
                
                # Check if bot won
                if self.check_ttt_win(self.current_game['bot']):
                    self.game_active = False
                    self.current_game = None
                    return "I won! Better luck next time. Here's the final board:\n" + self.format_ttt_board()
                
                # Check for draw after bot move
                if all(cell != ' ' for row in self.current_game['board'] for cell in row):
                    self.game_active = False
                    self.current_game = None
                    return "It's a draw! Here's the final board:\n" + self.format_ttt_board()
                
                return "Your move:\n" + self.format_ttt_board()
            except:
                return "Please enter a number between 1 and 9 to make your move."
        
        elif game_type == 'hangman':
            if len(message) != 1 or not message.isalpha():
                return "Please guess a single letter."
            
            letter = message.lower()
            
            if letter in self.current_game['used_letters']:
                return "You've already guessed that letter. Try another one."
            
            self.current_game['used_letters'].add(letter)
            
            word = self.current_game['word']
            guessed = self.current_game['guessed']
            found = False
            
            for i, c in enumerate(word):
                if c == letter:
                    guessed[i] = letter
                    found = True
            
            if found:
                if '_' not in guessed:
                    self.game_active = False
                    self.current_game = None
                    return f"Congratulations! You guessed the word: {word}"
                return f"Correct! The word now looks like: {' '.join(guessed)}. Incorrect guesses: {self.current_game['incorrect']}/{self.current_game['max_incorrect']}"
            else:
                self.current_game['incorrect'] += 1
                remaining = self.current_game['max_incorrect'] - self.current_game['incorrect']
                
                if self.current_game['incorrect'] >= self.current_game['max_incorrect']:
                    self.game_active = False
                    self.current_game = None
                    return f"Game over! The word was: {word}"
                
                return f"Incorrect! You have {remaining} guesses left. Word: {' '.join(guessed)}"
        
        return "I didn't understand that game input. Say 'quit game' to stop playing."
    
    def check_ttt_win(self, player):
        board = self.current_game['board']
        
        # Check rows
        for row in board:
            if all(cell == player for cell in row):
                return True
        
        # Check columns
        for col in range(3):
            if all(board[row][col] == player for row in range(3)):
                return True
        
        # Check diagonals
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i] == player for i in range(3)):
            return True
        
        return False
    
    def bot_ttt_move(self):
        board = self.current_game['board']
        bot = self.current_game['bot']
        player = self.current_game['player']
        
        # Simple AI: first try to win, then block player, then take center, then corners, then random
        for i in range(3):
            for j in range(3):
                if board[i][j] == ' ':
                    # Test if this move would win
                    board[i][j] = bot
                    if self.check_ttt_win(bot):
                        return
                    board[i][j] = ' '
        
        for i in range(3):
            for j in range(3):
                if board[i][j] == ' ':
                    # Test if this move would block player
                    board[i][j] = player
                    if self.check_ttt_win(player):
                        board[i][j] = bot
                        return
                    board[i][j] = ' '
        
        # Take center if available
        if board[1][1] == ' ':
            board[1][1] = bot
            return
        
        # Take a corner
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for i, j in corners:
            if board[i][j] == ' ':
                board[i][j] = bot
                return
        
        # Take any available space
        for i in range(3):
            for j in range(3):
                if board[i][j] == ' ':
                    board[i][j] = bot
                    return
    
    def format_ttt_board(self):
        board = self.current_game['board']
        lines = []
        for row in board:
            lines.append(" | ".join(row))
            lines.append("-" * 9)
        return "\n".join(lines[:-1])  # Remove last line of dashes
    
    def change_theme(self):
        color = colorchooser.askcolor(title="Choose theme color")
        if color[1]:
            self.config['theme']['primary'] = color[1]
            self.config['theme']['secondary'] = self.adjust_color(color[1], -20)
            self.config['theme']['highlight'] = self.adjust_color(color[1], 40)
            self.save_config()
            self.apply_theme()
    
    def adjust_color(self, hex_color, amount):
        """Lighten or darken a color by a given amount"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        adjusted = []
        for channel in rgb:
            new_channel = max(0, min(255, channel + amount))
            adjusted.append(new_channel)
        
        return '#%02x%02x%02x' % tuple(adjusted)
    
    def change_names(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Names")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Your Name:").grid(row=0, column=0, padx=5, pady=5)
        user_entry = tk.Entry(dialog)
        user_entry.grid(row=0, column=1, padx=5, pady=5)
        user_entry.insert(0, self.config['user_name'])
        
        tk.Label(dialog, text="Bot Name:").grid(row=1, column=0, padx=5, pady=5)
        bot_entry = tk.Entry(dialog)
        bot_entry.grid(row=1, column=1, padx=5, pady=5)
        bot_entry.insert(0, self.config['bot_name'])
        
        def save_names():
            self.config['user_name'] = user_entry.get().strip() or DEFAULT_CONFIG['user_name']
            self.config['bot_name'] = bot_entry.get().strip() or DEFAULT_CONFIG['bot_name']
            self.save_config()
            self.root.title(f"{self.config['bot_name']} - Futuristic Chatbot")
            dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save_names).grid(row=2, column=0, columnspan=2, pady=10)
    
    def toggle_speech(self):
        self.config['speech_enabled'] = not self.config['speech_enabled']
        self.save_config()
        if self.config['speech_enabled']:
            self.add_system_message("Speech output enabled")
        else:
            self.add_system_message("Speech output disabled")
    
    def toggle_interrupt(self):
        self.config['interrupt_enabled'] = not self.config['interrupt_enabled']
        self.save_config()
        if self.config['interrupt_enabled']:
            self.add_system_message("Interruptions enabled")
        else:
            self.add_system_message("Interruptions disabled")
    
    def clear_chat(self):
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
    
    def save_chat(self):
        content = self.chat_display.get('1.0', tk.END)
        if not content.strip():
            return
        
        default_name = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = filedialog.asksaveasfilename(
            initialdir=HISTORY_DIR,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text Files", ".txt"), ("All Files", ".*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                
                # Add to recent chats
                chat_info = {
                    'file': file_path,
                    'name': os.path.basename(file_path),
                    'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                
                # Keep only last 10 chats
                self.config['recent_chats'].append(chat_info)
                if len(self.config['recent_chats']) > 10:
                    self.config['recent_chats'] = self.config['recent_chats'][-10:]
                
                self.save_config()
                self.update_history_menu()
                self.add_system_message(f"Chat saved to {file_path}")
            except Exception as e:
                self.add_error_message(f"Error saving chat: {str(e)}")
    
    def load_chat_history(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            self.clear_chat()
            self.chat_display.config(state='normal')
            self.chat_display.insert('1.0', content)
            self.chat_display.config(state='disabled')
            self.add_system_message(f"Loaded chat history from {file_path}")
        except Exception as e:
            self.add_error_message(f"Error loading chat history: {str(e)}")
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all chat history?"):
            self.config['recent_chats'] = []
            self.save_config()
            self.update_history_menu()
            self.add_system_message("Chat history cleared")
    
    def on_closing(self):
        self.save_config()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FuturisticAIChatbot(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
