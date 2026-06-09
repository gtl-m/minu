import tkinter as tk

window = tk.Tk()
window.title("minu")
window.geometry("300x200")

def button_click():
    print("good")

button = tk.Button(window, text="minu", command=button_click)
button.pack(pady=50)

window.mainloop()