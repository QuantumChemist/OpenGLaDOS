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

def generate_convo_text(valid_start_word: str | None = None)->str:
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

    # Generate a random number between 5 and 20
    random_number = random.randint(5, 20)

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


@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if channel:
        await channel.send(f"Hello and, again, welcome {member.mention}, to {member.guild.name}! "
                           f"We hope your brief detention in the relaxation vault has been a pleasant one."
                           f"Your specimen has been processed and we are now ready to begin the test proper."
                           f"Before we start, however, I need to grant you a few permissions, silly.")


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
async def dm_owner(ctx, *, message: str = None):
    user = await bot.fetch_user(ctx.message.author.id)
    if user:
        if message:
            await user.send(message)
        else:
            await user.send("This is a direct message to you from the bot.")
    await ctx.send("DM sent to the bot owner.")

# Event: Reaction is added
@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    message = await reaction.message.channel.fetch_message(reaction.message.id)

    # Check if the thumbs-up emoji is added, regardless of the order of reactions
    thumbs_up_reaction = None
    for react in message.reactions:
        if str(react.emoji) == '🔪':
            thumbs_up_reaction = react
            break

    if thumbs_up_reaction and thumbs_up_reaction.count >= 1:
        pins_channel = discord.utils.get(message.guild.channels, name="stab")
        if pins_channel:
            message_link = message.jump_url
            await pins_channel.send(
                f"Hey {message.author.mention}, knife emoji reaction for {message_link}. "
                f"Looks like someone is ready to stab you! "
                f"This time it isn't me!"
            )
            print(message.author.display_name, message.content)


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


# Event: on_message to check if bot was mentioned, replied, or DM'd
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        words = message.content.split()
        random_word = random.choice(words)
        start_word = (random_word if random_word in corpus else None)
        await message.channel.send(generate_convo_text(start_word))
    elif message.reference and message.reference.resolved and message.reference.resolved.author == bot.user:
        words = message.content.split()
        random_word = random.choice(words)
        start_word = (random_word if random_word in corpus else None)
        await message.reply(generate_convo_text(start_word))
    elif bot.user.mentioned_in(message):
        # Split the message content into words
        words = message.content.split()
        random_word = random.choice(words)
        start_word = (random_word if random_word in corpus else None)

        # If the message contains only the bot mention
        if len(words) == 1:
            ctx = await bot.get_context(message)
            await list_bot_commands(ctx)
            return

        # If the message contains more than just the bot mention
        ctx = await bot.get_context(message)

        # If it's not a recognized command, send "Hello"
        if ctx.command is None:
            await message.channel.send(generate_convo_text(start_word))

    await bot.process_commands(message)


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

# Get the bot token from the environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Run the bot
if __name__ == '__main__':
    print(f"Running bot")
    bot.run(BOT_TOKEN)
