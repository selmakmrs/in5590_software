from body import BODY
import threading
import queue
import time




body = BODY
body.start()
cmd_queue = queue.Queue()
EMOTIONS = ["happy","sad","angry", "confused"]

def input_thread():
    while True:
        cmd = input("> ").strip().lower()
        cmd_queue.put(cmd)




# start the input reader
threading.Thread(target=input_thread, daemon=True).start()

# MAIN LOOP
while True:
    
    # 2) check if we got a command
    try:
        cmd = cmd_queue.get_nowait()
    except queue.Empty:
        cmd = None

    if cmd and cmd in EMOTIONS:
        if cmd == "happy":
           body.happy()

        if cmd == "angry":
           body.angry()

        if cmd == "sad":
            body.sad()

    body.idle()
    
        

    # 3) small sleep so we don’t burn CPU
    time.sleep(0.5) 
		
    



