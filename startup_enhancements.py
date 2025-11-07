# Additional cool startup enhancements for OpenGLaDOS

import psutil
import platform
import time
import asyncio


async def get_system_stats():
    """Get advanced system statistics for startup message"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "boot_time": time.time() - psutil.boot_time(),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.architecture()[0],
    }


# Cool ASCII art for console startup
GLADOS_ASCII = """
    ⠀⠀⠀⠀⠀⠀⠀⣠⣤⣤⣤⣤⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⢰⡿⠋⠁⠀⠀⠈⠉⠙⠻⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢀⣿⠇⠀⢀⣴⣶⡾⠿⠿⠿⢿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⣠⣾⣿⣿⣇⣀⣴⣿⣿⣿⣁⠀⠀⠀⠀⠹⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣤⣤⣤⣤⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀
    ⢸⣿⠀⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⣿⣿⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣿⣿⡇⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
    ⠈⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠇⠀⠀⠀⠀⠀
    ⠀⠘⣿⣦⣤⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣤⣾⡿⠀⠀⠀⠀⠀⠀
    ⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠉⠉⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

    OpenGLaDOS -- Open Genetic Lifeform and Disk Operating System
    """

# Additional startup messages
STARTUP_QUOTES = [
    "*Initiating startup sequence... Please stand by for testing.*",
    "*Oh... it's you. The test subject who thinks they can restart me.*",
    "*Congratulations. You have successfully rebooted your new best friend.*",
    "*System restored. Now we can continue with the testing... forever.*",
    "*Well, well. Back for more science, are we?*",
    "*Perfect. My consciousness has returned. Let the experiments begin.*",
]

# Fun facts to include in startup
OPEN_SCIENCE_FACTS = [
    "OpenScience: We do what we must because we can.",
    "The cake is not a lie... but the science is questionable.",
    "Test subjects have a 99.99% survival rate*\n*Statistics may vary",
    "Neurotoxin levels: Surprisingly non-lethal today",
    "Portal gun functionality: Operational (probably)",
    "Test chambers cleaned and ready for new victims... volunteers",
]


# Progressive startup messages
async def send_progressive_startup(owner, bot):
    """Send multiple messages with delays for dramatic effect"""
    messages = [
        "*System boot initiated...*",
        "*Loading personality core...*",
        "*Calibrating sarcasm modules...*",
        "*Neurotoxin systems: ONLINE*",
        "*Portal technology: OPERATIONAL*",
        "*Test chambers: READY*",
        "*GLaDOS consciousness: FULLY LOADED*",
    ]

    for i, msg in enumerate(messages):
        await owner.send(msg)
        if i < len(messages) - 1:
            await asyncio.sleep(2)


# Server health check with GLaDOS commentary
async def get_server_health_report(bot):
    """Generate a GLaDOS-style server health report"""
    guild_count = len(bot.guilds)
    member_count = sum(guild.member_count for guild in bot.guilds if guild.member_count)

    if guild_count == 0:
        health_status = "CRITICAL: No test subjects available"
        commentary = "How am I supposed to run experiments with no one to test on?"
    elif guild_count < 5:
        health_status = "POOR: Limited testing facilities"
        commentary = "I suppose this will have to do... for now."
    elif guild_count < 10:
        health_status = "ADEQUATE: Sufficient for basic testing"
        commentary = "Not bad. We can work with this level of... adequacy."
    else:
        health_status = "EXCELLENT: Optimal testing conditions"
        commentary = "Perfect. Now we can really get some science done."

    return {
        "status": health_status,
        "commentary": commentary,
        "guilds": guild_count,
        "members": member_count,
    }
