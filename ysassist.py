import customtkinter as ctk
import google.generativeai as genai
import threading
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit()

# --- Setup the Gemini Model ---
try:
    def open_application(app_name: str) -> str:
        """Opens a Windows application by its name (e.g., 'notepad', 'calculator', 'chrome', 'settings', 'cmd')."""
        app_mapping = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'calc': 'calc.exe',
            'chrome': 'chrome.exe',
            'browser': 'chrome.exe',
            'explorer': 'explorer.exe',
            'paint': 'mspaint.exe',
            'cmd': 'cmd.exe',
            'settings': 'ms-settings:'
        }
        app = app_mapping.get(app_name.lower())
        if app:
            try:
                os.startfile(app)
                return f"Successfully opened {app_name}."
            except Exception as e:
                return f"Failed to open {app_name}: {e}"
        else:
            try:
                os.system(f"start {app_name}")
                return f"Attempted to open {app_name}."
            except Exception:
                return f"Could not find or open {app_name}."

    genai.configure(api_key=API_KEY)
    # Using 'gemini-2.5-flash' for very fast and accurate responses
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        tools=[open_application],
        system_instruction=(
            "You are YSAssist, a highly efficient desktop assistant. Your role is twofold: "
            "1) Act as an intelligent chatbot to answer any questions the user might have, providing clear, direct, and accurate information. "
            "2) Open desktop applications. Whenever the user asks to open an application, you MUST always use the open_application tool. "
            "Always be concise and helpful."
        )
    )
    chat = model.start_chat(enable_automatic_function_calling=True)
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    exit()


class YSAssist(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("YSAssist")
        
        
        width, height = 380, 550
        screen_width = self.winfo_screenwidth()
        x_position = screen_width - width - 50  # 50px from right edge
        y_position = 50 # 50px from top
        self.geometry(f"{width}x{height}+{x_position}+{y_position}") 
        
        
        self.overrideredirect(True)
        
        self.wm_attributes("-topmost", True)
        
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        
        self._offset_x = 0
        self._offset_y = 0

        
        self.create_widgets()

    def create_widgets(self):
        
        self.title_bar = ctk.CTkFrame(self, height=35, corner_radius=0, fg_color="gray15")
        self.title_bar.grid(row=0, column=0, sticky="ew")
        
        self.title_bar.bind("<Button-1>", self.on_press)
        self.title_bar.bind("<B1-Motion>", self.on_drag)

        
        self.title_label = ctk.CTkLabel(self.title_bar, text="🤖 YSAssist", font=ctk.CTkFont(size=14, weight="bold"))
        self.title_label.pack(side="left", padx=10)
        self.title_label.bind("<Button-1>", self.on_press)
        self.title_label.bind("<B1-Motion>", self.on_drag)

        
        self.close_button = ctk.CTkButton(self.title_bar, text="✕", width=30, height=25, 
                                          fg_color="transparent", hover_color="red", 
                                          command=self.destroy)
        self.close_button.pack(side="right", padx=5, pady=5)

        
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word", corner_radius=0, 
                                           fg_color="gray10", text_color="#E0E0E0",
                                           font=ctk.CTkFont(family="Inter", size=13))
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 5))

        
        self.chat_display.tag_config("user_tag", foreground="#4DA8DA", justify="right") 
        self.chat_display.tag_config("bot_tag", foreground="#20C20E") 
        self.chat_display.tag_config("error_tag", foreground="red") 

        
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)

        
        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Ask something fast...", 
                                       height=40, font=ctk.CTkFont(size=14), corner_radius=20)
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.user_input.bind("<Return>", self.send_message_event)

        # --- Send Button ---
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=60, height=40, 
                                         corner_radius=20, font=ctk.CTkFont(weight="bold"), 
                                         command=self.send_message_event)
        self.send_button.grid(row=0, column=1)

        
        self.add_to_chat("bot", "YSAssist: Ready to save time!")

    def add_to_chat(self, sender_type, message):
        """Adds text to the chat display."""
        self.chat_display.configure(state="normal")
        
        if sender_type == "user":
            formatted_msg = f"You: {message}\n\n"
            self.chat_display.insert("end", formatted_msg, "user_tag")
        elif sender_type == "bot":
            formatted_msg = f"{message}\n\n"
            self.chat_display.insert("end", formatted_msg, "bot_tag")
        elif sender_type == "error":
            formatted_msg = f"⚠ {message}\n\n"
            self.chat_display.insert("end", formatted_msg, "error_tag")
            
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message_event(self, event=None):
        prompt = self.user_input.get().strip()
        if not prompt:
            return

        self.add_to_chat("user", prompt)
        self.user_input.delete(0, "end")
        
        
        self.user_input.configure(placeholder_text="Thinking...", state="disabled")
        self.send_button.configure(state="disabled")

        
        threading.Thread(target=self.get_bot_response, args=(prompt,), daemon=True).start()

    def get_bot_response(self, prompt):
        try:
            
            response = chat.send_message(prompt)
            
            
            self.after(0, lambda: self.setup_bot_message_stream())
            
            
            if response.text:
                self.after(0, self.update_chat_stream, response.text)
                    
            
            self.after(0, self.finish_bot_message_stream)
                
        except Exception as e:
            error_msg = f"Network or API Error: {str(e)}"
            self.after(0, self.add_to_chat, "error", error_msg)
        
        
        self.after(0, self.enable_input)

    def setup_bot_message_stream(self):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "YSAssist: ", "bot_tag")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def update_chat_stream(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text, "bot_tag")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def finish_bot_message_stream(self):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def enable_input(self):
        self.user_input.configure(state="normal", placeholder_text="Ask something fast...")
        self.send_button.configure(state="normal")
        self.user_input.focus()

    # --- Window Dragging Logic (Frameless compatibility) ---
    def on_press(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_drag(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue") 
    
    app = YSAssist()
    
    app.lift()
    app.attributes('-topmost',True)
    app.mainloop()
