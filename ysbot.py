import customtkinter as ctk
import google.generativeai as genai
import threading
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This securely loads variables from a .env file (which you should NOT share)
load_dotenv()

# --- Configure your Gemini API Key ---
# Get the API key from the environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found.")
    print("Please create a .env file and add your API key like this:")
    print("GEMINI_API_KEY=YOUR_API_KEY_GOES_HERE")
    exit()

# --- Setup the Gemini Model ---
try:
    genai.configure(api_key=API_KEY)
    # Using 'gemini-2.5-flash-preview-09-2025' which is a standard and fast model
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025') 
    chat = model.start_chat(history=[])
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    print("Please make sure your API key is correct and you have internet access.")
    exit()

# --- Main Application Class ---
class YSBot(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("YS Bot")
        
        # Place it on the side of the screen (e.g., top-right)
        # Adjust '+1500+100' based on your screen resolution
        # format is 'widthxheight+x_position+y_position'
        self.geometry("350x500+1500+100") 
        
        # This makes the window borderless (no title bar)
        self.overrideredirect(True)
        
        # This keeps the bot on top of all other windows
        self.wm_attributes("-topmost", True)
        
        # Set a color to be transparent (like the window corners)
        # self.wm_attributes("-transparentcolor", "black") 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- For borderless dragging ---
        self._offset_x = 0
        self._offset_y = 0
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)

        # --- Create UI Widgets ---
        self.create_widgets()

    def create_widgets(self):
        # --- Chat Display Box ---
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word", corner_radius=10, fg_color="gray20")
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=(10, 5))

        # Configure tags for nice colors
        self.chat_display.tag_config("tag_You", foreground="#00AFFF") # Bright Blue
        self.chat_display.tag_config("tag_YS Bot", foreground="#00FF7F") # Spring Green

        # --- User Input Entry ---
        self.user_input = ctk.CTkEntry(self, placeholder_text="Ask YS Bot anything...", corner_radius=10)
        self.user_input.grid(row=1, column=0, sticky="ew", padx=(10, 5), pady=10)
        
        # Bind the 'Enter' key to send a message
        self.user_input.bind("<Return>", self.send_message_event)

        # --- Send Button ---
        self.send_button = ctk.CTkButton(self, text="Send", width=60, corner_radius=10, command=self.send_message_event)
        self.send_button.grid(row=1, column=1, sticky="e", padx=(0, 10), pady=10)

        # --- Quit Button (needed since there's no 'X') ---
        self.quit_button = ctk.CTkButton(self, text="Quit", width=30, fg_color="darkred", hover_color="red", corner_radius=10, command=self.destroy)
        self.quit_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")

        # Add initial welcome message
        self.add_to_chat("YS Bot", "Hi! I'm YS Bot. How can I assist you?")

    def add_to_chat(self, sender, message):
        """Helper function to add text to the chat display"""
        self.chat_display.configure(state="normal")
        if sender:
            # Apply the tag to the sender's name
            self.chat_display.insert("end", f"{sender}:\n", (f"tag_{sender.replace(' ', '_')}",))
        self.chat_display.insert("end", f"{message}\n\n")
        self.chat_display.configure(state="disabled")
        
        # Auto-scroll to the bottom
        self.chat_display.see("end")

    def send_message_event(self, event=None):
        """Handles the 'send' button click or 'Enter' key press."""
        prompt = self.user_input.get().strip()
        if not prompt:
            return

        self.add_to_chat("You", prompt)
        self.user_input.delete(0, "end")
        
        # Disable input while bot is "thinking"
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")

        # Run the API call in a separate thread to avoid freezing the GUI
        threading.Thread(target=self.get_bot_response, args=(prompt,), daemon=True).start()

    def get_bot_response(self, prompt):
        """Sends prompt to Gemini and gets response."""
        try:
            response = chat.send_message(prompt, stream=True)
            
            # Stream the response for a "typing" effect
            full_response = ""
            # Add the "YS Bot:" header first on the main thread
            self.after(0, self.add_to_chat, "YS Bot", "") 
            
            for chunk in response:
                # Check for empty chunks just in case
                if hasattr(chunk, 'text'):
                    chunk_text = chunk.text
                    full_response += chunk_text
                    
                    # Update the textbox on the main thread
                    self.after(0, self.update_chat_stream, chunk_text)
                
        except Exception as e:
            # Handle API or other errors gracefully
            error_message = f"Sorry, an error occurred: {e}"
            print(error_message) # Also log to console for debugging
            self.after(0, self.add_to_chat, "Error", error_message)
        
        # Re-enable input fields on the main thread
        self.after(0, self.enable_input)

    def update_chat_stream(self, text):
        """Updates the chat display with a new chunk of text."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def enable_input(self):
        """Re-enables the input field and send button."""
        self.user_input.configure(state="normal")
        self.send_button.configure(state="normal")
        self.user_input.focus()

    # --- Dragging Functions ---
    def on_press(self, event):
        """Records the click position."""
        self._offset_x = event.x
        self._offset_y = event.y

    def on_drag(self, event):
        """Moves the window based on mouse drag."""
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")   # "light", "dark", or "system"
    ctk.set_default_color_theme("blue") # "blue", "green", "dark-blue"
    
    app = YSBot()
    app.mainloop()