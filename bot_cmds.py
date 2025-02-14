import io
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random
from utils import (
    get_groq_completion,
    wrap_text,
    ensure_code_blocks_closed,
    split_text_by_period,
)

# Load environment variables from .env file
load_dotenv()


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
            response += "| Name                 | ID              | Shard ID | Member Count | Channels      |\n"
            response += "|----------------------|-----------------|----------|--------------|---------------|\n"

            # Iterate through each guild and add its details to the response
            for guild in self.bot.guilds:
                channels = ", ".join(channel.name for channel in guild.channels)
                response += f"| {guild.name} | {guild.id} | {guild.shard_id or 'N/A'} | {guild.member_count} | {channels} |\n"

            # Create a markdown file in memory
            markdown_file = io.BytesIO(response.encode("utf-8"))
            markdown_file.name = "server_stats.md"

            # Send the markdown file as an attachment to the command invoker
            await ctx.author.send(
                "Here are the server statistics:", file=discord.File(markdown_file)
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
                await ctx.response.send_message(
                    "This command can only be used in servers where the bot owner is present. Because I said so. \n"
                    "https://http.cat/status/400",
                    ephemeral=True,
                )
                return

        # Regular expression pattern to match common URL patterns
        url_pattern = re.compile(
            r"(https?://|www\.)"  # Matches http:// or https:// or www.
            r"(\S+)"  # Matches one or more non-whitespace characters (URL body)
        )

        # Check if the message contains a link
        if message and url_pattern.search(message):
            await ctx.response.send_message(
                "Links are not allowed in the message. Or are they? \n"
                "https://http.cat/status/400",
                ephemeral=True,
            )
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
            await ctx.response.send_message(
                "Error: You do not have permission to use this command. "
                "Only the bot owner can use the `logout` command. \n"
                "https://http.cat/status/400",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
