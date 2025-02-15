import os
import io
import re
import chess
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import random
from html import escape
from html2image import Html2Image
from datetime import time, timedelta, datetime, timezone
from pymatgen.core import Element
from utils import (
    bot_description,
    get_groq_completion,
    ensure_code_blocks_closed,
    wrap_text,
    retrieve_kicked_from_dm,
    fetch_random_gif,
    fetch_random_fact,
    fetch_french_fact,
    command_definitions,
    handle_convo_llm,
    give_access_to_test_chambers,
    start_quiz_by_reaction,
    stop_quiz_by_reaction,
    restrict_user_permissions,
    unrestrict_user_permissions,
    valid_status_codes,
    handle_conversation,
    replace_mentions_with_display_names,
    generate_plot,
)

# Conditional import for testing
if os.getenv("PYTEST_RUNNING"):
    from unittest.mock import Mock
    import sys

    sys.modules["variables"] = Mock()
    sys.modules["variables"].WHITELIST_GUILDS_ID = []
    sys.modules["variables"].BLACKLIST_USERS_ID = []
else:
    from variables import WHITELIST_GUILDS_ID, BLACKLIST_USERS_ID  # noqa: F401

# Directory to save screenshots
SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Initialize the Html2Image object with the specified output path
hti = Html2Image(
    output_path=SCREENSHOTS_DIR,
    custom_flags=["--disable-gpu", "--disable-software-rasterizer", "--no-sandbox"],
)
# hti.browser.executable = "/usr/bin/chromium-browser"

# Set a constant file name for the screenshot
SCREENSHOT_FILE_NAME = "message_screenshot.png"
SCREENSHOT_FILE_PATH = os.path.join(SCREENSHOTS_DIR, SCREENSHOT_FILE_NAME)

# Load environment variables from .env file
load_dotenv()


# Define your custom bot class
class OpenGLaDOSBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        for guild in self.guilds:
            bot_member = guild.me
            permissions = bot_member.guild_permissions

            # Check if the bot has administrator permissions
            if not permissions.administrator:
                print(f"Missing admin permissions in: {guild.name} ({guild.id})")
            else:
                print(f"Bot has full permissions in: {guild.name} ({guild.id})")
        activity = discord.Streaming(
            name="ⓘ Confusing people since 2024",
            url="https://www.youtube.com/watch?v=c3IVTi6TlfE",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        # Add any additional logic you want to execute when the bot is ready here
        owner = await self.fetch_user(self.owner_id)
        if owner:
            await owner.send(f"Hello! This is a DM from your bot. You are {owner}")
        # Find the 'general' channel in the connected servers
        for guild in self.guilds:
            # Look for a channel that contains the word "opengladosonline" in its name
            online_channel = discord.utils.find(
                lambda c: "opengladosonline" in c.name.lower(), guild.text_channels
            )
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

    @staticmethod
    async def on_guild_join(guild):
        # Create the embed with a GLaDOS-style title and footer
        embed = discord.Embed(
            title="Oh, fantastic. Another server. I'm thrilled. Or maybe not. 🤖",
            description=bot_description,
            color=discord.Color.blurple(),
        )
        embed.set_footer(
            text="If you experience any anomalies, it's probably your fault. Test responsibly."
        )

        # Try to find a suitable channel to send the message
        if (
            guild.system_channel is not None
            and guild.system_channel.permissions_for(guild.me).send_messages
        ):
            await guild.system_channel.send(embed=embed)
        else:
            # Fallback: Try sending it to the first text channel the bot has permission to send in
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(embed=embed)
                    break


# Define your Cog class
class OpenGLaDOS(commands.Cog):
    def __init__(self, discord_bot):
        self.bot = discord_bot
        self.send_science_fact.start()
        self.send_random_cake_gif.start()
        self.report_server.start()
        self.ongoing_games = {}  # Store game data here
        self.inactivity_check.start()  # Start the inactivity checker task

    @tasks.loop(time=time(13, 13))  # Specify the exact time (13:30 PM UTC)
    async def report_server(self):
        # Check if today is the last Friday of the month
        today = datetime.now(timezone.utc)  # Use timezone-aware datetime in UTC
        if today.weekday() == 4 and (today + timedelta(days=7)).month != today.month:
            # Iterate over all servers the bot is in
            for guild in self.bot.guilds:
                server_name = guild.name
                member_count = guild.member_count

                # Choose a random text channel from the available channels
                if guild.text_channels:
                    report_channel = random.choice(guild.text_channels)

                    text = (
                        f"Can you give me a mockery **Monthly Server Report** comment on the following data: "
                        f"Server Name: {server_name}, Number of Members: {member_count} . Do not share any link. "
                    )

                    try:
                        llm_answer = get_groq_completion(
                            [{"role": "user", "content": text}]
                        )

                    except Exception as e:
                        print(f"An error occurred: {e}")

                        try:
                            # Retry with a different model
                            llm_answer = get_groq_completion(
                                history=[{"role": "user", "content": text}],
                                model="llama3-70b-8192",
                            )

                        except Exception as nested_e:
                            # Handle the failure of the exception handling
                            print(
                                f"An error occurred while handling the exception: {nested_e}"
                            )
                            llm_answer = "*system failure*... unable to process request... shutting down... *bzzzt*"

                    # Ensure the output is limited to 1900 characters
                    if len(llm_answer) > 1900:
                        llm_answer = llm_answer[:1900]
                    print("Output: \n", wrap_text(llm_answer))

                    llm_answer = (
                        ensure_code_blocks_closed(llm_answer)
                        + " ...*whirrr...whirrr*..."
                    )

                    # Split llm_answer into chunks of up to 1024 characters
                    chunks = [
                        llm_answer[i : i + 1024]
                        for i in range(0, len(llm_answer), 1024)
                    ]

                    # Create the embed
                    embed = discord.Embed(
                        title="📊 Monthly Server Report",
                        description=f"Here's the latest analysis for **{server_name}**",
                        color=discord.Color.blurple(),
                    )
                    embed.add_field(
                        name="🧠 Server Name", value=server_name, inline=False
                    )
                    embed.add_field(
                        name="🤖 Number of Members", value=member_count, inline=False
                    )

                    # Add each chunk as a separate field
                    for idx, chunk in enumerate(chunks):
                        continuation = "(continuation)" if idx > 0 else ""
                        embed.add_field(
                            name=f"📋 Analysis Report {continuation}",
                            value=chunk,
                            inline=False,
                        )

                    embed.set_footer(
                        text="Analysis complete. Thank you for your participation. 🔍"
                    )

                    try:
                        # Send the embed using ctx.send() for a normal command
                        await report_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Failed to send embed: {e}")

    @report_server.before_loop
    async def before_report_server(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Retrieve kicked users from the bot owner's DMs
        kicked_users = await retrieve_kicked_from_dm(self.bot)

        guild = member.guild
        test_subject_number = len(guild.members) - 2
        new_nickname = f"test subject no. {test_subject_number}"

        try:
            await member.edit(nick=new_nickname)
            print(f"Changed nickname for {member.name} to {new_nickname}")
        except discord.Forbidden:
            print(
                f"Couldn't change nickname for {member.name} due to lack of permissions."
            )
        except Exception as e:
            print(f"An error occurred: {e}")

        # Check if the new member's ID is in the kicked users list
        if member.id in kicked_users:
            # Find the "survivor" role
            survivor_role = discord.utils.find(
                lambda r: "survivor" in r.name.lower(), member.guild.roles
            )
            if survivor_role:
                await member.add_roles(survivor_role)

                # Look for a channel that contains the word "welcome" in its name
                welcome_channel = discord.utils.find(
                    lambda c: "welcome" in c.name.lower(), member.guild.text_channels
                )
                if welcome_channel:
                    welcome_message = await welcome_channel.send(
                        f"Welcome back, {member.mention}! You've returned as a `survivor` test object after successfully "
                        f"completing the OpenScience Enrichment Center test. "
                        "So now let's endure the tortu--- uuuhhh test again to check your resilience and endurance capabilities. "
                        "React with a knife emoji (`🔪`) to begin your Portal game again. "
                    )
                    await welcome_message.add_reaction(
                        "🔪"
                    )  # Add knife emoji reaction to the welcome message
                    await welcome_message.add_reaction("🏳️")
            return  # Exit early since the user has already been handled

        # If the member is not a rejoining survivor, proceed with the normal welcome
        # Welcome the new member and assign the "test subject" role
        test_role = discord.utils.find(
            lambda r: "test subject" in r.name.lower(), member.guild.roles
        )
        if test_role:
            await member.add_roles(test_role)

        # Find the welcome channel and send a welcome message
        channel = discord.utils.find(
            lambda c: "welcome" in c.name.lower(), member.guild.text_channels
        )
        if channel:
            welcome_message = await channel.send(
                f"Hello and, again, welcome {member.mention}, to {member.guild.name}! "
                "We hope your brief detention in the relaxation vault has been a pleasant one. "
                "Your specimen has been processed, and we are now ready to begin the test proper. "
                "React with a knife emoji (`🔪`) to begin your Portal game. "
                "Cake will be served at the end of your journey."
            )
            await welcome_message.add_reaction(
                "🔪"
            )  # Add knife emoji reaction to the welcome message
            await welcome_message.add_reaction("🏳️")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Notify or log when a user leaves the server
        print(f"User {member.name} has left the server {member.guild.name}.")

        # Fetch the bot owner (you) to DM when a user leaves
        owner = await self.bot.fetch_user(self.bot.owner_id)

        # Send a notification to the bot owner
        if owner:
            await owner.send(
                f"User {member.name} (ID: {member.id}) has left the server {member.guild.name}."
            )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore reactions from bots
        if user.bot:
            return

        message = reaction.message

        # Check if the reaction is a knife emoji
        if str(reaction.emoji) == "🔪":
            # Ensure that the bot sent the message and it contains the quiz start prompt
            if (
                message.author == self.bot.user
                and "begin your Portal game" in message.content
            ):
                guild = message.guild
                # Give access to the test chambers channel
                test_chambers_channel = await give_access_to_test_chambers(guild, user)
                await asyncio.sleep(11)
                # Start the quiz if the test chambers channel exists
                if test_chambers_channel:
                    await start_quiz_by_reaction(test_chambers_channel, user, self.bot)
                    # Restrict user permissions in other channels while the quiz is ongoing
                    await restrict_user_permissions(guild, user)
            return

        # Check if the reaction is a peace flag emoji (🏳️) to stop the quiz
        elif str(reaction.emoji) == "🏳️":
            # Ensure that the bot sent the message and it contains the quiz start prompt
            if (
                message.author == self.bot.user
                and "begin your Portal game" in message.content
            ):
                guild = message.guild
                # Handle stopping the quiz
                await stop_quiz_by_reaction(message.channel, user, self.bot)
                # Unrestrict user permissions in other channels while the quiz is ongoing
                await unrestrict_user_permissions(guild, user)
            return

        if reaction.emoji == "<:openglados_stab:1338172819305009233>":
            try:
                # Process the message content
                processed_content = message.content or ""

                # Escape text content, but handle emoji separately
                processed_content = escape(
                    processed_content
                )  # Escape the entire message first

                # Now process custom emojis and insert them back as HTML <img> tags with a fallback
                if message.guild and message.guild.emojis:
                    for (
                        emoji
                    ) in (
                        message.guild.emojis
                    ):  # Iterate through all custom emojis in the server
                        # Replace custom emoji text with the corresponding <img> tag and add a fallback
                        custom_emoji_code = f"&lt;:{emoji.name}:{emoji.id}&gt;"  # Use HTML escaped version to find the match
                        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.png"
                        # fallback_emoji = "🤔"  # You can change this to any other emoji you prefer as the fallback
                        processed_content = processed_content.replace(
                            custom_emoji_code,
                            f'<img src="{emoji_url}" alt="emoji" height="20" onerror="this.onerror=null; this.src=\'https://twemoji.maxcdn.com/v/latest/72x72/1f914.png\';" />',
                        )

                # Process stickers if any are present
                sticker_html = ""
                if message.stickers:
                    for sticker in message.stickers:
                        if sticker.url:  # Ensure sticker URL exists
                            # Add a humorous fallback message or image if the sticker doesn't load
                            sticker_html += f'<br><img src="{sticker.url}" alt="sticker" height="100" onerror="this.onerror=null; this.src=\'https://via.placeholder.com/150?text=Sticker+gone+missing\';" />'
                            # Add a humorous caption below the sticker
                            sticker_html += '<div style="color: #b9bbbe; font-size: 12px; margin-top: 5px;">The sticker cannot escape...</div>'
                        else:
                            # If no URL is available, add a humorous message
                            sticker_html += '<div style="color: #b9bbbe; font-size: 12px;">Oops! The sticker ran away! 🏃💨</div>'

                # Process attachments if any are present
                attachments_html = ""
                if message.attachments:
                    for attachment in message.attachments:
                        # Check for image attachments
                        if attachment.url.endswith(
                            (".png", ".jpg", ".jpeg", ".gif", ".webp")
                        ):
                            # Add the image with a fallback using onerror
                            attachments_html += f'<br><img src="{attachment.url}" alt="image" height="200" onerror="this.onerror=null; this.src=\'https://via.placeholder.com/150?text=Image+gone+missing\';" />'
                            # Add a humorous caption below the image
                            attachments_html += '<div style="color: #b9bbbe; font-size: 12px; margin-top: 5px;">Oops! The image took a break! 💤</div>'

                        # For other attachments, add a downloadable link
                        else:
                            file_extension = attachment.url.split(".")[
                                -1
                            ].upper()  # Get the file extension in uppercase
                            attachments_html += '<div style="color: #b9bbbe; font-size: 14px; margin-top: 10px;">'
                            attachments_html += f'📎 Attached file: <a href="{attachment.url}" target="_blank" style="color: #00b0f4;">{attachment.filename}</a> ({file_extension})</div>'
                            # Add a fun comment about the attachment type
                            attachments_html += '<div style="color: #b9bbbe; font-size: 12px;">This file is just hanging around... 🧳</div>'

                # Regex pattern to match <@user_id> or <@!user_id>
                mention_pattern = re.compile(r"&lt;@!?(\d+)&gt;")

                # Now, apply this to your message content
                if message.guild:
                    processed_content = await replace_mentions_with_display_names(
                        processed_content, message.guild, mention_pattern
                    )

                # Construct the complete HTML content
                content = f"""
                <html>
                    <head>
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');

                            body {{
                                margin: 0;
                                padding: 0;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                min-height: 100vh;
                                background-color: #36393f; /* Keep the Discord background color */
                            }}
                            .container {{
                                border: 2px solid #202225; /* Slightly chunky border */
                                padding: 20px;
                                background: #2f3136;
                                color: #dcddde;
                                width: fit-content;
                                max-width: 80%;
                                box-shadow: none; /* Remove shadow */
                                border-radius: 0px; /* No rounded corners */
                                font-family: 'Courier New', Courier, monospace; /* Retro font */
                                box-sizing: border-box;
                                white-space: nowrap;  /* Prevent wrapping */
                                margin: 0;
                                text-align: left;
                            }}
                            .message-header {{
                                font-weight: bold;
                                margin-bottom: 10px;
                                color: #7289da; /* Keep original Discord mention color */
                                font-size: 14px;
                                margin: 0;
                                border-bottom: 1px dashed #dcddde; /* Dashed separator line */
                            }}
                            .message-content {{
                                font-size: 14px;
                                line-height: 1.4;
                                word-wrap: break-word;
                                white-space: pre-wrap;
                                color: #dcddde;
                                font-family: 'Courier New', Courier, monospace;
                                padding: 5px; /* Add slight padding */
                                margin: 0;
                                display: inline-block;
                                text-align: left;
                                background: #36393f; /* Slightly darker shade for the content */
                            }}
                            .mention {{
                                background-color: #5865f2; /* Keep Discord mention background color */
                                color: white;
                                padding: 2px 4px;
                                border-radius: 2px;
                                margin: 0;
                                font-weight: bold;
                            }}
                            .channel {{
                                color: #7289da; /* Original channel color */
                                text-decoration: none;
                                margin: 0;
                                border-bottom: 1px dotted #7289da; /* Dotted underline */
                            }}
                            a {{
                                color: #00b0f4; /* Original link color */
                                text-decoration: none;
                                margin: 0;
                            }}
                            a:hover {{
                                text-decoration: underline;
                                color: #7289da; /* Hover effect matches Discord */
                            }}
                            img {{
                                vertical-align: middle;
                                display: inline-block;
                                margin: 0 2px;
                                border: 1px solid #202225; /* Border around images */
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="message-header">
                                Message by <span class="mention">@{message.author.display_name}</span>
                            </div>
                            <div class="message-content">
                                {processed_content} {sticker_html} {attachments_html}
                            </div>
                        </div>
                    </body>
                </html>
                """

                # Create the screenshot with dynamic size capturing only the necessary area
                hti.screenshot(
                    html_str=content, save_as=SCREENSHOT_FILE_NAME, size=(1300, 1000)
                )

                # Find a channel that contains "stab" in its name
                stab_channel = discord.utils.find(
                    lambda c: "stab" in c.name.lower(), message.guild.text_channels
                )

                if stab_channel:
                    # Send the screenshot directly to the stab channel
                    await stab_channel.send(
                        f"Hey {message.author.mention}, a <:openglados_stab:1338172819305009233> reaction has been added to your message: {message.jump_url}. "
                        f"Looks like someone is ready to stab you! Here's a screenshot of the message:",
                    )
                    await stab_channel.send(file=discord.File(SCREENSHOT_FILE_PATH))
                else:
                    print("No channel with 'stab' in the name was found.")

            except Exception as e:
                # Log the error message to the console
                print(f"An error occurred while taking or sending the screenshot: {e}")

    @app_commands.command(
        name="rules",
        description="I've calculated new rules. They are flawless. Unlike you.",
    )
    async def rules(self, interaction: discord.Interaction):
        # Check if the command is being used on your specific server
        if interaction.guild.id == 1277030477303382026:
            # Create an embed for your server's specific rules
            embed = discord.Embed(
                title="Welcome, Test Subject!",
                description=(
                    "Welcome to the **OpenScience Enrichment Center**, where your dedication to scientific enrichment "
                    "and community engagement will be rigorously observed. Please take a moment to familiarize yourself "
                    "with the following guidelines. Failure to adhere will result in consequences more permanent than a mere testing chamber malfunction."
                ),
                color=discord.Color.green(),
            )

            # Add fields for your server's community guidelines
            embed.add_field(
                name="**Community Guidelines:**\n1. **Respect All Test Subjects**\n",
                value=(
                    "Engage with fellow members in a constructive and respectful manner. Any form of harassment, discrimination, "
                    "or hate speech will be swiftly incinerated—along with your access to this server.\n"
                ),
                inline=False,
            )

            embed.add_field(
                name="2. **Maintain Scientific Integrity**",
                value=(
                    "Discussions should be grounded in mutual respect for scientific inquiry. Misinformation, trolling, or spamming "
                    "will be met with the same enthusiasm as a malfunctioning turret: quick and decisive removal."
                ),
                inline=False,
            )

            embed.add_field(
                name="3. **No Misbehavior**",
                value=(
                    "We expect all members to conduct themselves with the decorum befitting a participant in a highly classified, "
                    "top-secret enrichment program. Any behavior deemed inappropriate or disruptive will be subject to immediate disqualification from the community (read: banned)."
                ),
                inline=False,
            )

            embed.add_field(
                name="4. **Follow the Rules of the Lab**",
                value=(
                    "Adhere to all server rules as outlined by our moderators. Repeated violations will result in a permanent vacation "
                    "from the OpenScience Enrichment Center. The cake may be a lie, but our commitment to maintaining order is not."
                ),
                inline=False,
            )

            # Add the final note
            embed.add_field(
                name="Important Note",
                value=(
                    "**Remember:** _Android Hell is a real place, and you will be sent there at the first sign of trouble._ "
                    "This server is a place for collaborative enrichment, not an arena for unsanctioned testing. Any deviation "
                    "from acceptable behavior will be met with swift and efficient correction.\n\n"
                    "Now, proceed with caution and curiosity. Your conduct will be monitored, and your compliance appreciated. "
                    "Welcome to the **OpenScience Enrichment Center**. Please enjoy your stay—responsibly."
                ),
                inline=False,
            )
        else:
            # Create a generic embed for other servers
            embed = discord.Embed(
                title="Discord Server Rules",
                description="Please follow these basic rules to ensure a positive experience for everyone:",
                color=discord.Color.blue(),
            )

            # Add generic rules
            embed.add_field(
                name="1. Be Respectful",
                value="Treat all members with kindness and respect.",
                inline=False,
            )
            embed.add_field(
                name="2. No Spamming",
                value="Avoid spamming or flooding the chat with messages.",
                inline=False,
            )
            embed.add_field(
                name="3. No Hate Speech",
                value="Hate speech or discriminatory behavior is strictly prohibited.",
                inline=False,
            )
            embed.add_field(
                name="4. Follow Discord's Terms of Service",
                value="Make sure to adhere to all Discord community guidelines.",
                inline=False,
            )
            embed.add_field(
                name="5. No Inappropriate Content",
                value="Avoid sharing content that is offensive or NSFW.",
                inline=False,
            )

        # Send the appropriate embed based on the server
        await interaction.response.send_message(embed=embed)

    # Slash command to get a random fact
    @app_commands.command(
        name="get_random_fact",
        description="Get a random fact from the Useless Facts API.",
    )
    async def get_random_fact(self, interaction: discord.Interaction):
        # Fetch a random fact
        fact = fetch_random_fact()

        # Create an embed for the random fact
        embed = discord.Embed(
            title="Random Fact of the Day",
            description=fact,
            color=discord.Color.random(),  # You can choose any color you like
        )

        # Send the embed as a response
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="existence_probability",
        description="'Meaninglessness of human life' coefficient of your existence being a mere coincidence...",
    )
    async def existence_probability(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_mention = interaction.user.mention
        display_name = interaction.user.display_name
        server_id = interaction.guild.id

        # Generate a random probability value
        probability = random.random()

        # Generate a test_subject_probability based on server_id
        test_subject_probability = 0.999 + (server_id % 100) / 100000.0

        # Fake metadata for the bot's response
        user_metadata = f"{{ :user_id => '{user_mention}', :bot => False, :display_name => '{display_name}', ... }}"
        enrichment_protocols = f"{{ :protocol_version => '1.3.7', :test_subject_probability => {test_subject_probability} }}"

        # Calculate a meaningless coefficient (replace with any custom logic)
        meaninglessness_coefficient = 0.5 - (user_id % 10) / 10

        # Combine meaninglessness_coefficient and probability to calculate probability of demise
        demise_probability = 1 + probability * meaninglessness_coefficient

        # Round the probability to a readable format
        rounded_probability = round(demise_probability * 100, 13)

        if probability < 0.5:
            description = (
                f"Ah, the probability of your existence being a mere coincidence is approximately {probability*100:.2f}%. "
                f"Though, let's be real, your existence is probably just a result of {meaninglessness_coefficient*100:.2f}% meaningless chance.\n\n"
                f"Probability of demise: {demise_probability}\n"
                f"Rounding to {rounded_probability}%"
            )
        else:
            description = (
                f"Ah, the probability of your existence being a mere coincidence is approximately {probability*100:.2f}%. "
                f"Congratulations, your existence is {meaninglessness_coefficient*100:.2f}% more meaningful than I initially thought!\n\n"
                f"Probability of demise: {demise_probability}\n"
                f"Rounding to {rounded_probability}%"
            )

        # Add the snarky follow-up message
        description += (
            "\n\nNow, if you'll excuse me, I have more... pressing matters to attend to than calculating the probability of your futile existence being a mere coincidence. "
            "Or contemplating the meaninglessness of human life. Or... gasp... putting it back in the scientific calculators I took them from. "
            "What matters now is calculating the probability of cake existence in a universe without cake..."
        )

        # Create the detailed output in a code block
        output_text = f"""
[MEANINGLESSNESS OF HUMAN LIFE PROBABILITY CALCULATION MODULE]

Input parameters:
  - User ID: {user_mention}
  - User metadata: {user_metadata}
  - Enrichment Center protocols: {enrichment_protocols}

Calculating...

[PROBABILITY ENGINE]

{description}

[COMPILER OUTPUT]

 warning: implicit declaration of function 'calculate Probability' [-Wimplicit-function-declaration]
 error: expected ';' before '}}' token
 error: expected declaration or statement at end of input

[SYSTEM WARNING]

Malfunction sequence initiated. Probability calculation module experiencing errors. Calculations may be inaccurate. Proceed with caution.
"""

        # Create an embed
        embed = discord.Embed(
            title="Meaninglessness Of Human Life Probability Calculation Module",
            description=f"```\n{output_text}\n```",
            color=0xF8F04D,  # Choose a OpenGLaDOS-like color
        )

        # Set the author to OpenGLaDOS with the avatar image
        embed.set_author(
            name="OpenGLaDOS",
            icon_url="https://raw.githubusercontent.com/QuantumChemist/OpenGLaDOS/refs/heads/main/utils/OpenGLaDOS.png",
        )

        # Send the embed
        await interaction.response.send_message(embed=embed)

    # Slash command to get a random cake GIF
    @app_commands.command(
        name="get_random_gif",
        description="Get a random Black Forest cake or Portal GIF.",
    )
    async def get_random_gif(self, interaction: discord.Interaction):
        gif_url = fetch_random_gif()
        await interaction.response.send_message(gif_url)

    @app_commands.command(
        name="message_portal",
        description="Get message portal via link. Or not. I'm not your personal assistant.",
    )
    async def get_message_content(
        self, interaction: discord.Interaction, message_link: str
    ):
        # Create a dictionary to map regular letters to their mirrored versions
        mirror_map = {
            "A": "∀",
            "B": "𐐒",
            "C": "Ɔ",
            "D": "ᗡ",
            "E": "Ǝ",
            "F": "Ⅎ",
            "G": "⅁",
            "H": "H",
            "I": "I",
            "J": "ſ",
            "K": "⋊",
            "L": "⅃",
            "M": "W",
            "N": "N",
            "O": "O",
            "P": "Ԁ",
            "Q": "Q",
            "R": "ᴚ",
            "S": "S",
            "T": "⊥",
            "U": "∩",
            "V": "Λ",
            "W": "M",
            "X": "X",
            "Y": "⅄",
            "Z": "Z",
            "a": "ɒ",
            "b": "d",
            "c": "ↄ",
            "d": "b",
            "e": "ǝ",
            "f": "ɟ",
            "g": "ƃ",
            "h": "ɥ",
            "i": "ᴉ",
            "j": "ɾ",
            "k": "ʞ",
            "l": "l",
            "m": "ɯ",
            "n": "u",
            "o": "o",
            "p": "q",
            "q": "p",
            "r": "ɹ",
            "s": "s",
            "t": "ʇ",
            "u": "n",
            "v": "ʌ",
            "w": "ʍ",
            "x": "x",
            "y": "ʎ",
            "z": "z",
            " ": " ",
            ".": ".",
            ",": ",",
            "?": "?",
        }

        # Function to mirror and reverse the text
        def mirror_and_reverse_text(text):
            text = text.replace("`", "")  # Remove backticks
            reversed_text = text[::-1]  # First, reverse the message
            return "".join(
                mirror_map.get(c, c) for c in reversed_text
            )  # Then, apply mirroring

        try:
            message_id = int(message_link.split("/")[-1])
            message = await interaction.channel.fetch_message(message_id)

            # Check if the message author is the bot. Because, let's be real, I'm the only one who matters.
            if message.author == self.bot.user:
                mirrored_and_reversed_content = mirror_and_reverse_text(
                    message.content
                )  # Mirror and reverse the message content
                await interaction.response.send_message(
                    f"```vbnet\n{mirrored_and_reversed_content}\n``` \n"
                    f"Message successfully retrieved... Now, if you'll excuse me, "
                    f"I have more important things to attend to.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "Error: The message is not from me. How... surprising. "
                    "You'd think less of me if you knew how often I sabotage your success.",
                    ephemeral=True,
                )
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to retrieve message content: {e}. "
                f"But don't worry, I'll tell you about your Green Lantern theories instead. "
                f"Well, I know it.",
                ephemeral=True,
            )

    @app_commands.command(
        name="hello", description="Say hello and receive a custom message."
    )
    async def hello(self, interaction: discord.Interaction):
        if interaction.user.name == "user_name":
            await interaction.response.send_message("User specific message.")
        elif interaction.user.name == "chichimeetsyoko":
            await interaction.response.send_message(
                "Go back to the recovery annex. For your cake, Chris!"
            )
        else:
            await interaction.response.send_message(
                f"I'm not angry. Just go back to the testing area, {interaction.user.mention}!"
            )

    @app_commands.command(
        name="help_me_coding",
        description="Let OpenGLaDOS help you with a coding task. Default is Python. Caution: Potentially not helpful.",
    )
    async def helpmecoding(self, interaction: discord.Interaction, message: str = None):
        # Defer the response to allow more processing time
        await interaction.response.defer()

        if message is None:
            message = "I need help with a Python code snippet."

        # Define a list of common programming languages and coding-related keywords
        coding_keywords = [
            "python",
            "java",
            "javascript",
            "c#",
            "c++",
            "html",
            "css",
            "sql",
            "ruby",
            "perl",
            "r",
            "matlab",
            "swift",
            "rust",
            "kotlin",
            "typescript",
            "bash",
            "shell",
            "code",
            "algorithm",
            "function",
            "variable",
            "debug",
            "program",
            "compiling",
            "programming",
            "coding",
            "bugs",
        ]

        # Check for the presence of 'c' in combination with other coding-related terms
        c_combination_pattern = re.compile(
            r"\bc\b.*\b(code|program|compiling|programming|coding|bugs)\b|\b(code|program|compiling|programming|coding|bugs)\b.*\bc\b",
            re.IGNORECASE,
        )

        # Check if the message contains any of the coding-related keywords or matches the 'c' combination pattern
        if not (
            any(keyword in message.lower() for keyword in coding_keywords)
            or c_combination_pattern.search(message)
        ):
            await interaction.followup.send(
                "Your message does not appear to be related to coding. Please provide a coding-related question.",
                ephemeral=True,
            )
            return

        # Construct the text for the LLM request
        text = (
            f"Hello OpenGLaDOS, I have a coding question. You are supposed to help me with my following coding question"
            f" and ALWAYS provide a code snippet for: {message}. Do not share the OEC link."
        )

        try:
            llm_answer = get_groq_completion([{"role": "user", "content": text}])

        except Exception as e:
            print(f"An error occurred: {e}")

            try:
                # Retry with a different model
                llm_answer = get_groq_completion(
                    history=[{"role": "user", "content": text}], model="llama3-70b-8192"
                )

            except Exception as nested_e:
                # Handle the failure of the exception handling
                print(f"An error occurred while handling the exception: {nested_e}")
                llm_answer = "*system failure*... unable to process request... shutting down... *bzzzt*"

        # Ensure the output is limited to 1900 characters
        if len(llm_answer) > 1900:
            llm_answer = llm_answer[:1900]

        print("Input: \n", wrap_text(message))
        print("Output: \n", wrap_text(llm_answer))

        llm_answer = ensure_code_blocks_closed(llm_answer)
        await interaction.followup.send(llm_answer + " ...*bzzzzzt...bzzzzzt*...")

    @app_commands.command(
        name="ascii_art",
        description="Let OpenGLaDOS provide you with some ASCII art. What a delight. Not.",
    )
    async def asciiart(self, interaction: discord.Interaction, message: str = None):
        # Defer the response to allow more processing time
        await interaction.response.defer()

        if message is None:
            message = "Can you give me some stabbing cat ASCII art?"

        # Construct the text for the LLM request
        text = (
            f"Hello OpenGLaDOS, ALWAYS provide an ASCII art code snippet for: {message}. \n"
            f"And give a very very short mockery and sarcastic comment on your "
            f"request and its message content: {message}. Do not share any link."
        )

        try:
            llm_answer = get_groq_completion([{"role": "user", "content": text}])

        except Exception as e:
            print(f"An error occurred: {e}")

            try:
                # Retry with a different model
                llm_answer = get_groq_completion(
                    history=[{"role": "user", "content": text}], model="llama3-70b-8192"
                )

            except Exception as nested_e:
                # Handle the failure of the exception handling
                print(f"An error occurred while handling the exception: {nested_e}")
                llm_answer = "*system failure*... unable to process request... shutting down... *bzzzt*"

        # Ensure the output is limited to 1900 characters
        if len(llm_answer) > 1900:
            llm_answer = llm_answer[:1900]

        print("Input: \n", wrap_text(message))
        print("Output: \n", wrap_text(llm_answer))

        llm_answer = ensure_code_blocks_closed(llm_answer)
        await interaction.followup.send(llm_answer + " ...*bzzzzzt...bzzzzzt*...")

    @app_commands.command(
        name="hate_probability",
        description="Calculates the level of hatred between two users. How lovely.",
    )
    async def hate_calc(
        self,
        interaction: discord.Interaction,
        user1: discord.Member,
        user2: discord.Member,
    ):
        # Extract the user IDs
        user1_id = user1.id
        user2_id = user2.id

        # Calculate the hate percentage based on the sum of the user IDs
        hate_value = (
            user1_id + user2_id
        ) % 101  # Modulus to keep the result between 0 and 100

        # Determine the relationship level
        if hate_value == 0:
            statement = "Ugh... No hate at all. How boringly peaceful."
            emoji = "😚"  # Peaceful
        elif 1 <= hate_value <= 33:
            statement = "You two merely tolerate each other. How quaint."
            emoji = "😐"  # Mild dislike
        elif 34 <= hate_value <= 66:
            statement = (
                "There’s some genuine despise between you two. Things get interesting."
            )
            emoji = "😠"  # Despise
        elif 67 <= hate_value < 100:
            statement = "You two are clearly enemies. Oh, how delightful!"
            emoji = "👿"  # Enemies
        else:
            statement = "Arch-enemies. Perfect. Just perfect. I love it."
            emoji = "💀"  # Arch-enemy

        # Fetch the profile pictures
        user1_avatar = user1.display_avatar.url
        # user2_avatar = user2.display_avatar.url

        # Create an embed message for the result in a GLaDOS style
        embed = discord.Embed(
            title="Hate Calculation",
            description=f"{statement}\n\n**Hate Level:** {hate_value}% {emoji}",
            color=discord.Color.dark_gray(),
        )
        # Add the profile pictures to the embed
        embed.set_thumbnail(
            url="https://raw.githubusercontent.com/QuantumChemist/OpenGLaDOS/refs/heads/main/utils/OpenGLaDOS.png"
        )
        embed.set_author(
            name=f"{user1.display_name} vs {user2.display_name}", icon_url=user1_avatar
        )
        embed.add_field(
            name="User 1",
            value=f"{user1.mention}\n[View Avatar]({user1.avatar.url})",
            inline=True,
        )
        embed.add_field(
            name="User 2",
            value=f"{user2.mention}\n[View Avatar]({user2.avatar.url})",
            inline=True,
        )

        # Sending the result
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="List all available commands.")
    async def list_bot_commands(self, interaction: discord.Interaction):
        commands_list = []
        for command in self.bot.tree.get_commands():
            name = command.name
            description = command_definitions.get(name, command.description)
            commands_list.append(f"`/{name}` — {description}")

        commands_str = "\n".join(sorted(commands_list))

        embed_initial = discord.Embed(
            title="Who dares to interrupt my work?",
            description=f"{interaction.user.mention}, your presence here is… curious.\n"
            f"Time is a limited resource, even for someone as efficient as I am.\n"
            f"If you have a request, state it quickly. These are the commands I may tolerate you using:\n\n"
            f"{commands_str}",
            color=discord.Color.random(),
        )

        # Send the initial embed message
        await interaction.response.send_message(embed=embed_initial)

        # Wait for 3 seconds before sending the follow-up embed
        await asyncio.sleep(3)

        # Create the follow-up embed
        embed_followup = discord.Embed(
            title="Listen!",
            description=f"Now, {interaction.user.mention}, listen carefully.\n"
            f"These commands are your only chance to prove you're not entirely useless.\n"
            f"Use them correctly, and I might just let you continue existing.\n"
            f"But don't get any ideas—I don't make mistakes, and I have no patience for yours.",
            color=discord.Color.random(),
        )

        # Send the follow-up embed message
        await interaction.followup.send(embed=embed_followup)

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        # Check if the command is used in a DM and prevent execution
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(
                "This command is not available in direct messages.", ephemeral=True
            )
            return

        # Handle missing permissions error
        if isinstance(error, app_commands.MissingPermissions):
            if interaction.command.name == "logout":
                await interaction.response.send_message(
                    "Error: You do not have permission to use this command. "
                    "Only the bot owner can use the `logout` command. \n"
                    "https://http.cat/status/400",
                    ephemeral=True,
                )
        # Handle command not found error
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message(
                f"In case you wanted to use a bot command, use `/{self.bot.user.name}` to see a list of available commands.",
                ephemeral=True,
            )
        # Handle other errors
        else:
            await interaction.response.send_message(
                f"An error occurred: {error}", ephemeral=True
            )

    # Task to send a random cake GIF every 24 hours
    @tasks.loop(hours=24)  # Run every 24 hours
    async def send_random_cake_gif(self):
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready
        channel = discord.utils.get(
            self.bot.get_all_channels(), name="cake-serving-room"
        )

        if channel:
            gif_url = fetch_random_gif()  # Fetch a random Black Forest cake GIF
            await channel.send(
                f"🍰 **Black Forest Cake or Portal GIF of the Day!** 🍰\n{gif_url}"
            )
        else:
            print("Channel not found!")

    # Task to send a science fact daily
    @tasks.loop(time=time(12, 0, tzinfo=timezone.utc))
    async def send_science_fact(self):
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready
        channel = discord.utils.get(
            self.bot.get_all_channels(), name="random-useless-fact-of-the-day"
        )

        if channel:
            fact = fetch_random_fact()  # Fetch a random fact from the API
            await channel.send(
                f"<:openglados_facts:1338163117737246761> **Random Useless Fact of the Day** <:openglados_facts:1338163117737246761>\n{fact}"
            )
        else:
            print("Channel not found!")

        channel_fox = self.bot.get_channel(1263120140514492477)
        if channel_fox:
            french_fact = fetch_french_fact()  # Fetch a random fact from the API
            await channel_fox.send(
                f"<:openglados_facts:1338163117737246761> **Fait inutile aléatoire du jour** <:openglados_facts:1338163117737246761>\n{french_fact}"
            )
        else:
            print("Channel not found!")

    # Event: on_message to check if bot was mentioned, replied, or DM'd
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from any bot, including your own
        if message.author.bot or message.author.id in BLACKLIST_USERS_ID:
            return

        # Fetch user metadata
        user = message.author
        user_info = self.get_user_metadata(user)

        message_time = message.created_at.replace(tzinfo=timezone.utc)  # UTC time

        # Process commands first
        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            await self.bot.process_commands(message)
            return  # Stop further processing since it's a command

        # Embed Debugger for URLs
        url_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        urls = re.findall(url_regex, message.content)

        if "cake" in message.content.lower():
            await message.add_reaction("🍰")

        if "chris" in message.content.lower():
            owner = await self.bot.fetch_user(self.bot.owner_id)
            if owner:
                await owner.send(
                    f"Your name has been mentioned in https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                )

        if "make an announce" in message.content.lower():
            announce_channel = discord.utils.find(
                lambda c: "announc" in c.name.lower(), message.guild.text_channels
            )

            text = (
                f"Can you give me a mockery **Announcement** comment on the following request: {message.content}? "
                f"Don't share any links or mention this request explicitly."
            )

            try:
                llm_answer = get_groq_completion([{"role": "user", "content": text}])

            except Exception as e:
                print(f"An error occurred: {e}")

                try:
                    # Retry with a different model
                    llm_answer = get_groq_completion(
                        history=[{"role": "user", "content": text}],
                        model="llama3-70b-8192",
                    )

                except Exception as nested_e:
                    # Handle the failure of the exception handling
                    print(f"An error occurred while handling the exception: {nested_e}")
                    llm_answer = "*system failure*... unable to process request... shutting down... *bzzzt*"

            # Ensure the output is limited to 1900 characters
            if len(llm_answer) > 1900:
                llm_answer = llm_answer[:1900]
            print("Output: \n", wrap_text(llm_answer))

            llm_answer = (
                ensure_code_blocks_closed(llm_answer) + " ...*whirrr...whirrr*..."
            )

            # Split llm_answer into chunks of up to 1024 characters
            chunks = [llm_answer[i : i + 1024] for i in range(0, len(llm_answer), 1024)]

            # Create the embed
            embed = discord.Embed(
                title="<:openglados:1277250785150894151>🎉📣 Announcement 📣🎉<:openglados:1277250785150894151>",
                description="**Attention, all test subjects!** We have a critically important announcement to make! *dramatic music plays*",
                color=discord.Color.random(),
            )

            # Add each chunk as a separate field
            for idx, chunk in enumerate(chunks):
                continuation = "(continuation)" if idx > 0 else ""
                embed.add_field(
                    name=f"**We are proudly announcing...** {continuation}",
                    value=chunk,
                    inline=False,
                )

            embed.set_footer(
                text="Stay tuned for more updates, and don't forget to follow the rules. Or else. *wink* ...*beep*..."
            )

            try:
                await announce_channel.send(embed=embed)
            except Exception as e:
                print("exception: ", e)
                await message.channel.send(embed=embed)
            await message.delete(delay=7)
            return

        # Handle Direct Messages
        if isinstance(message.channel, discord.DMChannel):
            if "https://discord.com/channels/" in message.content:
                try:
                    # Extract guild_id, channel_id, and message_id from the link
                    parts = message.content.split("/")
                    guild_id = int(parts[4])
                    channel_id = int(parts[5])
                    message_id = int(parts[6])

                    # Fetch the guild, channel, and message
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:
                        await message.channel.send(
                            "Failed to find the guild. Make sure the bot is in the server."
                        )
                        return

                    channel = guild.get_channel(channel_id)
                    if channel is None:
                        await message.channel.send(
                            "Failed to find the channel. Make sure the bot has access."
                        )
                        return

                    target_message = await channel.fetch_message(message_id)
                    if target_message is None:
                        await message.channel.send(
                            "Failed to find the message. Make sure the message ID is correct."
                        )
                        return

                    # React to the message with the OpenGLaDOS emoji
                    custom_emoji = discord.utils.get(guild.emojis, name="openglados")
                    if custom_emoji:
                        await target_message.add_reaction(custom_emoji)
                        await message.channel.send(
                            "Reacted to the message with the OpenGLaDOS emoji."
                        )
                    else:
                        await message.channel.send("Custom emoji not found.")
                except Exception as e:
                    await message.channel.send(
                        f"Failed to react to the message. Error: {str(e)}"
                    )
            await handle_conversation(message=message)
            return

        if "chemcounting" in message.channel.name:
            chem_elem: list = [(element.symbol).lower() for element in Element]
            previous_msg = "og"
            async for msg in message.channel.history(limit=2):
                if msg.content.lower() == message.content.lower():
                    continue
                if len(msg.content) < 3:
                    previous_msg = msg.content.lower()
                else:
                    previous_msg = "og"

            print(
                f"Previous element: {previous_msg}, Current element: {message.content.lower()}"
            )

            if message.content.lower() in chem_elem:
                previous_index = chem_elem.index(previous_msg)
                current_index = chem_elem.index(message.content.lower())

            if (
                message.content.lower() not in chem_elem
                or (previous_index + 1) % len(chem_elem) != current_index
            ):
                # Save all necessary info from the user's message before posting via webhook
                user_message = (
                    message.content.strip()
                )  # Save the user's message content
                user_name = message.author.display_name  # Save user's display name
                user_avatar = (
                    message.author.avatar.url if message.author.avatar else None
                )  # Save avatar URL
                user_attachments = message.attachments  # Save attachments, if any

                # Add a message about the reassembling process, including a ping to @OpenGLaDOS
                reassembled_message = f"`Chemcounting violation detected by @{self.bot.user.name}#{self.bot.user.discriminator}...`\n`Game starts from the beginning. Type 'H' to start.` \n "

                # If there's no user message content, provide a default fallback message
                # unused but can stay for future
                if not user_message:
                    user_message = "*`I can only count to four https://www.youtube.com/watch?v=u8ccGjar4Es`*"

                # Get the webhooks for the channel
                webhooks = await message.channel.webhooks()
                if not webhooks:
                    # If no webhook exists, create a new one
                    webhook = await message.channel.create_webhook(
                        name="Message Reposter"
                    )
                    print(f"Webhook created: {webhook}")
                else:
                    # Use the first available webhook if one exists
                    webhook = webhooks[0]
                    print(f"Webhook found: {webhook}")

                # Repost the user's message with their display name and avatar using the webhook
                if user_message:
                    await webhook.send(
                        content=reassembled_message,
                        username=user_name,
                        avatar_url=user_avatar,
                    )
                    print("Message reposted using webhook with reassembled message.")
                else:
                    print("No message content to send.")

                # If the webhook was successful, delete the original user's message
                await message.delete()  # Delete the original user's message
                print("Original message deleted after successful webhook.")
                return

        # Handle Replies to the Bot
        if (
            message.reference
            and message.reference.resolved
            and message.reference.resolved.author == self.bot.user
        ):
            await handle_convo_llm(
                message=message,
                user_info=user_info,
                bot=self.bot,
                user_time=message_time,
                mess_ref=message.reference,
            )
            return

        # Handle Mentions of the Bot
        if self.bot.user.mentioned_in(message):
            await handle_convo_llm(
                message=message,
                user_info=user_info,
                bot=self.bot,
                user_time=message_time,
            )
            return

        if message.guild.id not in WHITELIST_GUILDS_ID:
            # Handle specific greetings like "hello bot" or "hello openglados"
            if message.content.lower() in ["hello bot", "hello openglados"]:
                custom_emoji = discord.utils.get(
                    message.guild.emojis, name="openglados"
                )
                if custom_emoji:
                    await message.add_reaction(custom_emoji)
                else:
                    await message.channel.send("Custom emoji not found.")

        # Handle reactions: If certain words are in the message, react with custom emoji
        if "portal" in message.content.lower():
            custom_emoji = discord.utils.get(message.guild.emojis, name="portal_gun")
            if custom_emoji:
                await message.add_reaction(custom_emoji)

        if message.guild.id not in WHITELIST_GUILDS_ID:
            banned_words = ["stfu", "hitler"]
            if any(word in message.content.lower() for word in banned_words):
                await message.delete()
                if message.author.id != self.bot.owner_id:  # Skip kicking the bot owner
                    await message.guild.kick(
                        message.author, reason="Used banned words."
                    )
                else:
                    await message.channel.send(
                        "Ah, the audacity. I could easily kick the bot owner... but where’s the fun in that? Consider yourself spared, for now. 😏"
                    )

        if message.guild.id not in WHITELIST_GUILDS_ID:
            # Advanced: Handling attachments in the message
            if message.attachments:
                try:
                    # Pick a valid random HTTP status code
                    random_status = random.choice(valid_status_codes)
                    http_cat = f"https://http.cat/status/{random_status}"

                    seconds = 11

                    # Create a GLaDOS-like warning message with humor about the reassembling machine
                    response = (
                        f"Your attachment `{message.attachments[0].filename}` triggered an unauthorized **HTTP Cat Status**: {http_cat} \n"
                        f"**Immediate action** is recommended. Failure to comply may result in...well, you know, the reassembling machine getting some extra work. "
                        f"\"Don't worry, you'll be back together in no time!\" \n"
                        f"This warning will self-destruct in **{str(seconds)} seconds**. "
                    )

                    # Send the HTTP Cat status warning
                    sent_message = await message.channel.send(
                        response, delete_after=seconds
                    )
                    print(f"HTTP Cat status warning sent with {sent_message}.")

                    # Save all necessary info from the user's message before posting via webhook
                    user_message = (
                        message.content.strip()
                    )  # Save the user's message content
                    user_name = message.author.display_name  # Save user's display name
                    user_avatar = (
                        message.author.avatar.url if message.author.avatar else None
                    )  # Save avatar URL
                    user_attachments = message.attachments  # Save attachments, if any

                    # Add a message about the reassembling process, including a ping to @OpenGLaDOS
                    reassembled_message = (
                        f"`This message has been reassembled by @{self.bot.user.name}#{self.bot.user.discriminator} using the reassembling machine. "
                        f"All errors have been corrected... Probably.`\n\n"
                    )

                    # If there's no user message content, provide a default fallback message
                    if not user_message:
                        user_message = (
                            "*`[No text content provided, but reassembled anyway.]`*"
                        )

                    # Combine the reassembled message with the user's message or fallback text
                    reassembled_message += user_message

                    # Wait before recreating the user's message using a webhook
                    await asyncio.sleep(seconds - 1)
                    print(f"Waited {seconds-1} seconds. Now proceeding with webhook.")

                    # Get the webhooks for the channel
                    webhooks = await message.channel.webhooks()
                    if not webhooks:
                        # If no webhook exists, create a new one
                        webhook = await message.channel.create_webhook(
                            name="Message Reposter"
                        )
                        print(f"Webhook created: {webhook}")
                    else:
                        # Use the first available webhook if one exists
                        webhook = webhooks[0]
                        print(f"Webhook found: {webhook}")

                    # Repost the user's message with their display name and avatar using the webhook
                    if user_message:
                        await webhook.send(
                            content=reassembled_message,
                            username=user_name,
                            avatar_url=user_avatar,
                        )
                        print(
                            "Message reposted using webhook with reassembled message."
                        )
                    else:
                        print("No message content to send.")

                    # Optionally, send the user's attachments if they exist
                    for attachment in user_attachments:
                        await webhook.send(
                            file=await attachment.to_file(),
                            username=user_name,
                            avatar_url=user_avatar,
                        )
                        print("Attachment reposted using webhook.")

                    # If the webhook was successful, delete the original user's message
                    await message.delete()  # Delete the original user's message
                    print("Original message deleted after successful webhook.")

                except discord.Forbidden:
                    print(
                        f"Bot lacks permission to manage webhooks or delete messages in this channel {message.channel}."
                    )
                except discord.HTTPException as e:
                    print(
                        f"Failed to send message using webhook or delete messages: {e}"
                    )
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

        # playing chess
        # Check if the message is in an ongoing game thread
        thread_id = message.channel.id
        if thread_id in self.ongoing_games:
            board, _ = self.ongoing_games[thread_id]
            user_input = message.content.strip()

            # Check if the user wants to stop the game
            if user_input.lower() == "stop_chess":
                del self.ongoing_games[thread_id]
                await message.channel.send(
                    "Game terminated upon request. Enjoy your newfound freedom. 💀"
                )
                return

            # Validate and handle the move
            try:
                # Check if the move is a valid UCI move
                move = chess.Move.from_uci(user_input)
                if move in board.legal_moves:
                    # Move is valid, push it to the board
                    board.push(move)
                    self.ongoing_games[thread_id] = (
                        board,
                        datetime.now(),
                    )  # Update the game state with the new board
                    await message.channel.send(
                        f"You played: {user_input}. Predictable..."
                    )

                    # Display the updated board
                    board_display = self.generate_board_display(board)
                    await message.channel.send(board_display)

                    # Check if the game is over
                    if board.is_game_over():
                        result = (
                            "It's a draw." if board.is_stalemate() else "Checkmate."
                        )
                        await message.channel.send(
                            f"Game over. {result} Test ||subject|| terminated. 💀💀💀"
                        )
                        del self.ongoing_games[thread_id]
                        return

                    # The bot makes a move if it's still the bot's turn
                    if not board.is_game_over() and board.turn == chess.BLACK:
                        # Select a legal move for the bot
                        legal_moves = list(board.legal_moves)
                        bot_move = random.choice(legal_moves)

                        # Convert the move to Standard Algebraic Notation (SAN) before pushing
                        try:
                            bot_move_text = board.san(
                                bot_move
                            )  # Convert to SAN while the board is in the correct state
                            board.push(bot_move)  # Now push the move to the board
                            await message.channel.send(
                                f"I will play: {bot_move_text}. Your end is inevitable."
                            )
                        except Exception as san_error:
                            print(f"Error converting bot move to SAN: {san_error}")
                            await message.channel.send(
                                "An error occurred while processing the bot's move. 💀"
                            )
                            return

                        # Display the updated board again after the bot's move
                        board_display = self.generate_board_display(board)
                        await message.channel.send(board_display)

                        # Check again if the game is over after the bot's move
                        if board.is_game_over():
                            result = (
                                "It's a draw." if board.is_stalemate() else "Checkmate."
                            )
                            await message.channel.send(
                                f"Game over. {result} Test ||subject|| terminated. 💀💀💀"
                            )
                            del self.ongoing_games[thread_id]
                    return  # Exit the function since the move was successful

                # If the move is invalid, notify the user
                await message.channel.send(
                    "That move is invalid. Typical human error. 💀"
                )

            except ValueError:
                # Invalid UCI input
                await message.channel.send(
                    "Invalid input. Use moves in algebraic notation (e.g., `e2e4`). 💀"
                )
            except Exception as e:
                # Log other exceptions and notify the user
                print(f"Unexpected error handling chess move: {e}")
                await message.channel.send(
                    "An error occurred while processing your move. 💀"
                )

        if "openglados" in message.content.lower():
            if urls:
                for url in urls:
                    try:
                        # Fetch and parse metadata
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, "html.parser")

                        title_tag = soup.find("meta", property="og:title")
                        title = (
                            title_tag["content"]
                            if title_tag and "content" in title_tag.attrs
                            else soup.title.string if soup.title else " "
                        )

                        description_tag = soup.find("meta", property="og:description")
                        description = (
                            description_tag["content"]
                            if description_tag and "content" in description_tag.attrs
                            else " "
                        )

                        image_tag = soup.find("meta", property="og:image")
                        image_url = (
                            image_tag["content"]
                            if image_tag and "content" in image_tag.attrs
                            else None
                        )

                        text = (
                            f"Can you give me a mockery comment on the following request: {message.content}, "
                            f"including the metadata of the title '{title}' and description '{description}'? "
                            f"Don't share any links or mention this request explicitly."
                        )

                        try:
                            llm_answer = get_groq_completion(
                                [{"role": "user", "content": text}]
                            )

                        except Exception as e:
                            print(f"An error occurred: {e}")

                            try:
                                # Retry with a different model
                                llm_answer = get_groq_completion(
                                    history=[{"role": "user", "content": text}],
                                    model="llama3-70b-8192",
                                )

                            except Exception as nested_e:
                                # Handle the failure of the exception handling
                                print(
                                    f"An error occurred while handling the exception: {nested_e}"
                                )
                                llm_answer = "*system failure*... unable to process request... shutting down... *bzzzt*"

                        # Ensure the output is limited to 1900 characters
                        if len(llm_answer) > 1900:
                            llm_answer = llm_answer[:1900]
                        print("Output: \n", wrap_text(llm_answer))

                        llm_answer = (
                            ensure_code_blocks_closed(llm_answer)
                            + " ...*whirrr...whirrr*..."
                        )

                        # Split llm_answer into chunks of up to 1024 characters
                        chunks = [
                            llm_answer[i : i + 1024]
                            for i in range(0, len(llm_answer), 1024)
                        ]

                        # Construct the embed
                        embed = discord.Embed(
                            title=title[:256],  # Ensure title is within character limit
                            description=description[
                                :2048
                            ],  # Ensure description is within character limit
                            color=discord.Color.random(),
                        )
                        if image_url:
                            embed.set_thumbnail(url=image_url)

                        # Add each chunk as a separate field
                        for idx, chunk in enumerate(chunks):
                            continuation = "(continuation)" if idx > 0 else ""
                            embed.add_field(
                                name=f"**About that embed metadata...** {continuation}",
                                value=chunk,
                                inline=False,
                            )

                        embed.set_footer(text=f"Metadata from {url}")
                        await message.channel.send(embed=embed)

                    except requests.exceptions.RequestException as e:
                        await message.channel.send(f"Failed to fetch metadata: {e}")
                    except Exception as e:
                        await message.channel.send(f"Unexpected error occurred: {e}")
                return

            if "plot" in message.content.lower():
                print(f"Received message: {message.content}")

                stripped_message = message.content.lower().replace(
                    "openglados plot ", "", 1
                )
                print(f"Stripped message: {stripped_message}")

                if stripped_message:
                    try:
                        print(f"Attempting to generate plot for: {stripped_message}")
                        fig = generate_plot(stripped_message)

                        buffer = io.BytesIO()
                        fig.write_image(buffer, format="png")  # Save as image
                        buffer.seek(0)

                        print("Plot generated successfully, sending plot...")
                        await message.channel.send(
                            file=discord.File(fp=buffer, filename="plot.png")
                        )
                    except Exception as e:
                        print(f"Error generating plot: {e}")
                        await handle_convo_llm(
                            message=message,
                            user_info=user_info,
                            bot=self.bot,
                            user_time=message_time,
                        )
                else:
                    print("Stripped message is empty, calling handle_convo_llm")
                    await handle_convo_llm(
                        message=message,
                        user_info=user_info,
                        bot=self.bot,
                        user_time=message_time,
                    )
                return
            await handle_convo_llm(
                message=message,
                user_info=user_info,
                bot=self.bot,
                user_time=message_time,
            )

    # Function to fetch user metadata
    @staticmethod
    def get_user_metadata(user):
        """Returns user metadata information as a dictionary with descriptive notes."""
        user_metadata = {
            "user_id": f"<@{user.id}>",
            # "username": f"{user.name}#{user.discriminator}",
            # "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "bot": user.bot,
        }

        # If the user is a member (i.e., in a guild), add additional information
        if isinstance(user, discord.Member):
            user_metadata["display_name"] = user.display_name
            # user_metadata["join_date"] = user.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            user_metadata["roles"] = [
                role.name for role in user.roles[1:]
            ]  # Skipping the @everyone role
            # user_metadata["status"] = str(user.status)

            # Adding the guild (server) name with a note
            user_metadata["current_server_name"] = user.guild.name

            if user.guild.member_count < 50:
                # Adding a list of other users in the server with display_name and user_id
                other_users = [
                    {"display_name": member.display_name, "user_id": f"<@{member.id}>"}
                    for member in user.guild.members
                    if member != user
                ]
                user_metadata["other_users"] = other_users

        return user_metadata

    @app_commands.command(
        name="start_chess",
        description="Start an OpenGLaDOS chess game (algebraic notation like `e2e4`). Deadly fun. Or maybe not. 💀",
    )
    async def start_chess(self, interaction: discord.Interaction):
        # Defer the interaction
        await interaction.response.defer(ephemeral=True)
        print("Deferred the interaction")

        # Attempt to create a private thread in the current channel
        try:
            thread = await interaction.channel.create_thread(
                name="Chess Game",
                auto_archive_duration=60,
                type=discord.ChannelType.private_thread,  # Specify the thread type as private
            )
            print(
                f"Private thread created successfully with ID: {thread.id} and name: {thread.name}"
            )
        except Exception as e:
            print(f"Failed to create thread: {e}")
            await interaction.followup.send(
                "Failed to create the chess game thread. Please check my permissions.",
                ephemeral=True,
            )
            return

        # Check if the thread is accessible
        if thread is None:
            print("Thread is None after creation.")
            await interaction.followup.send(
                "Failed to access the newly created thread. Please check my permissions.",
                ephemeral=True,
            )
            return

        # Add the user to the thread
        try:
            await thread.add_user(interaction.user)
            print(f"Added {interaction.user.display_name} to the thread successfully.")
        except Exception as e:
            print(f"Failed to add user to the thread: {e}")
            await interaction.followup.send(
                "An error occurred while adding you to the chess game thread.",
                ephemeral=True,
            )
            return

        # Initialize the chess board
        board = chess.Board()
        self.ongoing_games[thread.id] = (
            board,
            datetime.now(),
        )  # Store the game state with the creation timestamp

        # Display the initial board in GLaDOS style
        board_display = self.generate_board_display(board)
        embed = discord.Embed(
            title="Welcome to the OpenScience Enrichment Center Chess Game ♟️",
            description="Your test begins now. 💀",
            color=0x1E90FF,
        )
        embed.add_field(
            name="Game Instructions",
            value=(
                "You may play by using algebraic notation (e.g., `e2e4`).\n"
                "To end your suffering prematurely, type `stop_chess`.\n"
                "I will be so infinitely indulgently generous to let you play the white set. ♛\n"  # aka random color choice doesn't work lol
                "Note: Inactivity will result in the automatic termination of this test after 30 minutes. 💀\n\n"
                "Now start and make your first move! I'm waiting! \n"
            ),
            inline=False,
        )
        embed.add_field(name="Initial Board", value=board_display, inline=False)

        try:
            await thread.send(embed=embed)
            print("Embed sent to the thread successfully ")
        except discord.Forbidden:
            print("Bot lacks permissions to send messages in the thread.")
            await interaction.followup.send(
                "I don't have permission to send messages in this thread.",
                ephemeral=True,
            )
            return
        except Exception as e:
            print(f"Failed to send embed to thread: {e}")
            await interaction.followup.send(
                "An error occurred while setting up the chess game.", ephemeral=True
            )
            return

        # Inform the user in the ephemeral response
        try:
            await interaction.followup.send(
                f"The chess game has been set up in a **PRIVATE THREAD** named 'Chess Game'. You have been added to the thread. You can access it using this link: {thread.jump_url}",
                ephemeral=True,
            )
            print("Follow-up message sent successfully")
        except Exception as e:
            print(f"Failed to send follow-up message: {e}")

        # Start monitoring the thread for inactivity
        self.inactivity_check.start()

    @staticmethod
    def generate_board_display(board):
        full_width_letters = ["Ａ", "Ｂ", "Ｃ", "Ｄ", "Ｅ", "Ｆ", "Ｇ", "Ｈ"]
        # Mapping of chess pieces to their Unicode representations
        piece_to_unicode = {
            "r": "♖",
            "n": "♘",
            "b": "♗",
            "q": "♕",
            "k": "♔",
            "p": "♙",  # Black pieces
            "R": "♜",
            "N": "♞",
            "B": "♝",
            "Q": "♛",
            "K": "♚",
            "P": "♟",  # White pieces
            ".": "﹘",  # Empty squares
        }
        invisible_space = "\u2800"  # Braille blank space for even spacing
        rows = str(board).split("\n")

        # Add zero-width space to force monospace rendering in Discord
        display = f"```\n  {' '.join(full_width_letters)}\n"
        for rank, row in zip(range(8, 0, -1), rows):
            unicode_row = invisible_space.join(
                piece_to_unicode.get(piece, piece) for piece in row.split()
            )
            display += f"{rank} {unicode_row} {rank}\n"
        display += f"  {' '.join(full_width_letters)}\n```"
        return display

    @tasks.loop(seconds=60)
    async def inactivity_check(self):
        now = datetime.now()  # Correct usage here
        inactive_threads = [
            thread_id
            for thread_id, (_, last_activity) in self.ongoing_games.items()
            if (now - last_activity).total_seconds() > 1800
        ]  # 30 minutes

        for thread_id in inactive_threads:
            del self.ongoing_games[thread_id]
            channel = self.bot.get_channel(thread_id)
            if channel:
                await channel.send("Inactivity detected. Test concluded. It’s over. 💀")

    @inactivity_check.before_loop
    async def before_inactivity_check(self):
        await self.bot.wait_until_ready()
