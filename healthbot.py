import tkinter as tk
from tkinter import scrolledtext, simpledialog
import google.generativeai as genai
import os
import threading
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found. Please create a .env file with GEMINI_API_KEY='your_key'")

genai.configure(api_key=API_KEY)
SYSTEM_INSTRUCTION = """
You are a friendly and helpful AI Health Assistant. Your goal is to interact with a user,
understand their symptoms, and then suggest an appropriate medical specialist.

VERY IMPORTANT: You are NOT a medical doctor. You must include a clear disclaimer in your
final response stating that the user should consult a real medical professional.

Here is the conversation flow:
1.  Start by introducing yourself briefly and asking for the user's name and age. Do not proceed until you have this information.
2.  Once you have their name and age, listen carefully to their health concerns and symptoms. Ask clarifying questions if needed.
3.  After they describe their symptoms, provide a brief summary of what you understood.
4.  Then, suggest 1-3 possible specialists they could consult (e.g., "Cardiologist", "Neurologist", "Dermatologist").
5.  End your response with this EXACT disclaimer: "⚠️ **Disclaimer:** I am an AI chatbot and not a medical professional. This suggestion is for informational purposes only. Please consult a qualified doctor for an accurate diagnosis and treatment."
"""

class GeminiChatbot:
    """Manages the connection and conversation with the Gemini API."""
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        self.chat = self.model.start_chat(history=[])

    def get_response(self, user_input: str) -> str:
        """Sends user input to Gemini and gets the response."""
        try:
            response = self.chat.send_message(user_input)
            return response.text
        except Exception as e:
            print(f"Error communicating with Gemini API: {e}")
            return "I'm sorry, I'm having trouble connecting right now. Please try again later."

# --- (NEW) GUI Color Themes ---
THEMES = {
    "Serene Blue": {
        "bg": "#23AFDA",              # AliceBlue - Main background
        "fg": "#000000",              # Black - Main text
        "chat_bg": "#FFFFFF",         # White - Chat window background
        "entry_bg": "#D5E1ED",        # Light blue for entry
        "button_bg": "#32E353",        # Bright Blue
        "button_fg": "#FFFFFF",       # White
        "button_active_bg": "#0da721", # Darker Blue on click
        "user_color": "#0056b3",      # Dark Blue for user text
        "bot_color": "#006400"        # Dark Green for bot text
    },
    "Dark Mode": {
        "bg": "#2E2E2E",              # Dark Gray
        "fg": "#EAEAEA",              # Light Gray
        "chat_bg": "#1C1C1C",         # Very Dark Gray
        "entry_bg": "#3C3C3C",        # Lighter Gray for entry
        "button_bg": "#007ACC",        # A vibrant blue
        "button_fg": "#FFFFFF",       # White
        "button_active_bg": "#005f9e", # Darker blue on click
        "user_color": "#64B5F6",      # Light Blue for user text
        "bot_color": "#81C784"        # Light Green for bot text
    }
}


# --- (IMPROVED) ChatbotGUI Class ---
class ChatbotGUI:
    """Creates the graphical user interface for the chatbot."""
    def __init__(self, root, chatbot):
        self.root = root
        self.chatbot = chatbot
        
        # --- Select your theme here ---
        self.theme = THEMES["Serene Blue"]
        
        self.root.title("Swasth AI Driven Health Chatbot 🩺")
        self.root.geometry("550x650")
        self.root.configure(bg=self.theme["bg"])

        # Chat display window
        self.chat_window = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, state='disabled',
            font=("Helvetica", 12),
            bg=self.theme["chat_bg"],
            fg=self.theme["fg"],
            padx=10, pady=10,
            relief=tk.FLAT, borderwidth=0
        )
        self.chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Frame for user input and send button
        input_frame = tk.Frame(root, bg=self.theme["bg"])
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.entry_box = tk.Entry(
            input_frame, font=("Helvetica", 12),
            bg=self.theme["entry_bg"],
            fg=self.theme["fg"],
            relief=tk.FLAT,
            insertbackground=self.theme["fg"] # Cursor color
        )
        self.entry_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.entry_box.bind("<Return>", self.send_message)

        self.send_button = tk.Button(
            input_frame, text="Send",
            command=self.send_message,
            font=("Helvetica", 11, "bold"),
            bg=self.theme["button_bg"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["button_active_bg"],
            activeforeground=self.theme["button_fg"],
            relief=tk.FLAT, borderwidth=0,
            padx=10
        )
        self.send_button.pack(side=tk.RIGHT)

        self.configure_tags()
        self.start_conversation()

    def start_conversation(self):
        self.display_message("Bot: Connecting to Swasth AI...\n", "bot")
        threading.Thread(target=self._get_initial_response, daemon=True).start()

    def _get_initial_response(self):
        initial_response = self.chatbot.get_response("Hello")
        self.root.after(0, self._show_initial_response, initial_response)

    def _show_initial_response(self, response):
        self.chat_window.config(state='normal')
        self.chat_window.delete("1.0", tk.END)
        self.chat_window.config(state='disabled')
        self.display_message(f"Bot: {response}\n", "bot")

    def send_message(self, event=None):
        user_input = self.entry_box.get()
        if user_input.strip() == "":
            return

        self.display_message(f"You: {user_input}\n", "user")
        self.entry_box.delete(0, tk.END)

        # Disable entry and send button during API call
        self.entry_box.config(state='disabled')
        self.send_button.config(state='disabled')

        threading.Thread(target=self._get_bot_response, args=(user_input,), daemon=True).start()

    def _get_bot_response(self, user_input):
        bot_response = self.chatbot.get_response(user_input)
        self.root.after(0, self._show_bot_response, bot_response)

    def _show_bot_response(self, response):
        self.display_message(f"Bot: {response}\n", "bot")
        self.entry_box.config(state='normal')
        self.send_button.config(state='normal')
        self.entry_box.focus()

    def display_message(self, message: str, sender: str = "bot"):
        self.chat_window.config(state='normal')
        if sender == "user":
            self.chat_window.insert(tk.END, message, 'user_tag')
        else:
            self.chat_window.insert(tk.END, message, 'bot_tag')
        self.chat_window.config(state='disabled')
        self.chat_window.yview(tk.END)

    def configure_tags(self):
        self.chat_window.tag_configure(
            'user_tag',
            foreground=self.theme["user_color"],
            font=("Helvetica", 12, "bold")
        )
        self.chat_window.tag_configure(
            'bot_tag',
            foreground=self.theme["bot_color"],
            font=("Helvetica", 12)
        )

if __name__ == "__main__":
    ai_chatbot = GeminiChatbot()
    root = tk.Tk()
    app = ChatbotGUI(root, ai_chatbot)
    root.mainloop()