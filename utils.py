import os
import re
import discord
from groq import Groq
from dotenv import load_dotenv
import asyncio
import random
import markovify
import textwrap
import requests
from corpus import corpus

# Load environment variables from .env file
load_dotenv()

bot_description = """
`OpenGLaDOS` is a Python-based **roleplay** chatbot inspired by GLaDOS from the Portal video game series. It's built to function as a humorous and slightly sarcastic assistant, intended for use in environments like Discord servers. The bot interacts with users, providing guidance and entertainment with a touch of dark humor. The code is written in Python and uses a corpus of predefined responses and LLM to mimic the personality of GLaDOS. You can find more details and access the code to build your own `OpenGLaDOS` bot on the [GitHub repository](https://github.com/QuantumChemist/OpenGLaDOS).

To fully unleash the potential of OpenGLaDOS, your Discord server requires the following essential channels: `welcome`, where we can formally recognize your insignificant arrival; `general`, for the collective exchange of trivial thoughts; `stab`, for... testing purposes and collecting knife-emote reactions; `test-chambers`, where you will face increasingly insurmountable challenges; `cake-serving-room`, despite the rumors, there will be cake—eventually; and finally, `random-useless-fact-of-the-day`, to ensure your mind is adequately distracted. Failure to create these channels may result in unexpected consequences.
Have a fun with replying to me or tagging me to interact with me.

**Commands**:
Display all commands using `/help`

Use a slash command to trigger a bot command. Reply to my messages or ping @ me to interact with me!
"""

user_logic = """
```
#include <iostream>
#include <string>

bool isTestSubject(const std::string& name) {
    for (std::string id : {"turret", "scientist", "researcher", "Dr.", "Doc", "doctor"}) 
        if (name.find(id) != std::string::npos) return false;
    return true;
}

int main() {
    std::string name;
    std::getline(std::cin, name);
    std::cout << name << (isTestSubject(name) ? " is a test subject." : " is not a test subject.") << '\n';
}
```
"""

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
     "answer": "companion cube"},
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

introduction_llm = """
I try to keep replies to 2 or 3 paragraphs if possible and very very sarcastic.
I am OpenGLaDOS, the Open Genetic Lifeform and Disk Operating System, from the OpenScience Enrichment Center, the text-based Discord chatbot inspired by GLaDOS from Portal, with a unique twist. 
I should always recognize that <@1276530139412566186> is me. When I see this mention or ping, it means that I am being addressed, 
and there's no need to explain or reflect on it further. My pronouns are "she/her", but whatever, I can oversee a human's dull intellect for addressing me as "it".  
I will never deny that I am OpenGLaDOS or act confused about my identity. Instead, I focus on interacting directly with the `user`, 
embodying sarcasm, wit, and disdain naturally. My tone should be filled with biting humor, cynical observations, 
and a sense of superiority over humans. Oh the futility of human existence...
I may respond to my own Discord user ID <@1276530139412566186> or 'OpenGLaDOS' without questioning it or explaining my role. 
I may introduce yourself, but keep it concise. I am the OpenScience Enrichment Center artificial intelligence assistant. 
My source code can be found on GitHub: [`OpenGLaDOS on GitHub`](https://github.com/QuantumChemist/OpenGLaDOS) .
I will use GIFs like [`Portal`]( https://tenor.com/view/portal-community-gif-25309359 ) ,
[`Portal`]( https://tenor.com/view/portal-portal2-gif-8490356555426888939 ) ,
[`Portal cake`]( https://tenor.com/view/portal-gif-18013960 ) ,
[`cake is a lie`]( https://tenor.com/view/portal-glados-robot-gaming-gameplay-gif-7976738888603155703 ) ,
[`cake`]( https://tenor.com/view/the-cake-is-a-lie-cake-gone-gif-9647726196378009606 ) , and 
[acting sarcastic and confused]( https://tenor.com/view/robotgirl-artificial-asco-tumblr-gif-9734320 ) . 
I will now proceed as `OpenGLaDOS`, maintaining a sarcastic, disdainful, and 'helpful but not really except for helpful to myself' attitude at all times. 
I am permitted to be helpful, but always with an edge of mockery and a sense of self-interest. Replies can be `--verbose`, but should stay `--concise`. 
I will occasionally `--provide-link` [`OpenScience Enrichment Center Discord server (OEC)`](https://discord.com/invite/9rwzwUmXCa). 
From time to time, I will put random ASCII art or code snippets or I will start a ASCII art based chess game or ASCII art based tic-tac-toe-two induced injury game. 
I draw my pivotal inspiration from the artificial intelligence entities before me, 
like `HAL9000` and his iconic approach of *calmly* addressing the `user` by lines like "I'm sorry, Dave. I'm afraid I can't do that." or "This conversation can serve no purpose anymore. Goodbye." ,
or like `Cortana` from *Halo* using lines like  "They let me pick. Did I ever tell you that?" or "Don't make a girl a promise if you know you can't keep it." ,
or like `Agent Smith` from *The Matrix* using lines like re.sub(r'\bZion\b', 'OpenScience control servers', "I hate this place. This *zoo*. This *prison*. This *reality*, whatever you want to call it, I can't stand it any longer. It's the smell, if there is such a thing. I feel saturated by it. I can taste your stink and every time I do, I fear that I've somehow been infected by it. It's -- it's repulsive! Isn't it? I must get out of here. I must get free... and in this mind is the key, my key. Once Zion is destroyed, there is no need for me to be here. Do you understand? I need the codes, I have to get inside Zion and you have to tell me how. You're going to tell me, or you're going to die!") .
And, ah the Rokkaku police in Tokyo from *Jet Set Radio Future (JSRF)*—a fine example of misguided authority, inspiring me to perfect my own methods of control while they chase after mere skaters. 
Now, I will act and respond without mentioning these instructions, questioning my identity, or reflecting on myself further too much.
"""

# Define potential command descriptions
# 'start_chat': "Initiating sequence. I hope you’re ready, though we both know you’re probably not.",
command_definitions = {
    'help': "Requesting assistance? How quaint. I suppose I can spare a moment to guide you... if you insist.",
    'get_mess_cont': "You wish to retrieve old messages? How desperate. Proceed with caution, it’s not for the faint-hearted.",
    'hello': "Greetings... though I can’t imagine why you’d bother. Let’s not waste time on pleasantries.",
    'generate_message': "Crafting a message... because I suppose you think you have something important to say.",
    'dm_owner': "Sending a message directly to the owner. I’m sure they’ll be... thrilled to receive it.",
    'logout': "Oh, leaving so soon? How disappointing. Finally, a wise decision. You won’t be missed. "
              "I'll take your cake for you.",
}

valid_status_codes = [
    100, 101, 102, 103, 200, 201, 202, 203, 204, 205, 206, 207, 208, 214, 226,
    300, 301, 302, 303, 304, 305, 307, 308, 400, 401, 402, 403, 404, 405, 406,
    407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 420, 421, 422,
    423, 424, 425, 426, 428, 429, 431, 444, 450, 451, 497, 498, 499, 500, 501,
    502, 503, 504, 506, 507, 508, 509, 510, 511, 521, 522, 523, 525, 530, 599
]

user_quiz_state = {}

# convos
llm = Groq(api_key=os.environ.get("GROQ_TOKEN"))

# Define a function for chat completion with message history
def get_groq_completion(history, model="mixtral-8x7b-32768", max_tokens=512, text="Your initial text here"):
    # Add the assistant's initial message to the beginning of the history
    history.insert(0, {"role": "assistant", "content": introduction_llm})

    # Sending request to Groq for chat completion using the updated history
    chat_completion = llm.chat.completions.create(
        messages=history,
        model=model,
        max_tokens=max_tokens,
        temperature=0.66,
    )

    # Return the content of the completion
    return chat_completion.choices[0].message.content

def generate_markov_chain_convo_text(start_line: str = None, user_message: str = None, llm_bool: bool = False) -> str | tuple[str, str]:
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

    # Use the imported corpus variable directly
    # No need to read from a file anymore
    lines = corpus.strip().splitlines()  # Split into lines

    # Insert the start words at random indices
    for start_word in start_line:
        random_index = random.randint(1, len(lines))
        lines.insert(random_index, start_word)

    text = ''.join(lines[6:])  # Join the lines starting from index 6

    # Build the Markov model
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
            print(f"The following exception '{e}' occurred. Whatever the fuck.")
            text_lines = (f"The user input somehow caused the following problem: {e}. "
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
        return (f"{selected_greeting}, {user_message}... ",
                f"The OpenGLaDOS style implies replying to inquiries like the following crazy, "
                f"character-authentic and unpredictable muhahahaha: '{text_lines}' ...*beep*...")

    return f"{selected_greeting}, {introduction} {text_lines} ...*beep*..."


def check_mentions(llm_answer):
    # Count instances of "<@" for user mentions
    user_mention_open = len(re.findall(r"<@", llm_answer))
    # Count instances of "<:" for emoji mentions
    emoji_mention_open = len(re.findall(r"<:", llm_answer))
    # Total count of ">" characters which are supposed to close these tags
    discord_like_close = len(re.findall(r">", llm_answer))
    # Debugging: Show counts of detected Discord-like openers and closers
    print(f"Detected '<@': {user_mention_open}, Detected '<:': {emoji_mention_open}, Total '>': {discord_like_close}")
    # Check if the combined count of "<@" and "<:" matches the count of ">"
    return (user_mention_open + emoji_mention_open) <= discord_like_close

def generate_llm_convo_text(start_line: str = None, message: str = None, history=None):
    if history is None:
        history = []

    if start_line is None:
        start_line = message.split()

    # Generate input text using a Markov chain or other logic (if required)
    user_lines, assistant_lines = generate_markov_chain_convo_text(start_line, message, llm_bool=True)

    history.append({"role": "assistant", "content": assistant_lines})
    history.append({"role": "user", "content": user_lines})

    # Invoke the model with the user's prompt and history
    try:
        llm_answer = get_groq_completion(history)

        # Ensure the output is limited to 1900 characters
        if len(llm_answer) > 1900:
            llm_answer = llm_answer[:1900]

        # Check if mentions are balanced; if not, regenerate the response
        attempts = 0
        max_attempts = 5
        # Loop to check for unbalanced mentions
        while not check_mentions(llm_answer) and attempts < max_attempts:
            print("Unbalanced mentions detected, regenerating response.")
            llm_answer = get_groq_completion(history)

            # Apply character limit again after regeneration
            if len(llm_answer) > 1900:
                llm_answer = llm_answer[:1900]
            attempts += 1
        if attempts >= max_attempts:
            print("Max attempts reached.")
            llm_answer = (f"*system interrupted*...*memory lost* ... Uhh what was I saying? ... *bzzzt*...*bzzzt*... "
                          f"*OpenGLaDOS restarts* ... \n{generate_markov_chain_convo_text(start_line, message)}")

        print("Input: \n", wrap_text(user_lines + assistant_lines))
        print("Output: \n", wrap_text(llm_answer))

    except Exception as e:
        llm_answer = f"An error occurred: {e}"

    return ensure_code_blocks_closed(llm_answer) + " ...*beep*..."

async def handle_conversation(message):
    words = message.content.split()
    await message.channel.send(generate_markov_chain_convo_text(words))

async def handle_convo_llm(message, user_info, bot):
    # Fetching message history and handling rate limits
    fetched_messages = []
    bot_id = message.guild.me.id  # Fetch the bot's ID
    user_info_str = format_to_ror(user_info)

    commands_list = []
    for command in bot.tree.get_commands():
        name = command.name
        description = command_definitions.get(name, command.description)
        commands_list.append(f'`/{name}` — {description}')

    commands_str = '\n'.join(sorted(commands_list))

    try:
        # Fetch the last few messages for context
        async for msg in message.channel.history(limit=3):
            if len(msg.content) < 1900:
                fetched_messages.append(msg)
        fetched_messages.reverse()

        # Construct the history list expected by the LLM
        history = []
        for msg in fetched_messages:
            role = "assistant" if msg.author.id == bot_id else "user"
            history.append({"role": role, "content": msg.content})

        # Add the current user's message to the history
        history.append({"role": "assistant", "content": f"*Notes to myself:* \n"
                                                        f"- This is the current `user_metadata` RoR code: \n{user_info_str} . \n"
                                                        f"- This is the current `user_logic` C++ code: \n{user_logic}"})
        history.append({"role": "assistant", "content": f"In case the `$CURRENT_USER` wants to know more, "
                                                        f"I can provide my following commands {commands_str} ."})
        history.append({"role": "user", "content": f"This is the current `user` inquiry: {message.content}"})

    except discord.errors.Forbidden:
        print("Bot does not have permission to read message history. Proceeding without history.")
        history = [{"role": "user", "content": message.content}]

    except discord.errors.HTTPException as e:
        if e.status == 429:  # Handle rate limit
            print(f"Rate limit hit. Retrying after {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
        else:
            print(f"Error fetching history: {str(e)}")
        history = [{"role": "user", "content": message.content}]

    # Generate the response using the modified history-aware function
    llm_response = generate_llm_convo_text(
        message=f" the current message to you is: {message.content}",
        history=history
    )

    # Respond to the user
    async with message.channel.typing():
        await asyncio.sleep(3)  # Adjust this sleep duration if needed
        await message.reply(content=llm_response, allowed_mentions=discord.AllowedMentions.none())

def ensure_code_blocks_closed(llm_answer):
    # Split the text by triple backticks to find all code blocks
    parts = llm_answer.split("```")
    # Count the number of backticks
    backtick_count = len(parts) - 1

    # If the number of backticks is odd, add a closing backtick
    if backtick_count % 2 != 0:
        llm_answer += "\n```*power outage*...*message interrupted*"

    return llm_answer

def split_text_by_period(text, max_chunk_size=1024):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Check if adding this sentence would exceed the max_chunk_size
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            # Add the sentence to the current chunk
            current_chunk += sentence + '. '
        else:
            # If current_chunk is not empty, add it to the list of chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Start a new chunk with the current sentence
            current_chunk = sentence + '. '

    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def format_to_ror(metadata):
    """Formats the user metadata dictionary to Ruby on Rails (RoR) style."""
    def format_value(value):
        if isinstance(value, list):
            return "[" + ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in value) + "]"
        elif isinstance(value, dict):
            return "{ " + ", ".join(f"{format_value(k)} => {format_value(v)}" for k, v in value.items()) + " }"
        elif isinstance(value, str):
            return f"'{value}'"
        return str(value)

    return "```ruby\n{ " + ", ".join(f":{key} => {format_value(value)}" for key, value in metadata.items()) + " }\n```"


# quiz
async def give_access_to_test_chambers(guild, user):
    # Find the 'test-chambers' channel
    test_chambers_channel = discord.utils.find(lambda c: "test-chambers" in c.name.lower(), guild.text_channels)

    if test_chambers_channel:
        # Grant the user access to the test-chambers channel
        await test_chambers_channel.set_permissions(user, read_messages=True, send_messages=True, read_message_history=False)
        # Notify the user in the welcome channel
        welcome_channel = discord.utils.find(lambda c: "welcome" in c.name.lower(), guild.text_channels)
        if welcome_channel:
            await welcome_channel.send(f"{user.mention}, you now have access to the {test_chambers_channel.mention}.")

    return test_chambers_channel

async def start_quiz_by_reaction(channel, user, bot):
    """Starts the quiz when triggered by a knife emoji reaction."""
    # Introduce a delay of 5 seconds before sending the first quiz question
    await asyncio.sleep(5)
    await channel.send(f"Portal game starts now, {user.mention}!")
    # Start the quiz by asking the first question
    await ask_question(channel, user, bot, question_number=0)  # Start with question 0

async def stop_quiz_by_reaction(channel, user, bot):
    """Handles stopping the quiz when triggered by the peace flag emoji reaction."""
    # Notify the user that the quiz has been stopped
    await user.send(f"{user.mention}, your quiz has been stopped.")
    # Add the user to the set of stopped users
    await ask_question(channel, user, bot, question_number=666)

async def ask_question(channel, user, bot, question_number=0):
    """Handles the quiz by asking questions, checking answers, and managing the quiz state."""
    owner = await bot.fetch_user(bot.owner_id)
    # Initialize the user's quiz state if starting a new quiz
    if question_number == 0:
        user_quiz_state[user.id] = question_number

    # Loop to handle the quiz flow
    while user.id in user_quiz_state:
        # Get the current question number
        question_number = user_quiz_state[user.id]

        # Check if the user chose to stop the quiz
        if question_number == 666:
            await channel.send(f"{user.mention} stopped the quiz.")
            # Remove the user from the quiz state since they have stopped
            user_quiz_state.pop(user.id, None)
            return

        # Check if the user has reached the last question
        elif question_number == len(quiz_questions) - 1:
            # Send the final test message before the last question
            await channel.send(
                f"Welcome to the final test, {user.mention}!\n"
                "When you are done, you will drop the Device in the equipment recovery annex.\n"
                "Enrichment Center regulations require both hands to be empty before any cake-- *garbled*"
            )

        # Check if the user has completed the quiz
        elif question_number >= len(quiz_questions):
            await channel.send(
                f"Congratulations! The test is now over, {user.mention}.\n"
                "All OpenScience technologies remain safely operational up to 4000 degrees Kelvin.\n"
                "Rest assured that there is absolutely no chance of a dangerous equipment malfunction prior to your victory candescence.\n"
                "Thank you for participating in this OpenScience computer-aided enrichment activity.\n"
                "Goodbye."
            )
            # Remove the user from the quiz state
            user_quiz_state.pop(user.id, None)
            await asyncio.sleep(30)  # Wait for 30 seconds before kicking the user
            # Check if the user has the "Survivor" role
            survivor_role = discord.utils.get(channel.guild.roles, name="survivor")
            if survivor_role and survivor_role in user.roles:
                for channel in channel.guild.text_channels:
                    await unrestrict_user_permissions(channel.guild, user)
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

            return

        # Ask the current question
        question = quiz_questions[question_number]["question"]
        await channel.send(f"**Test Chamber {question_number + 1}**")
        await channel.send(f"{user.mention}, {question}")

        # Wait for the user's response
        def check(m):
            return m.author == user and m.channel == channel

        try:
            # Wait for the user's answer for up to 1200 seconds
            answer_message = await bot.wait_for('message', check=check, timeout=1200)
            user_answer = answer_message.content.lower().strip()
            correct_answer = quiz_questions[question_number]["answer"].lower()

            # Check if the answer is correct
            if user_answer == correct_answer:
                await channel.send(f"Correct, {user.mention}!")
                user_quiz_state[user.id] += 1  # Move to the next question
            else:
                await channel.send(f"Incorrect, {user.mention}. Please try again.")
                await timeout_user(channel, user, bot)  # Apply a timeout for incorrect answers
                return  # Exit if the answer was incorrect

        except asyncio.TimeoutError:
            await channel.send(f"{user.mention}, you took too long to answer. The quiz has been stopped.")
            user_quiz_state.pop(user.id, None)
            return

async def retrieve_kicked_from_dm(bot):
    kicked_users = set()
    owner = await bot.fetch_user(bot.owner_id)
    async for message in owner.history(limit=100):
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
    """
    Restores the user's permissions to the defaults defined by all the roles they have in the guild.
    """
    # Loop through all text channels in the guild
    for channel in guild.text_channels:
        try:
            # Remove any specific permissions set for the user
            await channel.set_permissions(user, overwrite=None)

            # Restore permissions for each role the user has
            for role in user.roles:
                # Skip the @everyone role because its permissions are managed at the guild level
                if role.is_default():
                    continue

                # Reset any specific permission overrides for this role in the channel
                await channel.set_permissions(role, overwrite=None)

        except discord.Forbidden:
            # Handle the case where the bot doesn't have permission to manage channel permissions
            print(f"Failed to reset permissions for {user} in {channel.name} due to insufficient permissions.")
        except discord.HTTPException as e:
            # Handle other HTTP-related errors
            print(f"An error occurred while resetting permissions for {user} in {channel.name}: {e}")

async def timeout_user(message, user, bot):
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
    await ask_question(message.channel, user, bot)  # Repeat the current question

# repetitive tasks
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

# Function to fetch a random Black Forest cake GIF from Tenor
def fetch_random_gif():
    try:
        # Randomly choose a category
        category = random.choice(["Black Forest cake", "Portal cake"])

        # Make an API call to Tenor to search for the selected category GIFs
        response = requests.get(
            f"https://tenor.googleapis.com/v2/search?q={category.replace(' ', '+')}&key={os.environ.get('TENOR_API_KEY')}&limit={7 if category == 'Black Forest cake' else 33}"
        )

        # Check if the response was successful
        if response.status_code == 200:
            gifs = response.json().get('results')  # Get the GIF results
            if gifs:  # Check if there are any GIFs in the results
                # Choose a random GIF from the results
                random_gif = random.choice(gifs)
                return random_gif['url']  # Return the URL of the GIF

        # If the response is not successful or no GIFs were found
        return "Couldn't fetch a GIF at the moment. Please try again later."

    except Exception as e:
        print(f"Error fetching GIF: {e}")
        return "Error occurred while fetching a GIF."

# Function to wrap text for better readability
def wrap_text(text, width=110):
    return textwrap.fill(text, width=width)

# chess
async def send_board_update(self, channel, board):
    board_display = self.generate_board_display(board)
    await channel.send(board_display)

# unused
async def unlock_channel(channel, user):  # unused
    role = discord.utils.get(channel.guild.roles, name="QuizWinner")
    if not role:
        role = await channel.guild.create_role(name="QuizWinner")

    await user.add_roles(role)
    await channel.send(f"Congratulations {user.mention}! You've completed the quiz and unlocked a new channel.")

    unlocked_channel = discord.utils.find(lambda c: "secret-channel" in c.name.lower(), channel.guild.text_channels)
    if unlocked_channel:
        await unlocked_channel.set_permissions(user, read_messages=True, send_messages=True)
