# main.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from bot import OpenGLaDOSBot, OpenGLaDOS  # Import your custom bot class and cog

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with a prefix and intents
bot = OpenGLaDOSBot(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all())
bot.owner_id = int(os.environ.get('chichi'))

# Define the main function to setup and start the bot
async def main():
    await bot.add_cog(OpenGLaDOS(bot))  # Add the main Cog to the bot
    # Load additional cogs from the bot_cmds.py
    try:
        await bot.load_extension("bot_cmds")  # Register commands in bot_cmds.py as a cog
        print("Successfully loaded bot_cmds cog!")
    except Exception as e:
        print(f"Failed to load bot_cmds cog: {e}")
    await bot.start(os.environ.get('BOT_TOKEN'))  # Start the bot

# Run the main function when the script is executed
if __name__ == '__main__':
    asyncio.run(main())
