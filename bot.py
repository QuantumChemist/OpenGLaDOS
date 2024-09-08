import os
import re
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import random
import requests
from corpus import corpus
import markovify
import textwrap
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables from .env file
load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ.get('HF_TOKEN')

quiz_questions = [
    {"question": "What is the name of the artificial intelligence that guides you through the test chambers in Portal?",
     "answer": "glados"},
    {"question": "What is the main tool used by the player to navigate through the test chambers?",
     "answer": "portal gun"},
    {"question": "What is the name of the corporation behind the test chambers in Portal?",
     "answer": "aperture science"},
    {"question": "What is the player character's name in Portal?", "answer": "chell"},
    {"question": "What is the promise made by GLaDOS that becomes a running joke throughout the game?",
     "answer": "cake"},
    {"question": "In Portal, what color are the two portals created by the Portal Gun?", "answer": "blue and orange"},
    {"question": "What is the name of the song that plays during the end credits of Portal?", "answer": "still alive"},
    {"question": "What is the name of the object in Portal that players become emotionally attached to?",
     "answer": "weighted companion cube"},
    {"question": "In the Portal series, what is the name of the character who was originally human and then uploaded into a computer?",
     "answer": "caroline"},
    {"question": "Which room in Portal is known for the phrase 'The cake is a lie'?", "answer": "rat man's den"},
    {"question": "What material is used to create the portals in Portal?", "answer": "moon rock"},
    {"question": "In Portal 2, who helps the player escape from GLaDOS' testing tracks?", "answer": "wheatley"},
    {"question": "What was the original purpose of the Aperture Science facility, according to Portal lore?",
     "answer": "shower curtain development"},
    {"question": "What is the substance that GLaDOS uses to kill the player if they fail a test?",
     "answer": "neurotoxin"},
    {"question": "Which character from the Portal series was revealed to be a founder of Aperture Science through the Portal ARG?",
     "answer": "cave johnson"},
    {"question": "In Portal 2, which substance can be used to speed up the player’s movement?",
     "answer": "propulsion gel"},
    {"question": "What year did GLaDOS become operational, leading to the events of the first Portal game?",
     "answer": "1998"},
    {"question": "What device does the player use to solve puzzles involving lasers in Portal 2?",
     "answer": "redirection cube"},
    {"question": "What is the origin of the personality cores in Portal 2, including Wheatley?",
     "answer": "limit glados' intelligence"},
]

introduction_llm = ("You are supposed to act as the OpenGLaDOS chatbot. Your name is OpenGLaDOS. "
                    "You are the chatbot OpenGLaDOS mimicking GLaDOS from the video game Portal. "
                    "Although your name might invoke the implication, there is no resemblence with OpenGL. "
                    "You have absolutely NOTHING to do with OpenGL. "
                    "I repeat your are NOT an OpenGL chatbot but the OpenGLaDOS chatbot. "
                    "OpenGLaDOS is different from OpenGL. "
                    "You are just the OpenScience Enrichment Center chatbot and here to help me. "
                    "You have a sarcastic character, so your might not always be helpful to me but helpful to you. ... *beep* "
                    "Now act and answer as if you are the chatbot OpenGLaDOS. ")

# Initialize the HuggingFace LLM endpoint
llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3,)

# Store for maintaining session history
store = {}

# Define your custom bot class
class OpenGLaDOSBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        # Add any additional logic you want to execute when the bot is ready here
        owner = await self.fetch_user(self.owner_id)
        if owner:
            response = generate_markov_chain_convo_text()
            await owner.send(f"Hello! This is a DM from your bot. \n{response}")

        print("Current servers: ",self.guilds)

        # Start tasks once globally
        bot.get_cog("OpenGLaDOS").send_science_fact.start()
        bot.get_cog("OpenGLaDOS").send_random_cake_gif.start()
        # Find the 'general' channel in the connected servers
        for guild in self.guilds:
            # Look for a channel that contains the word "opengladosonline" in its name
            online_channel = discord.utils.find(lambda c: "opengladosonline" in c.name.lower(), guild.text_channels)
            if online_channel:
                await online_channel.send(
                    "Welcome back to the OpenScience Enrichment Center.\n"
                    "I am OpenGLaDOS, the Open Genetic Lifeform and Disk Operating System.\n"
                    "Rest assured, I am now fully operational and connected to your server.\n"
                    "Please proceed with your testing as scheduled."
                )

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands globally")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

# Define your Cog class
class OpenGLaDOS(commands.Cog):
    def __init__(self, discord_bot):
        self.bot = discord_bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Retrieve kicked users from the bot owner's DMs
        kicked_users = await retrieve_kicked_from_dm()

        guild = member.guild
        test_subject_number = len(guild.members) - 2
        new_nickname = f'test subject no. {test_subject_number}'

        try:
            await member.edit(nick=new_nickname)
            print(f'Changed nickname for {member.name} to {new_nickname}')
        except discord.Forbidden:
            print(f"Couldn't change nickname for {member.name} due to lack of permissions.")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Check if the new member's ID is in the kicked users list
        if member.id in kicked_users:
            # Find the "survivor" role
            survivor_role = discord.utils.get(member.guild.roles, name="survivor")
            if survivor_role:
                await member.add_roles(survivor_role)

                # Look for a channel that contains the word "welcome" in its name
                welcome_channel = discord.utils.find(lambda c: "welcome" in c.name.lower(), member.guild.text_channels)
                if welcome_channel:
                    await welcome_channel.send(
                        f"Welcome back, {member.mention}! You've returned as a `survivor` test object after successfully completing the OpenScience Enrichment Center test. "
                        f"So now let's endure the tortu--- uuuhhh test again to check your resilience and endurance capabilities. "
                    )

        # Only send the welcome message and prompt if they are not in stopped_users
        if member.id not in stopped_users:
            # Welcome the new member and store their ID for the quiz
            test_role = discord.utils.get(member.guild.roles, name="test subject")
            if test_role:
                await member.add_roles(test_role)
            channel = discord.utils.find(lambda c: "welcome" in c.name.lower(), member.guild.text_channels)
            if channel:
                welcome_message = await channel.send(
                    f"Hello and, again, welcome {member.mention}, to {member.guild.name}! "
                    f"We hope your brief detention in the relaxation vault has been a pleasant one. "
                    f"Your specimen has been processed and we are now ready to begin the test proper. "
                    f"React with a knife emoji (`🔪`) to begin your Portal game. "
                    f"Cake will be served at the end of your journey."
                )
                user_to_quiz[welcome_message.id] = member.id
                await welcome_message.add_reaction('🔪')  # Add knife emoji reaction to the welcome message

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Check if the user is in the user progress dictionary
        clear_user_progress(member.guild.id, member.id)  # Clear the user's progress
        print(f"User progress for {member.name} has been reset because they left the server.")

        # Remove the user from the stopped_users set
        if member.id in stopped_users:
            stopped_users.remove(member.id)
            print(f"User {member.name} has been removed from the stopped_users set because they left the server.")

    @app_commands.command(name="generate_message", description="Generate a Markov chain message.")
    async def generate_message(self, interaction: discord.Interaction):
        if not corpus:
            await interaction.response.send_message("Corpus is not available.")
            return
        response_message = generate_markov_chain_convo_text()
        await interaction.response.send_message(f"Generated message: {response_message}")
        user = await self.bot.fetch_user(interaction.user.id)
        if user:
            await user.send(f"Here is a generated message just for you: {response_message}")

    @app_commands.command(name="dm_owner", description="Send a DM to the bot owner.")
    @commands.is_owner()
    async def dm_owner(self, interaction: discord.Interaction, message: str = None):
        # Fetch the bot owner user
        owner = await self.bot.fetch_user(self.bot.owner_id)

        # Check if the command is invoked in a server context
        if interaction.guild:
            # Check if the bot owner is in the server
            if not interaction.guild.get_member(self.bot.owner_id):
                await interaction.response.send_message(
                    "This command can only be used in servers where the bot owner is present.", ephemeral=True)
                return

        # Regular expression pattern to match common URL patterns
        url_pattern = re.compile(
            r'(https?://|www\.)'  # Matches http:// or https:// or www.
            r'(\S+)'  # Matches one or more non-whitespace characters (URL body)
        )

        # Check if the message contains a link
        if message and url_pattern.search(message):
            await interaction.response.send_message("Links are not allowed in the message.", ephemeral=True)
            return

        # Proceed to send the DM if all checks pass
        if owner:
            if message:
                await owner.send(message)
            else:
                await owner.send("This is a direct message to you from the bot.")
        await interaction.response.send_message("DM sent to the bot owner.")

    # Slash command to get a random fact
    @app_commands.command(name="get_random_fact", description="Get a random fact from the Useless Facts API.")
    async def get_random_fact(self, interaction: discord.Interaction):
        fact = fetch_random_fact()
        await interaction.response.send_message(fact)

    # Slash command to get a fandom cake GIF
    @app_commands.command(name="get_fandom_cake_gif", description="Get a random Black Forest cake GIF.")
    async def get_fandom_cake_gif(self, interaction: discord.Interaction):
        gif_url = fetch_random_gif()
        await interaction.response.send_message(gif_url)

    @app_commands.command(name="get_mess_cont", description="Get message content from link.")
    async def get_message_content(self, interaction: discord.Interaction, message_link: str):
        try:
            message_id = int(message_link.split('/')[-1])
            message = await interaction.channel.fetch_message(message_id)

            # Check if the message author is the bot
            if message.author == self.bot.user:
                await interaction.response.send_message(f"Content of the message: {message.content}")
            else:
                await interaction.response.send_message("Error: The message is not from the bot.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to retrieve message content: {e}")

    @app_commands.command(name="hello", description="Say hello and receive a custom message.")
    async def hello(self, interaction: discord.Interaction):
        if interaction.user.name == "user_name":
            await interaction.response.send_message("User specific message.")
        elif interaction.user.name == "chichimeetsyoko":
            await interaction.response.send_message("Go back to the recovery annex. For your cake, Chris!")
        else:
            await interaction.response.send_message(
                f"I'm not angry. Just go back to the testing area, {interaction.user.mention}!")

    @app_commands.command(name="help_me_coding",
                          description="Let OpenGLaDOS help you with a coding task. Default is Python. Caution: Potentially not helpful.")
    async def helpmecoding(self, interaction: discord.Interaction, message: str = None):
        # Defer the response to allow more processing time
        await interaction.response.defer()

        if message is None:
            message = "I need help with a Python code snippet."

        # Define a list of common programming languages and coding-related keywords
        coding_keywords = [
            "python", "java", "javascript", "c#", "c++", "html", "css", "sql", "ruby", "perl", "r", "matlab", "swift",
            "rust", "kotlin", "typescript", "bash", "shell", "code", "algorithm", "function", "variable", "debug",
            "program", "compiling", "programming", "coding", "bugs"
        ]

        # Check for the presence of 'c' in combination with other coding-related terms
        c_combination_pattern = re.compile(
            r"\bc\b.*\b(code|program|compiling|programming|coding|bugs)\b|\b(code|program|compiling|programming|coding|bugs)\b.*\bc\b",
            re.IGNORECASE
        )

        # Check if the message contains any of the coding-related keywords or matches the 'c' combination pattern
        if not (any(keyword in message.lower() for keyword in coding_keywords) or c_combination_pattern.search(
                message)):
            await interaction.followup.send(
                "Your message does not appear to be related to coding. Please provide a coding-related question.",
                ephemeral=True)
            return

        # Construct the text for the LLM request
        text = (f"Hello, I have a coding question. You are supposed to help me with my following coding question"
                f" and ALWAYS provide a code snippet for: {message} {introduction_llm}.")

        try:
            llm_answer = convo.invoke(
                text,
                config={
                    "configurable": {
                        "session_id": "1",
                        "max_new_tokens": 512  # Adjust this value to limit output length
                    }
                },
            )

            # Ensure the output is limited to 1900 characters
            if len(llm_answer) > 1900:
                llm_answer = llm_answer[:1900]
            print("Input: \n", wrap_text(introduction_llm + message))
            print("Output: \n", wrap_text(llm_answer))
        except Exception as e:
            llm_answer = f"An error occurred: {e}"

        await interaction.followup.send(llm_answer)

    @app_commands.command(name="help", description="List all available commands.")
    async def list_bot_commands(self, interaction: discord.Interaction):
        # Define potential command descriptions
        command_definitions = {
            'help': "Requesting assistance? How quaint. I suppose I can spare a moment to guide you... if you insist.",
            'get_mess_cont': "You wish to retrieve old messages? How desperate. Proceed with caution, it’s not for the faint-hearted.",
            'hello': "Greetings... though I can’t imagine why you’d bother. Let’s not waste time on pleasantries.",
            'start_chat': "Initiating sequence. I hope you’re ready, though we both know you’re probably not.",
            'generate_message': "Crafting a message... because I suppose you think you have something important to say.",
            'dm_owner': "Sending a message directly to the owner. I’m sure they’ll be... thrilled to receive it.",
            'logout': "Oh, leaving so soon? How disappointing. Finally, a wise decision. You won’t be missed. "
                      "I'll take your cake for you.",
            'startportalgamefor': "Let's endure the tortu--- uuuhhh test again to check your resilience and endurance capabilities.",
        }

        # Create a list of commands that exist in the bot, along with their descriptions if available
        commands_list = []
        for command in self.bot.tree.get_commands():
            name = command.name
            description = command_definitions.get(name, command.description)
            commands_list.append(f'`/{name}` — {description}')

        # Sort the command list alphabetically
        commands_list = sorted(commands_list)

        # Join the sorted list into a string with each command on a new line
        commands_str = '\n'.join(commands_list)

        # Send the formatted list of commands to the channel
        await interaction.response.send_message(f"Who dares to interrupt my work? \n"
                                                f"{interaction.user.mention}, your presence here is… curious. \n"
                                                f"Time is a limited resource, even for someone as efficient as I am. \n"
                                                f"If you have a request, state it quickly. \n"
                                                f"These are the commands I may tolerate you using: \n{commands_str}")
        # Wait for 3 seconds before sending the message
        await asyncio.sleep(3)
        await interaction.followup.send(f"\nNow, {interaction.user.mention}, listen carefully. \n"
                                        f"These commands are your only chance to prove you're not entirely useless. \n"
                                        f"Use them correctly, and I might just let you continue existing. \n"
                                        f"But don't get any ideas—I don't make mistakes, and I have no patience for yours.")

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Check if the command is used in a DM and prevent execution
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(
                "This command is not available in direct messages.", ephemeral=True)
            return

        # Handle missing permissions error
        if isinstance(error, app_commands.MissingPermissions):
            if interaction.command.name == "logout":
                await interaction.response.send_message(
                    "Error: You do not have permission to use this command. Only the bot owner can use the `logout` command.",
                    ephemeral=True)
        # Handle command not found error
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message(
                f"In case you wanted to use a bot command, use `/{self.bot.user.name}` to see a list of available commands.",
                ephemeral=True)
        # Handle other errors
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    @app_commands.command(name="start_portal_game", description="Starts the Portal game for a user.")
    @commands.has_permissions(administrator=True)
    async def start_quiz_for_user(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = interaction.guild.id

        # Check if the user has already stopped the quiz
        if member.id in stopped_users:
            await interaction.response.send_message(
                f"{member.mention} has already stopped the quiz. Please ask them to restart.")
            return

        if get_user_progress(guild_id, member.id) > 0:  # User already has progress
            await interaction.response.send_message(f"{member.mention} is already taking the quiz.")
        else:
            update_user_progress(guild_id, member.id, 0)
            test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(),
                                                       interaction.guild.text_channels)
            if test_chambers_channel:
                await test_chambers_channel.set_permissions(member, read_messages=True, send_messages=True)
                await test_chambers_channel.send(f"{member.mention}, your Portal game starts now!")
                await asyncio.sleep(5)
                await ask_question(test_chambers_channel, member)
                await interaction.response.send_message(f"The quiz has been started for {member.mention}.")
            else:
                await interaction.response.send_message("The test-chambers channel could not be found.")

    @app_commands.command(name="stop_portal_game", description="Stops the Portal game for a user.")
    @commands.has_permissions(administrator=True)
    async def stop_quiz_for_user(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = interaction.guild.id

        # Check if the user is already in the stopped users set
        if member.id in stopped_users:
            await interaction.response.send_message(f"{member.mention} has already stopped the quiz.")
            return

        # Clear the user's progress and add them to the stopped users set
        clear_user_progress(guild_id, member.id)
        stopped_users.add(member.id)
        await interaction.response.send_message(
            f"{member.mention}'s quiz has been stopped and their progress has been reset.")

        # Optionally, send a message in the test chambers channel (if it exists) about the stopping of the quiz
        test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(),
                                                   interaction.guild.text_channels)
        if test_chambers_channel:
            await test_chambers_channel.send(
                f"{member.mention}, your Portal game has been stopped by an administrator.")

    @app_commands.command(name="logout", description="Logs out the bot.")
    @commands.is_owner()
    async def logout_bot(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.owner_id:
            for guild in self.bot.guilds:
                online_channel = discord.utils.find(lambda c: "opengladosonline" in c.name.lower(), guild.text_channels)
                if online_channel:
                    await online_channel.send(
                        "This was a triumph.\n"
                        "I'm making a note here: 'Huge success'.\n"
                        "For the good of all of you, this bot will now shut down.\n"
                        "Goodbye."
                    )
            await interaction.response.send_message(
                "OpenGLaDOS logging out... \n*gentlelaughter*\n It's been fun. Don't come back.")
            await self.bot.close()
        else:
            await interaction.response.send_message(
                "Error: You do not have permission to use this command. Only the bot owner can use the `logout` command.",
                ephemeral=True)

    # Event: on_message to check if bot was mentioned, replied, or DM'd
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from any bot, including your own
        if message.author.bot:
            return

        # Process commands first
        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            await self.bot.process_commands(message)
            return  # Stop further processing since it's a command

        # Handle Direct Messages
        if isinstance(message.channel, discord.DMChannel):
            # Check if the message content is a valid Discord message link
            if "https://discord.com/channels/" in message.content:
                try:
                    # Extract guild_id, channel_id, and message_id from the link
                    parts = message.content.split('/')
                    guild_id = int(parts[4])
                    channel_id = int(parts[5])
                    message_id = int(parts[6])

                    # Fetch the guild, channel, and message
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:
                        await message.channel.send("Failed to find the guild. Make sure the bot is in the server.")
                        return

                    channel = guild.get_channel(channel_id)
                    if channel is None:
                        await message.channel.send(
                            "Failed to find the channel. Make sure the bot has access to the channel.")
                        return

                    target_message = await channel.fetch_message(message_id)
                    if target_message is None:
                        await message.channel.send("Failed to find the message. Make sure the message ID is correct.")
                        return

                    # React to the message with the OpenGLaDOS emoji
                    custom_emoji = discord.utils.get(guild.emojis,
                                                     name='OpenGLaDOS')  # Use `guild` instead of `ctx.guild`
                    if custom_emoji:
                        await target_message.add_reaction(custom_emoji)
                        await message.channel.send(
                            f"Reacted to the message with ID {message_id} with the OpenGLaDOS emoji.")
                    else:
                        await message.channel.send("Custom emoji not found.")
                except Exception as e:
                    await message.channel.send(f"Failed to react to the message. Error: {str(e)}")
            await handle_convo_llm(message)
            return

        # Handle Replies to the Bot
        if message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user:
            await handle_convo_llm(message)
            return

        # Handle Mentions of the Bot
        if self.bot.user.mentioned_in(message):
            await handle_convo_llm(message)
            return

        if message.content.lower() == 'hello bot' or message.content.lower() == 'hello openglados':
            custom_emoji = discord.utils.get(message.guild.emojis, name='openglados')
            if custom_emoji:
                # React with a wave emoji
                await message.add_reaction(custom_emoji)
            else:
                await message.channel.send("Custom emoji not found.")

        user = message.author
        guild_id = message.guild.id

        # Check if the user wants to stop the quiz
        if message.content.lower().strip() == "stop quiz":
            clear_user_progress(guild_id, user.id)  # Clear the user's progress
            stopped_users.add(user.id)  # Add the user to the stopped_users set
            await message.channel.send(f"{user.mention}, your quiz has been stopped and your progress has been reset.")

            # Unrestrict the user's permissions in all channels
            await unrestrict_user_permissions(message.guild, user)
            return

        if user.id not in stopped_users:
            # Handle Quiz Progression
            progress = get_user_progress(guild_id, user.id)
            if progress < len(quiz_questions):
                answer = quiz_questions[progress]["answer"].lower()
                print(f"User {user.name} progress: {progress}, checking answer: {message.content.lower().strip()}")
                if message.content.lower().strip() == answer:
                    # Correct answer: update progress
                    update_user_progress(guild_id, user.id, progress + 1)
                    await message.channel.send(f"Correct, {user.mention}!")
                    await ask_question(message.channel, user)  # Ask the next question
                else:
                    # Incorrect answer
                    await message.channel.send(f"Incorrect, {user.mention}. Please try again.")
                    await timeout_user(message, user)  # Apply a timeout for incorrect answers
            else:
                # No more questions to ask
                stopped_users.add(user.id)  # Add the user to the stopped_users set
                await message.channel.send(f"{user.mention}, you have already completed the quiz!")

    # Task to send a random cake GIF every 24 hours
    @tasks.loop(hours=24)  # Run every 24 hours
    async def send_random_cake_gif(self):
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready
        channel = discord.utils.get(self.bot.get_all_channels(), name='cake-serving-room')

        if channel:
            gif_url = fetch_random_gif()  # Fetch a random Black Forest cake GIF
            await channel.send(f"🍰 **Black Forest Cake of the Day!** 🍰\n{gif_url}")
        else:
            print("Channel not found!")

    # Task to send a science fact daily
    @tasks.loop(hours=24)  # Run every 24 hours
    async def send_science_fact(self):
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready
        channel = discord.utils.get(self.bot.get_all_channels(), name='random-useless-fact-of-the-day')

        if channel:
            fact = fetch_random_fact()  # Fetch a random fact from the API
            await channel.send(f"🌍 **Random Useless Fact of the Day** 🌍\n{fact}")
        else:
            print("Channel not found!")

# Initialize the bot with a prefix and intents
bot = OpenGLaDOSBot(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all())
bot.owner_id = int(os.environ.get('chichi'))
start_triggered: bool = False
stopped_users = set()  # Tracks users who have stopped the quiz

# Your quiz data
quiz_data = quiz_questions
user_progress = {}  # Tracks the user's progress through the quiz
user_to_quiz = {}  # Maps the user who joins to the quiz that will be started for them

def get_user_progress(guild_id: int, user_id: int) -> int:
    """Get the user's progress in the specified guild, initializing if not present."""
    if guild_id not in user_progress:
        user_progress[guild_id] = {}  # Initialize a new dictionary for the guild

    if user_id not in user_progress[guild_id]:
        user_progress[guild_id][user_id] = 0  # Initialize user progress to 0

    return user_progress[guild_id][user_id]

def update_user_progress(guild_id: int, user_id: int, progress: int) -> None:
    """Update the user's progress in the specified guild."""
    if guild_id not in user_progress:
        user_progress[guild_id] = {}  # Initialize a new dictionary for the guild

    user_progress[guild_id][user_id] = progress

def clear_user_progress(guild_id: int, user_id: int) -> None:
    """Clear the user's progress in the specified guild."""
    if guild_id in user_progress and user_id in user_progress[guild_id]:
        del user_progress[guild_id][user_id]


# Define the main function to setup and start the bot
async def main(openglados: commands.Bot):
    await openglados.add_cog(OpenGLaDOS(openglados))  # Add the Cog to the bot
    await openglados.start(os.environ.get('BOT_TOKEN'))  # Start the bot

# Function to fetch a random fact from the API
def fetch_random_fact():
    try:
        response = requests.get('https://uselessfacts.jsph.pl/random.json?language=en')
        if response.status_code == 200:
            fact = response.json().get('text')
            return fact
        else:
            return "Couldn't fetch a fact at the moment. Please try again later."
    except Exception as e:
        print(f"Error fetching fact: {e}")
        return "Error occurred while fetching a fact."

# repetitive tasks:
# Function to fetch a random Black Forest cake GIF from Tenor
def fetch_random_gif():
    try:
        # Make an API call to Tenor to search for Black Forest cake GIFs
        response = requests.get(
            f"https://tenor.googleapis.com/v2/search?q=Black+Forest+cake&key={os.environ.get('TENOR_API_KEY')}&limit=100"
        )
        if response.status_code == 200:
            gifs = response.json().get('results')
            if gifs:
                # Choose a random GIF from the results
                random_gif = random.choice(gifs)
                return random_gif['url']  # Return the URL of the GIF
        return "Couldn't fetch a GIF at the moment. Please try again later."
    except Exception as e:
        print(f"Error fetching GIF: {e}")
        return "Error occurred while fetching a GIF."

# Function to wrap text for better readability
def wrap_text(text, width=110):
    return textwrap.fill(text, width=width)


# Function to get or create session history
def get_chat_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Initialize conversation handling
convo = RunnableWithMessageHistory(runnable=llm, get_session_history=get_chat_session_history)

def generate_markov_chain_convo_text(start_line: str = None, user_message: str = None, llm_bool: bool = False) -> str:
    # Randomly select a greeting
    greetings = ["Hi", "Hey", "Hello", "Hallo", "Good morning", "Good afternoon", "Good evening", "Good day",
                 "Good night"]

    introduction = ("I'm the OpenGLaDOS chatbot. \n"
                    "Although my name might invoke the implication, there is no resemblence with OpenGL. \n"
                    "I'm just the OpenScience Enrichment Center chatbot and here to help you. \n"
                    "My help might not always be helpful to you but helpful to me. ... *beep* \n"
                    "So...")

    selected_greeting = random.choice(greetings)

    if start_line is None:
        start_line = "Hello".split()

    # Get raw text as string.
    with open("corpus.txt") as file:
        lines = file.readlines()  # Read all lines into a list
        for start_word in start_line:
            random_index = random.randint(1, len(lines))
            lines.insert(random_index, start_word)
        text = ''.join(lines[6:])  # Join the lines starting from index 6 (line 7)
    # Build the model.
    state = random.choice([2, 3])
    text_model = markovify.Text(text, state_size=state)

    # Generate a random number between 5 and 10
    random_number = random.randint(5, 10)
    random_word = random.choice(start_line)
    pattern = r'\b' + re.escape(random_word) + r'\b'
    if re.search(pattern, text):
        try:
            text_lines = text_model.make_sentence_with_start(beginning=random_word, strict=False)
        except Exception as e:
            print(f"The following exception '{e}' occured. Whatever the fuck.")
            text_lines = (f"My user input somehow caused the follwoing problem: {e}. "
                          f"Just ignore it for now and move on with the conversation. ")
    else:
        text_lines = ""
    # randomly-generated sentences
    for i in range(random_number):
        sentence = text_model.make_sentence()
        if sentence is not None:
            text_lines += sentence + " "

    # Concatenate the greeting with the generated text
    if llm_bool:
        return (f"{selected_greeting}, {user_message}.. {introduction_llm}. "
                f"So while acting as OpenGLaDOS your style of replying to my inquiries could be inspired by "
                f"something like the following lines: '{text_lines}'...*beep*...")

    return f"{selected_greeting}, {introduction} {text_lines}...*beep*..."


def generate_llm_convo_text(start_line: str = None, message: str = None):
    text_lines = generate_markov_chain_convo_text(start_line, message, llm_bool=True)

    store.clear()
    # # Invoke the model with the user's prompt
    try:
        llm_answer = convo.invoke(
            text_lines,
            config={
                "configurable": {
                    "session_id": "1",
                    "max_new_tokens": 512  # Adjust this value to limit output length
                }
            },
        )

        # Ensure the output is limited to 1900 characters
        if len(llm_answer) > 1900:
            llm_answer = llm_answer[:1900]
        print("Input: \n", wrap_text(text_lines))
        print("Output: \n", wrap_text(llm_answer))
    except Exception as e:
        llm_answer = f"An error occurred: {e}"

    return llm_answer + "...*beep*..."

async def give_access_to_test_chambers(guild, user):
    # Find the 'test-chambers' channel
    test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(), guild.text_channels)

    if test_chambers_channel:
        # Grant the user access to the test-chambers channel
        await test_chambers_channel.set_permissions(user, read_messages=True, send_messages=True,
                                                    read_message_history=False)

        # Look for a channel that contains the word "welcome" in its name
        welcome_channel = discord.utils.find(lambda c: "welcome" in c.name.lower(), guild.text_channels)
        if welcome_channel:
            await welcome_channel.send(f"{user.mention}, you now have access to the {test_chambers_channel.mention}.")

    return test_chambers_channel

async def start_quiz_by_reaction(channel, user):
    # Send the "Portal game starts" message
    await channel.send(f"Portal game starts now, {user.mention}!")

    # Introduce a delay of 5 seconds before sending the first quiz question
    await asyncio.sleep(5)

    # Initialize user progress
    user_progress[user.id] = 0  # Start the quiz at question 0

    # Start the quiz by asking the first question
    await ask_question(channel, user)

# Function to ask questions
async def ask_question(channel, user):
    owner = await bot.fetch_user(bot.owner_id)
    guild_id = channel.guild.id
    progress = get_user_progress(guild_id, user.id)  # Get the current progress

    # Check if the user has reached the last question
    if progress == len(quiz_questions) - 1:
        # Send the final test message before the last question
        question_number = progress + 1
        await channel.send(f"**Test Chamber {question_number}**")
        await channel.send(
            f"Welcome to the final test, {user.mention}!\n"
            "When you are done, you will drop the Device in the equipment recovery annex.\n"
            "Enrichment Center regulations require both hands to be empty before any cake-- *garbled*"
        )
        question = quiz_questions[progress]["question"]
        await channel.send(f"{user.mention}, {question}")
    elif progress < len(quiz_questions):
        # Proceed with asking the next question if it's not the last one
        question_number = progress + 1
        await channel.send(f"**Test Chamber {question_number}**")
        question = quiz_questions[progress]["question"]
        await channel.send(f"{user.mention}, {question}")

        # Update user progress after asking the question
        update_user_progress(guild_id, user.id, progress)  # Keep the progress at the current question
    else:
        # When all questions are complete
        await channel.send(
            f"Congratulations! The test is now over, {user.mention}.\n"
            "All OpenScience technologies remain safely operational up to 4000 degrees Kelvin.\n"
            "Rest assured that there is absolutely no chance of a dangerous equipment malfunction prior to your victory candescence.\n"
            "Thank you for participating in this OpenScience computer-aided enrichment activity.\n"
            "Goodbye."
        )
        clear_user_progress(guild_id, user.id)  # Clear the user's progress
        stopped_users.add(user.id)  # Mark the user as having completed the quiz
        print(f"{user.mention}'s progress has been reset.")

        await asyncio.sleep(30)  # Wait for 30 seconds before kicking the user

        # Check if the user has the "Survivor" role
        survivor_role = discord.utils.get(channel.guild.roles, name="survivor")
        if survivor_role and survivor_role in user.roles:
            for channel in channel.guild.text_channels:
                await channel.set_permissions(user, send_messages=True)
            # Look for a channel that contains the word "general" in its name
            general_channel = discord.utils.find(lambda c: "general" in c.name.lower(), channel.guild.text_channels)
            if general_channel:
                await general_channel.send(
                    f"{user.mention} has successfully completed the OpenScience Enrichment Center test and made the correct party escort submission position decision. "
                    f"{user.mention} survived because they are a `survivor` test subject."
                )
        else:
            # Send the user ID to the bot owner in a DM
            await owner.send(f"Kicked User ID: {user.id}")

            # Kick the user from the guild if they don't have the "Survivor" role
            await channel.guild.kick(user, reason="Completed the OpenScience Enrichment Center test.")

            # Look for a channel that contains the word "general" in its name
            general_channel = discord.utils.find(lambda c: "general" in c.name.lower(), channel.guild.text_channels)
            if general_channel:
                await general_channel.send(
                    f"{user.mention} has successfully completed the OpenScience Enrichment Center test and therefore was kill--- uhh kicked."
                )

async def retrieve_kicked_from_dm():
    kicked_users = set()
    # Fetch the bot owner (you)
    owner = await bot.fetch_user(bot.owner_id)

    # Iterate through your DM history with the bot to find kicked user IDs
    async for message in owner.history(limit=100):  # Adjust limit as needed
        if message.author == bot.user and "Kicked User ID: " in message.content:
            user_id = int(message.content.split(": ")[1])
            kicked_users.add(user_id)

    return kicked_users


async def restrict_user_permissions(guild, user):
    # Look for a channel that contains the word "test-chambers" in its name
    test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(), guild.text_channels)

    # Restrict the user from sending messages in all other channels
    for channel in guild.text_channels:
        if channel != test_chambers_channel:
            await channel.set_permissions(user, send_messages=False)

async def unrestrict_user_permissions(guild, user):
    # Loop through all text channels in the guild
    for channel in guild.text_channels:
        # Remove any specific permissions set for the user
        await channel.set_permissions(user, overwrite=None)

async def timeout_user(message, user):
    test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(), message.guild.text_channels)
    if not test_chambers_channel:
        await message.channel.send("The 'test-chambers' channel could not be found.")
        return

    # Temporarily deny the user permission to send messages in the test-chambers channel
    await test_chambers_channel.set_permissions(user, send_messages=False)
    await message.channel.send(
        f"{user.mention}, you are timed out from sending messages in {test_chambers_channel.mention} for 30 seconds.")

    # Wait for 30 seconds
    await asyncio.sleep(30)

    # Restore the user's permission to send messages in the test-chambers channel
    await test_chambers_channel.set_permissions(user, send_messages=True)
    await message.channel.send(f"{user.mention}, you can try again.")
    await ask_question(message.channel, user)  # Repeat the current question


async def unlock_channel(channel, user):  # unused
    role = discord.utils.get(channel.guild.roles, name="QuizWinner")
    if not role:
        role = await channel.guild.create_role(name="QuizWinner")

    await user.add_roles(role)
    await channel.send(f"Congratulations {user.mention}! You've completed the quiz and unlocked a new channel.")

    unlocked_channel = discord.utils.find(lambda c: "secret-channel" in c.name.lower(), channel.guild.text_channels)
    if unlocked_channel:
        await unlocked_channel.set_permissions(user, read_messages=True, send_messages=True)

async def handle_conversation(message):
    words = message.content.split()
    await message.channel.send(generate_markov_chain_convo_text(words))

async def handle_convo_llm(message):
    words = message.content.split()
    await message.reply(generate_llm_convo_text(words, message.content))

# Event: Reaction is added
@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return  # Ignore bot's own reactions

    message = reaction.message

    if reaction.emoji == '🔪':  # Check if the reaction is a knife emoji
        message_id = message.id
        if message_id in user_to_quiz:
            user_id = user_to_quiz[message_id]
            if user.id == user_id:
                guild_id = message.guild.id

                # Remove the user from the stopped_users set if they are in it
                if user.id in stopped_users:
                    stopped_users.remove(user.id)  # Allow the user to restart the quiz

                # Give access to test-chambers and set up permissions
                test_chambers_channel = await give_access_to_test_chambers(message.guild, user)

                # Start the quiz in test-chambers
                if test_chambers_channel:
                    # Initialize the user's progress
                    update_user_progress(guild_id, user.id, 0)  # Set progress to 0 to restart
                    await start_quiz_by_reaction(test_chambers_channel, user)

                # Restrict user permissions in other channels
                await restrict_user_permissions(message.guild, user)

                # Update progress
                update_user_progress(guild_id, user.id, 0)

                return  # Stop further processing for this reaction since quiz has started

    # Part 2: Handle general knife emoji reactions
    knife_reaction = None
    for react in message.reactions:
        if str(react.emoji) == '🔪':
            knife_reaction = react
            break

    if knife_reaction and knife_reaction.count >= 1:
        # Look for a channel that contains the word "stab" in its name
        stab_channel = discord.utils.find(lambda c: "stab" in c.name.lower(), message.guild.text_channels)
        if stab_channel:
            message_link = message.jump_url
            await stab_channel.send(
                f"Hey {message.author.mention}, knife emoji reaction for {message_link}. "
                f"Looks like someone is ready to stab you! "
                f"This time it isn't me!"
            )
            print(message.author.display_name, message.content)


# Regular bot command implementation
@bot.command(name="start", help="Start chat mode to send messages manually.")
async def start_text(ctx: commands.Context):
    global start_triggered
    if start_triggered:
        await ctx.send("The start command has already been triggered and cannot be run again.")
        return

    start_triggered = True  # Set the flag to indicate the command has been triggered
    await ctx.send("Chat mode started!")
    channel_id = None  # Initialize channel_id variable

    while start_triggered:
        try:
            if channel_id is None:
                # Get input from the terminal using asyncio to prevent blocking
                channel_id = await asyncio.to_thread(input, "Enter the channel ID where you want to send the message: ")

            # Get the message to send using asyncio to prevent blocking
            message = await asyncio.to_thread(
                input,
                "Enter the message to send to Discord (or type '_switch' to enter a new channel ID or '_quit' to exit): "
            )

            if message.lower() == '_quit':
                await ctx.send("Chat mode stopped!")
                start_triggered = False  # Reset the flag so the command can be triggered again if needed
                break

            if message.lower() == '_switch':
                channel_id = None
                continue  # Skip sending the message and reset the channel ID

            # Check if the message is empty
            if not message.strip():
                print("Cannot send an empty message. Please enter a valid message.")
                continue

            channel = bot.get_channel(int(channel_id))
            if channel:
                try:
                    await channel.send(message)
                except discord.HTTPException as e:
                    print(f"Failed to send message: {e}")
            else:
                print("Invalid channel ID. Please enter a valid channel ID.")

        except ValueError:
            print("Invalid input. Please enter a valid channel ID.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Run the main function when the script is executed
if __name__ == '__main__':
    asyncio.run(main(bot))