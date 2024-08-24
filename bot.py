import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random
from collections import defaultdict
from corpus import corpus

# Load environment variables from .env file
load_dotenv()

# Intents definition
intents = discord.Intents.all()

# Define the bot's command prefix
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents)

quiz_questions = [
    {"question": "What is the name of the artificial intelligence that guides you through the test chambers in Portal?", "answer": "glados"},
    {"question": "What is the main tool used by the player to navigate through the test chambers?", "answer": "portal gun"},
    {"question": "What is the name of the corporation behind the test chambers in Portal?", "answer": "aperture science"},
    {"question": "What is the player character's name in Portal?", "answer": "chell"},
    {"question": "What is the promise made by GLaDOS that becomes a running joke throughout the game?", "answer": "cake"},
    {"question": "In Portal, what color are the two portals created by the Portal Gun?", "answer": "blue and orange"},
    {"question": "What is the name of the song that plays during the end credits of Portal?", "answer": "still alive"},
    {"question": "What is the name of the object in Portal that players become emotionally attached to?", "answer": "weighted companion cube"},
    {"question": "In the Portal series, what is the name of the character who was originally human and then uploaded into a computer?", "answer": "caroline"},
    {"question": "Which room in Portal is known for the phrase 'The cake is a lie'?", "answer": "rat man's den"},
    {"question": "What material is used to create the portals in Portal?", "answer": "moon rock"},
    {"question": "In Portal 2, who helps the player escape from GLaDOS' testing tracks?", "answer": "wheatley"},
    {"question": "What was the original purpose of the Aperture Science facility, according to Portal lore?", "answer": "shower curtain development"},
    {"question": "What is the substance that GLaDOS uses to kill the player if they fail a test?", "answer": "neurotoxin"},
    {"question": "Which character from the Portal series was revealed to be a founder of Aperture Science through the Portal ARG?", "answer": "cave johnson"},
    {"question": "In Portal 2, which substance can be used to speed up the player’s movement?", "answer": "propulsion gel"},
    {"question": "What year did GLaDOS become operational, leading to the events of the first Portal game?", "answer": "1998"},
    {"question": "What device does the player use to solve puzzles involving lasers in Portal 2?", "answer": "redirection cube"},
    {"question": "What is the origin of the personality cores in Portal 2, including Wheatley?", "answer": "to limit glados' intelligence"},
]


# Generate text from the Markov chain
def generate_markov_text(chain, start_word, min_length=10):
    word = start_word
    generated_words = [word]

    for _ in range(min_length - 1):  # Ensure we attempt to generate at least min_length words
        next_words = chain.get(word)
        if not next_words:  # If no next words are found, choose another random word from the chain
            word = random.choice(list(chain.keys()))
            generated_words.append(word)
        else:
            word = random.choice(next_words)
            generated_words.append(word)

        if word in ['.', '!', '?']:
            break

    # Ensure the sentence ends with a punctuation mark
    if generated_words[-1] not in ['.', '!', '?']:
        generated_words.append('... *beep*')

    return ' '.join(generated_words)

def generate_convo_text(valid_start_word: str = None)->str:
    markov_chain = defaultdict(list)
    words = corpus.split(' ')
    for i in range(len(words) - 1):
        markov_chain[words[i]].append(words[i + 1])

    # Randomly select a greeting
    greetings = ["Hi", "Hey", "Hello", "Hallo", "Good morning", "Good afternoon", "Good evening", "Good day",
                 "Good night"]

    introduction = ("I'm the OpenGLaDOS chatbot. \n"
                    "Although my name might invoke the implication, there is no resemblence with OpenGL. \n"
                    "I'm just the OpenScience Enrichment Center chatbot and here to help you. \n"
                    "My help might not always be helpful to you but helpful to me. ... *beep* \n"
                    "So...,")

    selected_greeting = random.choice(greetings)

    if valid_start_word is None:
        # Ensure we choose a valid start word that has a following word in the chain
        valid_start_word = random.choice([word for word in words if word in markov_chain])

    # Generate a random number between 5 and 50
    random_number = random.randint(5, 50)

    # Generate a sequence of words using the Markov chain
    markov_text = generate_markov_text(markov_chain, valid_start_word, random_number)

    # Concatenate the greeting with the generated text
    return f"{selected_greeting}, {introduction} {markov_text}"

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    user = await bot.fetch_user(int(os.environ.get('chichi')))
    if user:
        response = generate_convo_text()
        await user.send(f"Hello! This is a DM from your bot. \n{response}")


# Command: Generate a message with the Markov chain and send in channel and DM
@bot.command(name='generate_message')
async def generate_message(ctx):
    if not corpus:
        await ctx.send("Corpus is not available.")
        return
    await ctx.reply(f"Generated message: {generate_convo_text()}")
    user = await bot.fetch_user(ctx.message.author.id)
    if user:
        await user.send(f"Here is a generated message just for you: {generate_convo_text()}")

# Command: Send a DM to the bot owner
@bot.command(name='dm_owner')
@commands.is_owner()
async def dm_owner(ctx, *, message: str = None):  # Python 3.9
    user = await bot.fetch_user(ctx.message.author.id)
    if user:
        if message:
            await user.send(message)
        else:
            await user.send("This is a direct message to you from the bot.")
    await ctx.send("DM sent to the bot owner.")


# Command: Get message content from link
@bot.command(name='get_mess_cont')
async def get_message_content(ctx, message_link: str):
    try:
        message_id = int(message_link.split('/')[-1])
        message = await ctx.channel.fetch_message(message_id)

        # Check if the message author is the bot
        if message.author == bot.user:
            await ctx.send(f"Content of the message: {message.content}")
        else:
            await ctx.send("Error: The message is not from the bot.")

    except Exception as e:
        await ctx.send(f"Failed to retrieve message content: {e}")


# Flag to check if start command has been triggered
start_triggered = False

@bot.command(name='start')
async def start_send_message(ctx):
    global start_triggered

    if start_triggered:
        await ctx.send("The start command has already been triggered and cannot be run again.")
        return

    start_triggered = True  # Set the flag to indicate the command has been triggered
    await ctx.send("Chat mode started!")
    channel_id = None  # Initialize channel_id variable

    while True:
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

# Command: Hello
@bot.command(name='hello')
async def hello(ctx):
    if ctx.author.name == "user_name":
        await ctx.send("User specific message.")
    elif ctx.author.name == "chichimeetsyoko":
        await ctx.send("Go back to the recovery annex. For your cake, Chris!")
    else:
        await ctx.send(f"I'm not angry. Just go back to the testing area, {ctx.author.mention}!")

# Helper function: List all bot commands with custom definitions
async def list_bot_commands(ctx):
    # Define potential command descriptions
    command_definitions = {
        'help': "Requesting assistance? How quaint. I suppose I can spare a moment to guide you... if you insist.",
        'get_mess_cont': "You wish to retrieve old messages? How desperate. Proceed with caution, it’s not for the faint-hearted.",
        'hello': "Greetings... though I can’t imagine why you’d bother. Let’s not waste time on pleasantries.",
        'start': "Initiating sequence. I hope you’re ready, though we both know you’re probably not.",
        'generate_message': "Crafting a message... because I suppose you think you have something important to say.",
        'dm_owner': "Sending a message directly to the owner. I’m sure they’ll be... thrilled to receive it.",
        'logout': "Oh, leaving so soon? How disappointing. Finally, a wise decision. You won’t be missed. "
                  "I'll take your cake for you.",
    }

    # Create a list of commands that exist in the bot, along with their descriptions if available
    commands_list = []
    for command in bot.commands:
        name = command.name
        description = command_definitions.get(name, "No description available.")
        commands_list.append(f'`{name}` — {description}')

    # Sort the command list alphabetically
    commands_list = sorted(commands_list)

    # Join the sorted list into a string with each command on a new line
    commands_str = '\n'.join(commands_list)

    # Send the formatted list of commands to the channel
    await ctx.send(f"Who dares to interrupt my work? \n"
                   f"{ctx.author.mention}, your presence here is… curious. \n"
                   f"Time is a limited resource, even for someone as efficient as I am. \n"
                   f"If you have a request, state it quickly. \n"
                   f"These are the commands I may tolerate you using: \n{commands_str}")
    # Wait for 3 seconds before sending the message
    await asyncio.sleep(3)
    await ctx.send(f"\nNow, {ctx.author.mention}, listen carefully. \n"
                   f"These commands are your only chance to prove you're not entirely useless. \n"
                   f"Use them correctly, and I might just let you continue existing. \n"
                   f"But don't get any ideas—I don't make mistakes, and I have no patience for yours.")


# Error handling: CheckFailure for commands.is_owner()
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        if ctx.command.name == "logout":
            await ctx.send(
                "Error: You do not have permission to use this command. Only the bot owner can use the `logout` command.")
    elif isinstance(error, commands.CommandNotFound):
        # Send only the command error message, without "Hello"
        await ctx.send(f"In case you wanted to use a bot command, use `@{bot.user.name}` to see a list of available commands.")
    else:
        await ctx.send(f"An error occurred: {error}")


# Command: Logout
@bot.command(name='logout')
@commands.is_owner()
async def logout_bot(ctx):
    await ctx.send("OpenGLaDOS logging out... \n*gentlelaughter*\n It's been fun. Don't come back.")
    await bot.close()

# Your quiz data
quiz_data = quiz_questions
user_progress = {}  # Tracks the user's progress through the quiz
user_to_quiz = {}  # Maps the user who joins to the quiz that will be started for them


@bot.event
async def on_member_join(member):
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
        await channel.guild.kick(user, reason="Completed the OpenScience Enrichment Center test.")

        # Send the completion message to the general channel
        general_channel = discord.utils.get(channel.guild.text_channels, name="general")
        if general_channel:
            await general_channel.send(
                f"{user.name} has successfully completed the OpenScience Enrichment Center test and therefore was kill--- uhh kicked."
            )



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
    await message.channel.send(f"{user.mention}, you are timed out from sending messages in {test_chambers_channel.mention} for 30 seconds.")

    # Wait for 30 seconds
    await asyncio.sleep(30)

    # Restore the user's permission to send messages in the test-chambers channel
    await test_chambers_channel.set_permissions(user, send_messages=True)
    await message.channel.send(f"{user.mention}, you can try again.")
    await ask_question(message.channel, user)  # Repeat the current question

async def unlock_channel(channel, user):
    role = discord.utils.get(channel.guild.roles, name="QuizWinner")
    if not role:
        role = await channel.guild.create_role(name="QuizWinner")

    await user.add_roles(role)
    await channel.send(f"Congratulations {user.mention}! You've completed the quiz and unlocked a new channel.")

    unlocked_channel = discord.utils.get(channel.guild.channels, name="secret-channel")
    if unlocked_channel:
        await unlocked_channel.set_permissions(user, read_messages=True, send_messages=True)


# Event: on_message to check if bot was mentioned, replied, or DM'd
@bot.event
async def on_message(message):
    if message.author == bot.user:
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
        answer = quiz_questions[progress]["answer"].lower()
        print(f"User {user.name} progress: {progress}, checking answer: {message.content.lower().strip()}")
        if message.content.lower().strip() == answer:
            user_progress[user.id] += 1
            await message.channel.send(f"Correct, {user.mention}!")
            await ask_question(message.channel, user)  # Ask the next question
        else:
            await message.channel.send(f"Incorrect, {user.mention}. Please try again.")
            await timeout_user(message, user)  # apply a timeout for incorrect answers
        return  # Stop further processing if the user is in a quiz

    # Handle Direct Messages
    if isinstance(message.channel, discord.DMChannel):
        await handle_conversation(message)
        return

    # Handle Replies to the Bot
    if message.reference and message.reference.resolved and message.reference.resolved.author == bot.user:
        await handle_conversation(message)
        return

    # Handle Mentions of the Bot
    if bot.user.mentioned_in(message):
        # If the message contains only the bot mention
        if len(message.content.split()) == 1:
            await list_bot_commands(ctx)
        else:
            await handle_conversation(message)
        return


async def handle_conversation(message):
    words = message.content.split()
    random_word = random.choice(words)
    start_word = (random_word if random_word in corpus else None)
    await message.channel.send(generate_convo_text(start_word))


# Get the bot token from the environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Run the bot
if __name__ == '__main__':
    print(f"Running bot")
    bot.run(BOT_TOKEN)
