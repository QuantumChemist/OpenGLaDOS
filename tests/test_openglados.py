import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import bot
import utils
import bot_cmds
import discord

@pytest.fixture
def mock_ctx() -> MagicMock:
    mock = MagicMock()
    mock.send = AsyncMock()
    mock.author.send = AsyncMock()
    mock.guild = MagicMock()  # Mock guild attribute
    mock.channel = MagicMock()  # Mock channel attribute
    return mock

@pytest.mark.asyncio
async def test_start_text(mock_ctx):
    bot_instance = bot_cmds.BotCommands(MagicMock())
    bot_instance.start_triggered = False
    await bot_instance.start_text(mock_ctx)
    assert bot_instance.start_triggered
    mock_ctx.send.assert_awaited()

@pytest.mark.asyncio
async def test_server_stats(mock_ctx):
    bot_instance = bot_cmds.BotCommands(MagicMock())
    bot_instance.server_stats_triggered = False
    bot_instance.bot.guilds = [MagicMock()]  # Mocked guilds
    await bot_instance.server_stats(mock_ctx)
    mock_ctx.author.send.assert_awaited()

class TestOpenGLaDOSBot(unittest.IsolatedAsyncioTestCase):
    async def test_on_guild_join(self):
        guild_mock = MagicMock()
        guild_mock.system_channel.permissions_for.return_value.send_messages = True
        guild_mock.system_channel.send = AsyncMock()

        bot_instance = bot.OpenGLaDOSBot(command_prefix='!', intents=discord.Intents.all())
        await bot_instance.on_guild_join(guild_mock)
        guild_mock.system_channel.send.assert_awaited()

class TestUtils(unittest.TestCase):
    def test_wrap_text(self):
        text = "This is a sample text that needs to be wrapped."
        wrapped_text = utils.wrap_text(text, width=10)
        self.assertTrue('\n' in wrapped_text)  # Ensure the text is wrapped

    @patch('requests.get')
    def test_fetch_random_fact(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'text': 'Random Fact'}
        mock_get.return_value = mock_response

        fact = utils.fetch_random_fact()
        self.assertEqual(fact, 'Random Fact')

if __name__ == '__main__':
    unittest.main()