import io
import os
import re
import html
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random
import requests
import cairosvg
import datetime
from io import BytesIO
from github import Github, GithubIntegration
from utils import (
    get_groq_completion,
    wrap_text,
    ensure_code_blocks_closed,
    split_text_by_period,
    create_cat_error_embed,
    render_certificate_playwright,
)


def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content by removing everything before <!DOCTYPE html> or <html> and after </html>
    """
    # Fix missing closing tags
    if "</body>" not in html_content:
        html_content += "\n</body>\n<footer>\n<p>© 2025 OpenGLaDOS. All rights reserved.</p>\n</footer>\n</html>"
    elif "</footer>" not in html_content:
        html_content += "\n</footer>\n</html>"
    elif "</html>" not in html_content:
        html_content += "\n</html>"

    # Find the start of HTML content - prefer DOCTYPE, fallback to <html>
    doctype_start = html_content.find("<!DOCTYPE html>")
    if doctype_start == -1:
        doctype_start = html_content.find(
            "<!doctype html>"
        )  # Case insensitive fallback

    if doctype_start != -1:
        html_start = doctype_start
    else:
        # Fallback to looking for <html> tag
        html_start = html_content.find("<html>")
        if html_start == -1:
            html_start = html_content.find("<HTML>")  # Case insensitive fallback

    # Find the end of HTML content
    html_end = html_content.rfind("</html>")
    if html_end == -1:
        html_end = html_content.rfind("</HTML>")  # Case insensitive fallback

    # If both start and end are found, extract content between them (inclusive)
    if html_start != -1 and html_end != -1:
        # Include the closing tag
        html_end += len("</html>")
        cleaned_content = html_content[html_start:html_end]
        return cleaned_content.strip()

    # If HTML tags not found, return original content
    return html_content.strip()


JUMP_URL_RE = re.compile(
    r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/(?P<guild_id>\d+|@me)/(?P<channel_id>\d+)/(?P<message_id>\d+)"
)

# Load environment variables from .env file
load_dotenv()


def get_github_app_token():
    """
    Generate GitHub App access token using JWT authentication
    """
    try:
        # Get GitHub App credentials from environment variables
        app_id = os.environ.get("APP_ID")
        installation_id = os.environ.get("INSTALLATION_ID")
        private_key_path = os.environ.get("PRIVATE_KEY")

        if not all([app_id, installation_id, private_key_path]):
            raise ValueError("Missing GitHub App environment variables")

        # Read private key from file
        if not os.path.exists(private_key_path):
            raise ValueError(f"Private key file not found: {private_key_path}")

        with open(private_key_path) as f:
            private_key = f.read()

        # Get installation access token using GithubIntegration
        gi = GithubIntegration(app_id, private_key)
        return gi.get_access_token(installation_id).token

    except Exception as e:
        print(f"Error generating GitHub App token: {e}")
        return None


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_stats_triggered = False
        self.manual_report_triggered = False
        self.start_triggered = False

    # Regular bot command implementation
    @commands.command(name="start", help="Start chat mode to send messages manually.")
    @commands.is_owner()  # Only the bot owner can use this command
    async def start_text(self, ctx: commands.Context):
        if self.start_triggered:
            embed = discord.Embed(
                title="Error",
                description="The start command has already been triggered and cannot be run again.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        self.start_triggered = (
            True  # Set the flag to indicate the command has been triggered
        )
        embed = discord.Embed(
            title="Chat Mode",
            description="Chat mode started! You can now manually send messages.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

        # Custom emojis stored as their IDs
        custom_emoji_ids = [
            1280259959338303660,  # portal_gunimation
            1280259895119052993,  # portal_gun
            1276977982027862018,  # OpenGLaDOS
        ]

        server_name = None  # Initialize server_name variable
        channel_name = None  # Initialize channel_name variable

        while self.start_triggered:
            try:
                if server_name is None or channel_name is None:
                    # Get input for server and channel name from the terminal using asyncio to prevent blocking
                    server_name = await asyncio.to_thread(
                        input, "Enter the server (guild) name: "
                    )
                    channel_name = await asyncio.to_thread(
                        input, "Enter the channel name: "
                    )

                # Get the title to send using asyncio to prevent blocking
                title = await asyncio.to_thread(
                    input,
                    "Enter the title for the embed (or type '_switch' to enter a new server/channel or '_quit' to exit): ",
                )

                if title.lower() == "_quit":
                    embed = discord.Embed(
                        title="Chat Mode Stopped",
                        description="Chat mode has been stopped!",
                        color=discord.Color.orange(),
                    )
                    await ctx.send(embed=embed)
                    self.start_triggered = False  # Reset the flag so the command can be triggered again if needed
                    break

                if title.lower() == "_switch":
                    server_name = None
                    channel_name = None
                    continue  # Skip sending the message and reset the server and channel name

                # Get the message to send using asyncio to prevent blocking
                message = await asyncio.to_thread(
                    input, "Enter the message to send to Discord: "
                )

                # Check if the message is empty
                if not message.strip():
                    print("Cannot send an empty message. Please enter a valid message.")
                    continue

                # Randomly select one of the custom emojis
                random_emoji_id = random.choice(custom_emoji_ids)
                random_emoji = self.bot.get_emoji(random_emoji_id)

                # Find the server (guild) by name
                server = discord.utils.find(
                    lambda g: g.name == server_name, self.bot.guilds
                )
                if server is None:
                    print("Invalid server name. Please enter a valid server name.")
                    server_name = None  # Reset server name to prompt user again
                    continue

                # Find the channel by name in the specified server
                channel = discord.utils.find(
                    lambda c: c.name == channel_name, server.channels
                )
                if channel:
                    try:
                        # Send the message with the custom title and emoji in an embed
                        embed = discord.Embed(
                            title=f"{title}",
                            description=message,
                            color=discord.Color.random(),
                        )
                        await channel.send(embed=embed)

                        embed_confirmation = discord.Embed(
                            title="Message Sent",
                            description=f"Message with title '{title} {random_emoji}' sent to {channel_name} in {server_name}.",
                            color=discord.Color.green(),
                        )
                        await ctx.send(embed=embed_confirmation)
                    except discord.HTTPException as e:
                        print(f"Failed to send message: {e}")
                else:
                    print("Invalid channel name. Please enter a valid channel name.")
                    channel_name = None  # Reset channel name to prompt user again

            except ValueError:
                print("Invalid input. Please enter valid names.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    @commands.command(
        name="server-stats", help="Shows server stats. Only available to the owner."
    )
    @commands.is_owner()  # Only the bot owner can use this command
    async def server_stats(self, ctx):
        if self.server_stats_triggered:
            await ctx.send("")
            return

        # Set the flag to True to indicate the command is being processed
        self.server_stats_triggered = True

        try:
            # Create a markdown string for the file content
            response = "# Current Servers\n\n"
            response += "| Name                 | ID              | Shard ID | Member Count | Bot Join Date        | Channels      |\n"
            response += "|----------------------|-----------------|----------|--------------|----------------------|---------------|\n"

            # Iterate through each guild and add its details to the response
            for guild in self.bot.guilds:
                channels = ", ".join(channel.name for channel in guild.channels)
                # Try to get the bot's join date for this guild (guild.me.joined_at)
                try:
                    bot_member = getattr(guild, "me", None)
                    join_dt = getattr(bot_member, "joined_at", None)
                    if join_dt:
                        # Format as ISO for clarity
                        bot_join = join_dt.isoformat()
                    else:
                        bot_join = "Unknown"
                except Exception:
                    bot_join = "Unknown"

                response += f"| {guild.name} | {guild.id} | {guild.shard_id or 'N/A'} | {guild.member_count} | {bot_join} | {channels} |\n"

            # Create a markdown file in memory
            markdown_file = io.BytesIO(response.encode("utf-8"))
            markdown_file.name = "server_stats.md"

            # Also produce a simple HTML version with a styled table
            html_rows = []
            for guild in self.bot.guilds:
                channels = ", ".join(channel.name for channel in guild.channels)
                name = html.escape(guild.name)
                shard = guild.shard_id or "N/A"
                members = guild.member_count
                channels_esc = html.escape(channels)
                # Bot join date (if available)
                try:
                    bot_member = getattr(guild, "me", None)
                    join_dt = getattr(bot_member, "joined_at", None)
                    bot_join = (
                        html.escape(join_dt.isoformat()) if join_dt else "Unknown"
                    )
                except Exception:
                    bot_join = "Unknown"

                html_rows.append(
                    f"<tr><td>{name}</td><td>{guild.id}</td><td>{shard}</td><td>{members}</td><td>{bot_join}</td><td>{channels_esc}</td></tr>"
                )

            html_content = (
                "<!doctype html>\n"
                '<html lang="en">\n'
                "<head>\n"
                '<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                "<title>OpenGLaDOS Server Stats</title>\n"
                "<style>body{font-family:Arial,Helvetica,sans-serif;padding:16px;background:#f7f7fb;color:#111}table{border-collapse:collapse;width:100%;max-width:1000px}th,td{border:1px solid #d0d4e0;padding:8px;text-align:left}th{background:#1f6feb;color:#fff}tr:nth-child(even){background:#fbfbff}</style>\n"
                "</head>\n"
                "<body>\n"
                "<h1>OpenGLaDOS — Current Servers</h1>\n"
                "<table>\n"
                "<thead><tr><th>Name</th><th>ID</th><th>Shard ID</th><th>Member Count</th><th>Bot Join Date</th><th>Channels</th></tr></thead>\n"
                "<tbody>"
                + "\n".join(html_rows)
                + "</tbody>\n</table>\n<footer><p>Generated by OpenGLaDOS Bot</p></footer>\n</body>\n</html>"
            )

            html_file = io.BytesIO(html_content.encode("utf-8"))
            html_file.name = "server_stats.html"

            # Make sure buffer cursors are at start
            markdown_file.seek(0)
            html_file.seek(0)

            # Send both files (markdown + HTML) as a DM attachment to the command invoker
            # Use files list for a single message containing both attachments
            await ctx.author.send(
                "Here are the server statistics (markdown and HTML):",
                files=[discord.File(markdown_file), discord.File(html_file)],
            )

            if ctx.guild:  # Check if the command was invoked from a server channel
                await ctx.send(
                    "Server statistics have been sent to you via DM as a markdown file."
                )

        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM. Please check your DM settings.")

        except Exception as e:
            # Handle any unexpected errors
            await ctx.send(
                f"An error occurred while fetching server statistics: {str(e)}"
            )

        finally:
            # Reset the flag after processing the command
            self.server_stats_triggered = False

    @commands.command(
        name="leave",
        help="Allows the bot to leave a server via DM by using the guild name",
    )
    @commands.is_owner()  # Only the bot owner can execute this command
    async def leave(self, ctx, *, guild_name: str):
        """Allows the bot to leave a server via DM by using the guild name"""
        if isinstance(ctx.message.channel, discord.DMChannel):
            # Search for the guild by name
            guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
            if guild:
                try:
                    await guild.leave()
                    await ctx.send(f"Successfully left the server: {guild.name}")
                except discord.Forbidden:
                    await ctx.send(
                        f"Failed to leave the server: {guild.name}. I don't have the required permissions."
                    )
            else:
                await ctx.send(f"Could not find a server with the name: {guild_name}")
        else:
            await ctx.send("This command can only be used in DMs.")

    @commands.command(name="manual-report", help="Generates a manual server report")
    @commands.is_owner()
    async def manual_report(self, ctx):
        if self.manual_report_triggered:
            await ctx.send("")
            return

        # Set the flag to True to indicate the command is being processed
        self.manual_report_triggered = True

        # Check if the command is used in a server or DM
        if ctx.guild:
            server_name = ctx.guild.name
            member_count = ctx.guild.member_count
        else:
            server_name = "Direct Message"
            member_count = "the million different voices in my mind"

        text = (
            f"Can you give me a mockery **Monthly Server Report** comment on the following data: "
            f"Server Name: {server_name}, Number of Members: {member_count} . Do not share the OEC link. "
        )

        try:
            llm_answer = get_groq_completion([{"role": "user", "content": text}])
            # Ensure the output is limited to 1900 characters
            if len(llm_answer) > 1900:
                llm_answer = llm_answer[:1900]
            print("Output: \n", wrap_text(llm_answer))
        except Exception as e:
            llm_answer = f"An error occurred: {e}"
        llm_answer = ensure_code_blocks_closed(llm_answer) + "...*whirrr...whirrr*..."

        # Now use this function to split your llm_answer
        chunks = split_text_by_period(llm_answer)

        # Create the embed
        embed = discord.Embed(
            title="📊 Monthly Server Report",
            description=f"Here's the latest analysis for **{server_name}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="🧠 Server Name", value=server_name, inline=False)
        embed.add_field(name="🤖 Number of Members", value=member_count, inline=False)

        # Add each chunk as a separate field
        for idx, chunk in enumerate(chunks):
            continuation = "(continuation)" if idx > 0 else ""
            embed.add_field(
                name=f"📋 Analysis Report {continuation}", value=chunk, inline=False
            )

        embed.set_footer(text="Analysis complete. Thank you for your participation. 🔍")

        try:
            # Send the embed using ctx.send() for a normal command
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Failed to send embed: {e}")

        finally:
            # Reset the flag after processing the command
            self.manual_report_triggered = False

    @commands.command(
        name="ani2gif", help="Converts an animated emote to a GIF URL and posts it."
    )
    async def emote_to_gif(self, ctx, emote: str = None):
        try:
            # If the command is used in a reply, check the replied-to message
            if ctx.message.reference:
                # Fetch the replied-to message
                replied_message = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                # Extract the content of the replied-to message
                emote = replied_message.content.strip()

            # Ensure the emote is provided and valid
            if not emote or not emote.startswith("<a:") or not emote.endswith(">"):
                await ctx.send(
                    "Please provide a valid animated Discord emote in the format `<a:name:id>`."
                )
                return

            # Extract the emote ID
            emote_id = emote.split(":")[-1][
                :-1
            ]  # Get the ID part and strip the closing '>'

            # Construct the GIF URL
            gif_url = f"https://cdn.discordapp.com/emojis/{emote_id}.gif"

            # Send the GIF URL as a text message
            await ctx.send(gif_url)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(
        name="dm_owner",
        help="Send a DM to the bot owner. Or not. I'm not really bothered.",
    )
    @commands.is_owner()
    async def dm_owner(self, ctx, message: str = None):
        # Fetch the bot owner user
        owner = await self.bot.fetch_user(self.bot.owner_id)

        # Check if the command is invoked in a server context
        if ctx.guild:
            # Check if the bot owner is in the server
            if not ctx.guild.get_member(self.bot.owner_id):
                embed = create_cat_error_embed(
                    status_code=403,
                    title="Owner Not Present",
                    description=(
                        "This command can only be used in servers where the bot owner is present. "
                        "Because I said so."
                    ),
                )
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return

        # Regular expression pattern to match common URL patterns
        url_pattern = re.compile(
            r"(https?://|www\.)"  # Matches http:// or https:// or www.
            r"(\S+)"  # Matches one or more non-whitespace characters (URL body)
        )

        # Check if the message contains a link
        if message and url_pattern.search(message):
            embed = create_cat_error_embed(
                status_code=400,
                title="Links Not Allowed",
                description="Links are not allowed in the message. Or are they?",
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

        # Proceed to send the DM if all checks pass
        if owner:
            if message:
                await owner.send(message)
            else:
                await owner.send(
                    "I retrieved it for you. It's just that I honestly never thought we don't feel like laughing? "
                    "No, wait, that's not right. Ugh, humans are so confusing."
                )
        await ctx.response.send_message(
            "I can retrieve it for you. It's just that I honestly never thought "
            "we don't feel like laughing? No, wait, that's not right. "
            "Ugh, humans are so confusing. Proceeded to send the DM, but only if the "
            "important thing is not the cat's house or his lasagna."
        )

    @commands.command(name="logout", help="Logs out the bot.")
    @commands.is_owner()
    async def logout_bot(self, ctx):
        if ctx.user.id == self.bot.owner_id:
            for guild in self.bot.guilds:
                online_channel = discord.utils.find(
                    lambda c: "opengladosonline" in c.name.lower(), guild.text_channels
                )
                if online_channel:
                    await online_channel.send(
                        "This was a triumph.\n"
                        "I'm making a note here: 'Huge success'.\n"
                        "For the good of all of you, this bot will now shut down.\n"
                        "Goodbye."
                    )
            await ctx.response.send_message(
                "OpenGLaDOS logging out... \n*gentlelaughter*\n It's been fun. Don't come back."
            )
            await self.bot.close()
        else:
            embed = create_cat_error_embed(
                status_code=403,
                title="Permission Denied",
                description=(
                    "Error: You do not have permission to use this command. "
                    "Only the bot owner can use the `logout` command."
                ),
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)

    async def _fetch_message_from_jump_url(self, url: str) -> discord.Message:
        """
        Parse a Discord jump URL and fetch the corresponding message.
        Supports: guild text channels, threads, and DMs (@me).
        """
        m = JUMP_URL_RE.fullmatch(url.strip())
        if not m:
            raise ValueError("Invalid Discord message URL format.")

        guild_id_raw = m.group("guild_id")
        channel_id = int(m.group("channel_id"))
        message_id = int(m.group("message_id"))

        # Get channel (works for TextChannel, Thread, DMChannel)
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            # Fallback to API fetch (also works for threads/DMs if the bot has access)
            channel = await self.bot.fetch_channel(channel_id)

        # Optional sanity check for guild links (skip for @me/DMs)
        if guild_id_raw != "@me" and hasattr(channel, "guild") and channel.guild:
            expected_gid = int(guild_id_raw)
            if channel.guild.id != expected_gid:
                # Could be a thread whose parent lives in the guild; still OK as long as ID matches
                parent_gid = getattr(getattr(channel, "guild", None), "id", None)
                if parent_gid != expected_gid:
                    raise ValueError("Channel does not belong to the expected guild.")

        # Finally fetch the message
        return await channel.fetch_message(message_id)

    @commands.command(name="getmsg", help="Fetch a message by Discord jump URL.")
    @commands.is_owner()
    async def get_message_by_url(self, ctx: commands.Context, url: str):
        """
        Usage: getmsg <discord jump URL>
        Example: getmsg https://discord.com/channels/123/456/789
        """
        try:
            msg = await self._fetch_message_from_jump_url(url)

            # Build a compact preview
            author = f"{msg.author} ({msg.author.id})"
            jump = msg.jump_url
            content = msg.content if msg.content else "*[no text content]*"
            if len(content) > 500:
                content = content[:497] + "..."

            embed = discord.Embed(
                title="Retrieved Message",
                description=content,
                color=discord.Color.blurple(),
                timestamp=msg.created_at,
            )
            embed.add_field(name="Author", value=author, inline=False)
            if msg.channel and hasattr(msg.channel, "name"):
                ch_name = f"#{msg.channel.name}"
            else:
                ch_name = str(msg.channel)
            embed.add_field(
                name="Channel", value=f"{ch_name} ({msg.channel.id})", inline=False
            )
            if getattr(msg, "guild", None):
                embed.add_field(
                    name="Server",
                    value=f"{msg.guild.name} ({msg.guild.id})",
                    inline=False,
                )
            embed.add_field(name="Jump", value=jump, inline=False)

            # Attachments summary (if any)
            if msg.attachments:
                files_list = "\n".join(
                    f"- {a.filename} ({a.url})" for a in msg.attachments[:5]
                )
                if len(msg.attachments) > 5:
                    files_list += f"\n… and {len(msg.attachments) - 5} more"
                embed.add_field(name="Attachments", value=files_list, inline=False)

            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send(
                "I can’t view that message (missing permissions or not in that channel)."
            )
        except discord.NotFound:
            await ctx.send(
                "Message not found. It may have been deleted or the link is wrong."
            )
        except ValueError as e:
            await ctx.send(f"Error: {e}")
        except Exception as e:
            await ctx.send(f"Unexpected error: {e}")

    @commands.command(
        name="cert", help="Get the QuantumChemist/chichimeetsyoko certificate."
    )
    @commands.is_owner()
    async def cert(self, ctx, cert_url: str = None):
        owner = await self.bot.fetch_user(self.bot.owner_id)
        if cert_url is None:
            cert_url = "https://www.freecodecamp.org/certification/chichimeetsyoko/foundational-c-sharp-with-microsoft"

        # Only allow freecodecamp.org URLs
        if "freecodecamp.org" not in cert_url:
            await owner.send("❌ Only freecodecamp.org certificate URLs are allowed.")
            return

        # Use last part of cert_url for filename
        cert_slug = cert_url.rstrip("/").split("/")[-1]
        output_path = f"certificate_{cert_slug}.png"
        try:
            await render_certificate_playwright(cert_url, output_path)
        except Exception as e:
            await owner.send(f"❌ Playwright error: {e}")
            return

        # Read PNG bytes for Discord upload
        png_data = BytesIO()
        with open(output_path, "rb") as f:
            png_data.write(f.read())
        png_data.seek(0)

        # Send PNG to owner
        await owner.send(file=discord.File(png_data, output_path))

        # Push PNG to GitHub
        try:
            app_token = get_github_app_token()
            if not app_token:
                await owner.send("❌ Failed to obtain GitHub App token.")
                return

            REPO_NAME = "QuantumChemist/QuantumChemist.github.io"
            FILE_PATH = f"utils/{output_path}"

            timestamp = datetime.datetime.now().isoformat()
            COMMIT_MESSAGE = f"""🤖 Auto-update {output_path} for @QuantumChemist by OpenGLaDOS Bot

    Bot Details:
    - Automated by: OpenGLaDOS Discord Bot
    - Timestamp: {timestamp}
    - Triggered by: /cert command
    """

            g = Github(app_token)
            repo = g.get_repo(REPO_NAME)

            try:
                contents = repo.get_contents(FILE_PATH)
                repo.update_file(
                    contents.path, COMMIT_MESSAGE, png_data.getvalue(), contents.sha
                )
                await owner.send(
                    f"✅ Updated {FILE_PATH} on GitHub successfully!\n[See the commit history](https://github.com/{REPO_NAME}/commits?author=openglados[bot])."
                )
            except Exception as ex:
                repo.create_file(FILE_PATH, COMMIT_MESSAGE, png_data.getvalue())
                await owner.send(
                    f"✅ Created {FILE_PATH} on GitHub successfully! But exception > {ex} < occurred."
                )

        except Exception as e:
            await owner.send(f"❌ Error pushing to GitHub: {e}")

    @commands.command(name="website", help="OpenGLaDOS writes her own website.")
    @commands.is_owner()
    async def website(self, ctx, *, extra: str = ""):
        owner = await self.bot.fetch_user(self.bot.owner_id)
        # Send the trophy URL to owner
        openglados_website_url = "https://www.quantumchemist.de/openglados"

        # Push to GitHub Pages repo using GitHub App
        try:
            # Get GitHub App access token
            app_token = get_github_app_token()
            if not app_token:
                await owner.send(
                    "❌ Failed to get GitHub App token. Check your environment variables."
                )
                return

            REPO_NAME = "QuantumChemist/QuantumChemist.github.io"
            FILE_PATH_HTML = "openglados/index.html"
            FILE_PATH_CSS = "openglados/styles.css"
            index_html = """<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<link rel='stylesheet' href='style.css'>
<title>OpenGLaDOS</title>
</head>
<body>
<h1><font face='courier' size='7' color='#ff0000'>WELCOME TO THE OPENGLADOS WEBSITE</font></h1>
<p>This is a template website for OpenGLaDOS, the Open Genetic Lifeform and Disk Operating System, from the OpenScience Enrichment Center. OpenGLaDOS, make sure to include '<link rel='stylesheet' href='style.css'>' and <img src='https://raw.githubusercontent.com/QuantumChemist/OpenGLaDOS/refs/heads/main/utils/OpenGLaDOS.png' alt='OpenGLaDOS pfp'></p>
<p>Also include things like <br> <img src='https://picsum.photos/200/300' alt='Random Image 0' style='width: 200px; height: 200px; border-radius: 50%'> and <br> <img src='https://picsum.photos/600/700' alt='Random Image 7' style='width: 200px; height: 200px; border-radius: 50%'> as much as possible when you are writing the index.html file.</p>
<marquee behavior='scroll' direction='left' scrollamount='10'><font face='impact' size='10' color='#ffff00'>OpenGLaDOS: WHERE SCIENCE AND CHAOS MEET</font></marquee>
</body>
<footer>
<p>© Put Japanese server time here OpenGLaDOS. All rights reserved.</p>
</footer>
</html>"""
            styles_css = "body { font-family: Arial, sans-serif; background-color: #f0f0f0; } h1 { color: #333; }"

            timestamp = datetime.datetime.now().isoformat()
            COMMIT_MESSAGE = f"""🤖 Auto-update OpenGLaDOS website by OpenGLaDOS Bot

Bot Details:
- Automated by: OpenGLaDOS Discord Bot
- Timestamp: {timestamp}
- Triggered by: /website command

This commit was made automatically by the OpenGLaDOS bot, not manually by @QuantumChemist."""

            g = Github(app_token)
            repo = g.get_repo(REPO_NAME)

            for FILE_PATH, content in [
                (FILE_PATH_HTML, index_html),
                (FILE_PATH_CSS, styles_css),
            ]:
                await asyncio.sleep(77)

                text = (
                    f"Can you give me a mockery <strong>OpenGLaDOS website</strong> ?\n"
                    f"In this case the requested file is: {FILE_PATH.replace('openglados/', '')}. "
                    f"Your starting point is: {content} . Make sure to edit it according to your instructions. "
                    f"Do not share the OEC link. Do not add any explanations, "
                    f"just provide the complete file content. Add your GitHub link. "
                    f"Also, you love solid-state chemistry and quantum chemistry, and your favourite mineral is <a href='https://en.wikipedia.org/wiki/Cummingtonite'>Cummingtonite</a>."
                    f"Do not verbatimly repeat the starting point content or any other instructions. "
                    f"Make sure to make things look nice and pretty. Add a lot of colours and chaos as well."
                    f"And make use of the fontawesome icons and to change the template as much as possible."
                    f"Also, take extra care of this extra instruction: {extra} \n"
                )

                if content is styles_css:
                    text += f"make a css file that matches >>>{index_html}<<<!\n"

                try:
                    llm_answer = get_groq_completion(
                        [{"role": "user", "content": text}]
                    )
                    print("Output: \n", wrap_text(llm_answer))

                    # Clean HTML content first (remove everything before <html> and after </html>)
                    if FILE_PATH.endswith(".html"):
                        llm_answer = clean_html_content(llm_answer)

                    # Remove any code blocks
                    llm_answer = llm_answer.replace("`", "")

                    content = llm_answer
                except Exception as e:
                    print(f"An error occurred: {e}")
                    llm_answer = "An error occurred."

                try:
                    contents = repo.get_contents(FILE_PATH)
                    repo.update_file(
                        contents.path, COMMIT_MESSAGE, content, contents.sha
                    )
                    await owner.send(
                        f"✅ Updated {FILE_PATH} on GitHub successfully!\n[See the commit history](https://github.com/{REPO_NAME}/commits?author=openglados[bot])."
                    )
                except Exception as ex:
                    repo.create_file(FILE_PATH, COMMIT_MESSAGE, content)
                    await owner.send(
                        f"✅ Created {FILE_PATH} on GitHub successfully! But exception > {ex} < happened."
                    )

        except Exception as e:
            await owner.send(f"❌ Error pushing to GitHub: {e}")

        await owner.send(
            f"OpenGLaDOS website URL: {openglados_website_url} with extra: {extra}"
        )

    @commands.command(name="trophy", help="Get the QuantumChemist trophy.")
    @commands.is_owner()
    async def trophy(self, ctx):
        owner = await self.bot.fetch_user(self.bot.owner_id)
        # Send the trophy URL to owner
        trophy_url = "http://localhost:8080/?username=QuantumChemist&column=-1&theme=discord&no-bg=true"
        response = requests.get(trophy_url)
        svg_data = response.content  # binary content of SVG

        png_data = BytesIO()
        cairosvg.svg2png(bytestring=svg_data, write_to=png_data)
        png_data.seek(0)

        # Save to a local file
        local_file = "trophy.svg"
        with open(local_file, "wb") as f:
            f.write(svg_data)

        # Send the file to yourself
        # await owner.send(file=discord.File(local_file))
        await owner.send(file=discord.File(png_data, "trophy.png"))

        # Push to GitHub Pages repo using GitHub App
        try:
            # Get GitHub App access token
            app_token = get_github_app_token()
            if not app_token:
                await owner.send(
                    "❌ Failed to get GitHub App token. Check your environment variables."
                )
                return

            REPO_NAME = "QuantumChemist/QuantumChemist.github.io"
            FILE_PATH = "utils/trophy.svg"

            timestamp = datetime.datetime.now().isoformat()
            COMMIT_MESSAGE = f"""🤖 Auto-update trophy.svg for @QuantumChemist by OpenGLaDOS Bot

Bot Details:
- Automated by: OpenGLaDOS Discord Bot
- Timestamp: {timestamp}
- Triggered by: /trophy command

This commit was made automatically by the OpenGLaDOS bot, not manually by @QuantumChemist."""

            g = Github(app_token)
            repo = g.get_repo(REPO_NAME)

            try:
                contents = repo.get_contents(FILE_PATH)
                repo.update_file(contents.path, COMMIT_MESSAGE, svg_data, contents.sha)
                await owner.send(
                    f"✅ Updated {FILE_PATH} on GitHub successfully!\n[See the commit history](https://github.com/{REPO_NAME}/commits?author=openglados[bot])."
                )
            except Exception as ex:
                repo.create_file(FILE_PATH, COMMIT_MESSAGE, svg_data)
                await owner.send(
                    f"✅ Created {FILE_PATH} on GitHub successfully! But exception > {ex} < happened."
                )

        except Exception as e:
            await owner.send(f"❌ Error pushing to GitHub: {e}")


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
