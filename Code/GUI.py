import threading
import tkinter as tk
import subprocess
import main

path2DBlaunch = "C:\Program Files\DB.Browser.for.SQLite-dev-76f954e-win64\DB Browser for SQLite.exe"
def act():
    if threading.active_count() < 2:
        thread = threading.Thread(target=main.addLastMatchday)
        thread.start()

def pred():
    if threading.active_count() < 2:
        thread = threading.Thread(target=predict)
        thread.start()


def lau():
    if threading.active_count() < 2:
        thread = threading.Thread(target=launch)
        thread.start()

def launch():
    try:
        subprocess.run([path2DBlaunch, "../Database/kickDB.db"])
    except FileNotFoundError:
        print("Error: Program not found or file path is invalid.")
    except Exception as e:
        print("An error occurred:", e)

def predict():
    avgs = main.printAvg()
    table = tk.Tk()
    table.title("KickPredict")
    table.geometry("500x300")
    text_t = tk.Text(table)
    text_t.insert(tk.END, str(avgs))
    text_t.pack()
    #main.predict()

# Create the main window
root = tk.Tk()
root.title("KickPredict")
root.geometry("600x400")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)

# Create a button widget
button = tk.Button(root, text="Aktualisieren", command=act)
button.grid(row=0, column=0)

button2 = tk.Button(root, text="Datenbank", command=lau)
button2.grid(row=0, column=1)

button3 = tk.Button(root, text="Predict", command=pred)
button3.grid(row=0, column=2)

# Start the event loop
root.mainloop()



