import requests
import time
import os
import random
import string
import sys
import threading
import concurrent.futures
from pystyle import Colors, Colorate, Center, Write

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the main banner for the tool."""
    banner = """
██╗   ██╗███╗   ██╗██╗██╗  ██╗
██║   ██║████╗  ██║██║╚██╗██╔╝
██║   ██║██╔██╗ ██║██║ ╚███╔╝ 
██║   ██║██║╚██╗██║██║ ██╔██╗ 
╚██████╔╝██║ ╚████║██║██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
    """
    credit_line = "MADE BY XONT WITH ♡"
    colored_banner = Colorate.Vertical(Colors.purple_to_blue, Center.XCenter(banner), 1)
    colored_credit = Colorate.Vertical(Colors.purple_to_blue, Center.XCenter(credit_line), 1)
    
    print(colored_banner)
    print(colored_credit)
    print("\n")

def get_webhook_url():
    """Prompts user for a Discord webhook URL and validates it."""
    while True:
        url = Write.Input("Enter Discord Webhook URL -> ", Colors.purple, interval=0.01)
        if "discord.com/api/webhooks/" in url and url.startswith("http"):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    Write.Print("Webhook validated successfully.\n", Colors.green, interval=0.01)
                    time.sleep(1)
                    return url
                else:
                    Write.Print(f"Webhook returned status {response.status_code}. It might be invalid or deleted.\n", Colors.red, interval=0.01)
            except requests.exceptions.RequestException:
                 Write.Print("Could not connect to the URL. Please check your internet connection.\n", Colors.red, interval=0.01)
        else:
            Write.Print("Invalid Discord Webhook URL format. It must contain 'discord.com/api/webhooks/'.\n", Colors.red, interval=0.01)

def handle_response(response, success_message="Action completed successfully.", on_delete=False):
    """Handles the response from the Discord API."""
    if on_delete:
        if response.status_code == 204:
            Write.Print(f"{success_message}\n", Colors.green, interval=0.01)
        else:
            Write.Print(f"Error: {response.status_code} - {response.text}\n", Colors.red, interval=0.01)
    else:
        if response.status_code in [200, 204]:
            Write.Print(f"{success_message}\n", Colors.green, interval=0.01)
        else:
            Write.Print(f"Error: {response.status_code} - {response.text}\n", Colors.red, interval=0.01)
    time.sleep(1.5)

def send_message():
    """Sends a specified number of messages to a webhook with a live progress counter."""
    webhook_url = get_webhook_url()
    if not webhook_url: return

    message = Write.Input("Enter message to send -> ", Colors.purple, interval=0.01)
    try:
        amount = int(Write.Input("Enter number of messages to send -> ", Colors.purple, interval=0.01))
        speed = int(Write.Input("Enter speed/threads (1-100) -> ", Colors.purple, interval=0.01))
        if not 1 <= speed <= 100:
            raise ValueError
    except ValueError:
        Write.Print("Invalid input. Please enter valid numbers (speed 1-100).\n", Colors.red, interval=0.01)
        time.sleep(1)
        return

    payload = {"content": message, "username": "Unix Tool"}
    success_count = 0
    fail_count = 0
    lock = threading.Lock()

    def update_progress():
        """Updates the progress line in the console."""
        Write.Print(f"\rSent: {success_count}/{amount} | Failed: {fail_count}", Colors.cyan, interval=0)
        sys.stdout.flush()

    def worker(_):
        """The worker function for each thread. Handles sending and rate limiting."""
        nonlocal success_count, fail_count
        while True:
            try:
                response = requests.post(webhook_url, json=payload, timeout=10)
                if response.status_code in [200, 204]:
                    with lock:
                        success_count += 1
                        update_progress()
                    return
                elif response.status_code == 429: # Rate limited
                    retry_after = response.json().get('retry_after', 1)
                    time.sleep(retry_after)
                else:
                    with lock:
                        fail_count += 1
                        update_progress()
                    return
            except requests.exceptions.RequestException:
                with lock:
                    fail_count += 1
                    update_progress()
                return

    Write.Print(f"Sending {amount} messages with {speed} threads...\n", Colors.purple, interval=0.01)
    update_progress()
    with concurrent.futures.ThreadPoolExecutor(max_workers=speed) as executor:
        executor.map(worker, range(amount))

    print("\n")
    Write.Print(f"Finished. Total Successful: {success_count}, Total Failed: {fail_count}\n", Colors.green, interval=0.01)
    time.sleep(2)

def send_embed():
    """Sends a simple embed to a webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url: return

    payload = {
        "username": "Unix Tool",
        "embeds": [{
            "title": "Unix Tool",
            "description": "UNIX TOOL ON TOP",
            "color": 7506394
        }]
    }
    try:
        response = requests.post(webhook_url, json=payload)
        handle_response(response, "Embed sent successfully.")
    except requests.exceptions.RequestException as e:
        Write.Print(f"A network error occurred: {e}\n", Colors.red, interval=0.01)
        time.sleep(1.5)

def send_file():
    """Sends a random empty file to a webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url: return

    filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".txt"
    with open(filename, "w") as f:
        f.write("UNIX TOOL ONTOP BITCH.")
    
    try:
        with open(filename, "rb") as f:
            response = requests.post(webhook_url, files={"file": f}, data={"username": "Unix Tool"})
        handle_response(response, f"File '{filename}' sent successfully.")
    except requests.exceptions.RequestException as e:
        Write.Print(f"A network error occurred: {e}\n", Colors.red, interval=0.01)
    except FileNotFoundError:
        Write.Print("Could not create the temporary file.\n", Colors.red, interval=0.01)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        time.sleep(1.5)

def delete_webhook():
    """Deletes a webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url: return

    try:
        response = requests.delete(webhook_url)
        handle_response(response, "Webhook deleted successfully.", on_delete=True)
    except requests.exceptions.RequestException as e:
        Write.Print(f"A network error occurred: {e}\n", Colors.red, interval=0.01)
        time.sleep(1.5)

def send_fake_nitro():
    """Sends a fake Nitro gift embed to a webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url: return

    gift_url = "https://discord.com/gifts/scammerman"

    payload = {
        "username": "Nitro",
        "avatar_url": "https://static.wikia.nocookie.net/club-roblox/images/5/54/Discord-nitro-feat.jpg/revision/latest?cb=20210811031144",
        "embeds": [{
            "title": "You've been gifted a subscription!",
            "description": f"You've been gifted **Nitro** for **1 month**!\nExpires in **48 hours**\n\n[Click to claim]({gift_url})",
            "color": 7506394,
            "thumbnail": {"url": "https://static.wikia.nocookie.net/club-roblox/images/5/54/Discord-nitro-feat.jpg/revision/latest?cb=20210811031144"}
        }],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "Claim",
                        "style": 5,
                        "url": gift_url
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(webhook_url, json=payload)
        handle_response(response, "Fake Nitro gift sent successfully.")
    except requests.exceptions.RequestException as e:
        Write.Print(f"A network error occurred: {e}\n", Colors.red, interval=0.01)
        time.sleep(1.5)

def main():
    """Main function to run the tool."""
    while True:
        clear_screen()
        display_banner()
        menu = """
[ 1 ] Send Message
[ 2 ] Send Embed
[ 3 ] Send File
[ 4 ] Delete Webhook
[ 5 ] Send Fake Nitro Gift
[ 6 ] Exit
        """
        print(Colorate.Vertical(Colors.purple_to_blue, Center.XCenter(menu)))
        
        choice = Write.Input(">> ", Colors.purple, interval=0.02)

        if choice == '1':
            send_message()
        elif choice == '2':
            send_embed()
        elif choice == '3':
            send_file()
        elif choice == '4':
            delete_webhook()
        elif choice == '5':
            send_fake_nitro()
        elif choice == '6':
            Write.Print("Exiting the Unix Tool...\n", Colors.cyan, interval=0.01)
            time.sleep(1)
            clear_screen()
            sys.exit()
        else:
            Write.Print("Invalid choice. Please select a valid option.\n", Colors.red, interval=0.01)
            time.sleep(1)

if __name__ == "__main__":
    main()