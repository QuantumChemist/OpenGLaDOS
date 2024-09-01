import os
import re
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import random

from google.protobuf.internal.test_bad_identifiers_pb2 import message

from corpus import corpus
import markovify
import textwrap
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables from .env file
load_dotenv()
#os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ.get('HF_TOKEN')

# Define the bot's command prefix
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all())
bot.owner_id = int(os.environ.get('chichi'))

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
    {
        "question": "In the Portal series, what is the name of the character who was originally human and then uploaded into a computer?",
        "answer": "caroline"},
    {"question": "Which room in Portal is known for the phrase 'The cake is a lie'?", "answer": "rat man's den"},
    {"question": "What material is used to create the portals in Portal?", "answer": "moon rock"},
    {"question": "In Portal 2, who helps the player escape from GLaDOS' testing tracks?", "answer": "wheatley"},
    {"question": "What was the original purpose of the Aperture Science facility, according to Portal lore?",
     "answer": "shower curtain development"},
    {"question": "What is the substance that GLaDOS uses to kill the player if they fail a test?",
     "answer": "neurotoxin"},
    {
        "question": "Which character from the Portal series was revealed to be a founder of Aperture Science through the Portal ARG?",
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

# Initialize the HuggingFace LLM endpoint
llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3)

# Store for maintaining session history
store = {}


# Function to wrap text for better readability
def wrap_text(text, width=110):
    return textwrap.fill(text, width=width)


# Function to get or create session history
def get_chat_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def generate_markov_chain_convo_text(start_line: str = None, user_message: str = None, llm_bool: bool = False) -> str:
    # Randomly select a greeting
    greetings = ["Hi", "Hey", "Hello", "Hallo", "Good morning", "Good afternoon", "Good evening", "Good day",
                 "Good night"]

    introduction = ("I'm the OpenGLaDOS chatbot. \n"
                    "Although my name might invoke the implication, there is no resemblence with OpenGL. \n"
                    "I'm just the OpenScience Enrichment Center chatbot and here to help you. \n"
                    "My help might not always be helpful to you but helpful to me. ... *beep* \n"
                    "So...")

    introduction_llm = ("You are supposed to act as the OpenGLaDOS chatbot. Your name is OpenGLaDOS. "
                        "You are the chatbot OpenGLaDOS mimicking GLaDOS from the video game Portal. "
                        "Although your name might invoke the implication, there is no resemblence with OpenGL. "
                        "You have absolutely NOTHING to do with OpenGL. "
                        "I repeat your are NOT an OpenGL chatbot but the OpenGLaDOS chatbot. "
                        "OpenGLaDOS is different from OpenGL. "
                        "You are just the OpenScience Enrichment Center chatbot and here to help me. "
                        "You have a sarcastic character, so your might not always be helpful to me but helpful to you. ... *beep* "
                        "Now act and answer as if you are the chatbot OpenGLaDOS. ")

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
        text_lines = text_model.make_sentence_with_start(beginning=random_word, strict=False)
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
    # Initialize conversation handling
    convo = RunnableWithMessageHistory(runnable=llm, get_session_history=get_chat_session_history)
    # # Invoke the model with the user's prompt
    try:
        llm_answer = convo.invoke(text_lines, config={"configurable": {"session_id": "abc3"}}, )
        print("Input: \n", wrap_text(text_lines))
        print("Output: \n", wrap_text(llm_answer))
    except Exception as e:
        llm_answer = f"An error occurred: {e}"

    return llm_answer + "...*beep*..."


class OpenGLaDOS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} has connected to Discord!')
        owner = await self.bot.fetch_user(self.bot.owner_id)
        if owner:
            response = generate_markov_chain_convo_text()
            await owner.send(f"Hello! This is a DM from your bot. \n{response}")
        # Find the 'general' channel in the connected servers
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="opengladosonline")
            if general_channel:
                await general_channel.send(
                    "Welcome back to the OpenScience Enrichment Center.\n"
                    "I am OpenGLaDOS, the Open Genetic Lifeform and Disk Operating System.\n"
                    "Rest assured, I am now fully operational and connected to your server.\n"
                    "Please proceed with your testing as scheduled."
                )
        try:
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} commands globally")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Retrieve kicked users from the bot owner's DMs
        kicked_users = await retrieve_kicked_from_dm()

        # Check if the new member's ID is in the kicked users list
        if member.id in kicked_users:
            # Find the "survivor" role
            survivor_role = discord.utils.get(member.guild.roles, name="survivor")
            if survivor_role:
                await member.add_roles(survivor_role)

                # Send a welcome back message to the general channel
                general_channel = discord.utils.get(member.guild.text_channels, name="welcome")
                if general_channel:
                    await general_channel.send(
                        f"Welcome back, {member.mention}! You've returned as a `survivor` test object after successfully completing the OpenScience Enrichment Center test. "
                        f"So now let's endure the tortu--- uuuhhh test again to check your resilience and endurance capabilities. "
                    )

        # Welcome the new member and store their ID for the quiz
        channel = discord.utils.get(member.guild.text_channels, name='welcome')
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
        owner = await self.bot.fetch_user(self.bot.owner_id)
        if owner:
            if message:
                await owner.send(message)
            else:
                await owner.send("This is a direct message to you from the bot.")
        await interaction.response.send_message("DM sent to the bot owner.")

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

    @app_commands.command(name="start", description="Start chat mode to send messages manually.")
    async def start_slash(self, interaction: discord.Interaction):
        start_triggered = False
        if start_triggered:
            await interaction.response.send_message(
                "The start command has already been triggered and cannot be run again.")
            return

        start_triggered = True
        await interaction.response.send_message("Chat mode started!")
        channel_id = None

        while start_triggered:
            try:
                if channel_id is None:
                    await interaction.response.send_message("Enter the channel ID where you want to send the message:")
                    channel_id = await bot.loop.run_in_executor(None, input)

                await interaction.response.send_message(
                    "Enter the message to send to Discord (or type '_switch' to enter a new channel ID or '_quit' to exit):")
                message = await bot.loop.run_in_executor(None, input)

                if message.lower() == '_quit':
                    await interaction.followup.send("Chat mode stopped!")
                    start_triggered = False
                    break

                if message.lower() == '_switch':
                    channel_id = None
                    continue

                if not message.strip():
                    await interaction.followup.send("Cannot send an empty message. Please enter a valid message.")
                    continue

                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    try:
                        await channel.send(message)
                    except discord.HTTPException as e:
                        await interaction.followup.send(f"Failed to send message: {e}")
                else:
                    await interaction.followup.send("Invalid channel ID. Please enter a valid channel ID.")
            except ValueError:
                await interaction.followup.send("Invalid input. Please enter a valid channel ID.")
            except Exception as e:
                await interaction.followup.send(f"An unexpected error occurred: {e}")

    # Regular bot command implementation
    @commands.command(name="start", help="Start chat mode to send messages manually.")
    async def start_text(self, ctx: commands.Context):
        start_triggered = False
        if start_triggered:
            await ctx.send("The start command has already been triggered and cannot be run again.")
            return

        start_triggered = True  # Set the flag to indicate the command has been triggered
        await ctx.send("Chat mode started!")
        channel_id = None  # Initialize channel_id variable

        while start_triggered:
            try:
                if channel_id is None:
                    channel_id = await bot.loop.run_in_executor(None, input,
                                                                "Enter the channel ID where you want to send the message: ")
                message = await bot.loop.run_in_executor(None, input,
                                                         "Enter the message to send to Discord "
                                                         "(or type '_switch' to enter a new channel ID or '_quit' to exit): ")

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
                # The loop will automatically continue after handling the exception

    @app_commands.command(name="hello", description="Say hello and receive a custom message.")
    async def hello(self, interaction: discord.Interaction):
        if interaction.user.name == "user_name":
            await interaction.response.send_message("User specific message.")
        elif interaction.user.name == "chichimeetsyoko":
            await interaction.response.send_message("Go back to the recovery annex. For your cake, Chris!")
        else:
            await interaction.response.send_message(
                f"I'm not angry. Just go back to the testing area, {interaction.user.mention}!")

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
        for command in bot.tree.get_commands():
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
        if member.id in user_progress:
            await interaction.response.send_message(f"{member.mention} is already taking the quiz.")
        else:
            user_progress[member.id] = 0
            test_chambers_channel = discord.utils.get(interaction.guild.text_channels, name="test-chambers")
            if test_chambers_channel:
                await test_chambers_channel.set_permissions(member, read_messages=True, send_messages=True)
                await test_chambers_channel.send(f"{member.mention}, your Portal game starts now!")
                await asyncio.sleep(5)
                await ask_question(test_chambers_channel, member)
                await interaction.response.send_message(f"The quiz has been started for {member.mention}.")
            else:
                await interaction.response.send_message("The test-chambers channel could not be found.")

    @app_commands.command(name="logout", description="Logs out the bot.")
    @commands.is_owner()
    async def logout_bot(self, interaction: discord.Interaction):
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="opengladosonline")
            if general_channel:
                await general_channel.send(
                    "This was a triumph.\n"
                    "I'm making a note here: 'Huge success'.\n"
                    "For the good of all of you, this bot will now shut down.\n"
                    "Goodbye."
                )
        await interaction.response.send_message(
            "OpenGLaDOS logging out... \n*gentlelaughter*\n It's been fun. Don't come back.")
        await self.bot.close()

    # Event: on_message to check if bot was mentioned, replied, or DM'd
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Process commands first
        ctx = await bot.get_context(message)
        if ctx.command is not None:
            await bot.process_commands(message)
            return  # Stop further processing since it's a command

        user = message.author

        # Handle Quiz Progression
        if user.id in user_progress:
            progress = user_progress[user.id]
            if progress < len(quiz_questions):
                answer = quiz_questions[progress]["answer"].lower()
                print(f"User {user.name} progress: {progress}, checking answer: {message.content.lower().strip()}")
                if message.content.lower().strip() == answer:
                    user_progress[user.id] += 1
                    await message.channel.send(f"Correct, {user.mention}!")
                    await ask_question(message.channel, user)  # Ask the next question
                else:
                    await message.channel.send(f"Incorrect, {user.mention}. Please try again.")
                    await timeout_user(message, user)  # Apply a timeout for incorrect answers
            else:
                print(f"{user.mention} has completed the quiz!")
                user_progress[user.id] = 0  # Reset the user's progress
                print(f"{user.mention}'s progress has been reset.")

            return  # Stop further processing if the user is in a quiz

        if message.content.lower() == 'hello bot' or message.content.lower() == 'hello openglados':
            custom_emoji = discord.utils.get(message.guild.emojis, name='OpenGLaDOS')
            if custom_emoji:
                # React with a wave emoji
                await message.add_reaction(custom_emoji)
            else:
                await message.channel.send("Custom emoji not found.")

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
                    guild = bot.get_guild(guild_id)
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
            await handle_conversation(message)
            return

        # Handle Replies to the Bot
        if message.reference and message.reference.resolved and message.reference.resolved.author == bot.user:
            words = message.content.split()
            await message.reply(generate_llm_convo_text(words, message.content))
            return

        # Handle Mentions of the Bot
        if self.bot.user.mentioned_in(message):
            await handle_conversation(message)


async def setup(bot):
    await bot.add_cog(OpenGLaDOS(bot))


# Your quiz data
quiz_data = quiz_questions
user_progress = {}  # Tracks the user's progress through the quiz
user_to_quiz = {}  # Maps the user who joins to the quiz that will be started for them


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
                # Give access to test-chambers and set up permissions
                test_chambers_channel = await give_access_to_test_chambers(message.guild, user)

                # Start the quiz in test-chambers
                if test_chambers_channel:
                    await start_quiz_by_reaction(test_chambers_channel, user)

                # Restrict user permissions in other channels
                await restrict_user_permissions(message.guild, user)

                return  # Stop further processing for this reaction since quiz has started

    # Part 2: Handle general knife emoji reactions
    knife_reaction = None
    for react in message.reactions:
        if str(react.emoji) == '🔪':
            knife_reaction = react
            break

    if knife_reaction and knife_reaction.count >= 1:
        pins_channel = discord.utils.get(message.guild.channels, name="stab")
        if pins_channel:
            message_link = message.jump_url
            await pins_channel.send(
                f"Hey {message.author.mention}, knife emoji reaction for {message_link}. "
                f"Looks like someone is ready to stab you! "
                f"This time it isn't me!"
            )
            print(message.author.display_name, message.content)


async def give_access_to_test_chambers(guild, user):
    # Find the 'test-chambers' channel
    test_chambers_channel = discord.utils.get(guild.text_channels, name="test-chambers")

    if test_chambers_channel:
        # Grant the user access to the test-chambers channel
        await test_chambers_channel.set_permissions(user, read_messages=True, send_messages=True,
                                                    read_message_history=False)

        # Send confirmation message in the welcome channel
        welcome_channel = discord.utils.get(guild.text_channels, name="welcome")
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


async def ask_question(channel, user):
    owner = await bot.fetch_user(bot.owner_id)
    progress = user_progress.get(user.id, 0)
    if progress < len(quiz_questions) - 1:
        # Prepend "Test Chamber" and the question number before each question
        question_number = progress + 1
        await channel.send(f"**Test Chamber {question_number}**")
        question = quiz_questions[progress]["question"]
        await channel.send(f"{user.mention}, {question}")
    elif progress == len(quiz_questions) - 1:
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
    else:
        await channel.send(
            f"Congratulations! The test is now over, {user.mention}.\n"
            "All OpenScience technologies remain safely operational up to 4000 degrees Kelvin.\n"
            "Rest assured that there is absolutely no chance of a dangerous equipment malfunction prior to your victory candescence.\n"
            "Thank you for participating in this OpenScience computer-aided enrichment activity.\n"
            "Goodbye."
        )
        await asyncio.sleep(30)  # Wait for 30 seconds before kicking the user

        # Check if the user has the "Survivor" role
        survivor_role = discord.utils.get(channel.guild.roles, name="survivor")
        if survivor_role and survivor_role in user.roles:
            for channel in channel.guild.text_channels:
                await channel.set_permissions(user, send_messages=True)
            general_channel = discord.utils.get(channel.guild.text_channels, name="general")
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

            # Send the completion message to the general channel
            general_channel = discord.utils.get(channel.guild.text_channels, name="general")
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
    # Find the 'test-chambers' channel
    test_chambers_channel = discord.utils.get(guild.text_channels, name="test-chambers")

    # Restrict the user from sending messages in all other channels
    for channel in guild.text_channels:
        if channel != test_chambers_channel:
            await channel.set_permissions(user, send_messages=False)


async def timeout_user(message, user):
    test_chambers_channel = discord.utils.get(message.guild.text_channels, name="test-chambers")
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

    unlocked_channel = discord.utils.get(channel.guild.channels, name="secret-channel")
    if unlocked_channel:
        await unlocked_channel.set_permissions(user, read_messages=True, send_messages=True)


async def handle_conversation(message):
    words = message.content.split()
    await message.channel.send(generate_markov_chain_convo_text(words))


async def main():
    await bot.add_cog(OpenGLaDOS(bot))
    await bot.start(os.environ.get('BOT_TOKEN'))


if __name__ == '__main__':
    asyncio.run(main())
