import discord
from discord.ext import commands
from discord.ui import Button, View
import json
from dotenv import load_dotenv
import os
import aiohttp

# Load environment variables from .env file
load_dotenv()

# Retrieve the bot token and channel ID from the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNELID = int(os.getenv('CHANNELID'))
# Define your API endpoint
API_URL=os.getenv('API_URL')

# Initialize the bot with the required intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

# Initialize bot with command prefix
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

    # Send the main menu options directly in the channel when the bot is ready
    channel = bot.get_channel(CHANNELID)
    if channel:
        await send_menu(channel, 'menu')

async def send_menu(channel, choice):
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={'choice': choice}) as response:
            if response.status == 200:
                data = await response.json()
                if 'question' in data:
                    questions_text = "\n".join([f"{idx + 1}. {opt}" for idx, opt in enumerate(data['options'])])
                    embed = discord.Embed(title=data['question'], description=questions_text, color=discord.Color.blue())
                    view = View()
                    for idx, option in enumerate(data['options']):
                        view.add_item(OptionButton(label=str(idx + 1), custom_id=option, session=session))
                    if choice != 'menu':
                        view.add_item(BackToMenuButton(session=session))
                    await channel.send(embed=embed, view=view)
                elif 'answer' in data:
                    await channel.send(data['answer'])
            else:
                await channel.send("Failed to retrieve data from API.")

async def show_menu(interaction, menu_key):
    await interaction.response.defer()
    await send_menu(interaction.channel, menu_key)

class OptionButton(Button):
    def __init__(self, label, custom_id, session):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
        self.session = session

    async def callback(self, interaction: discord.Interaction):
        await show_menu(interaction, self.custom_id)

class BackToMenuButton(Button):
    def __init__(self, session):
        super().__init__(label="Back to Main Menu", style=discord.ButtonStyle.danger)
        self.session = session
    
    async def callback(self, interaction: discord.Interaction):
        await show_menu(interaction, "menu")

# Run the bot with your token
bot.run(DISCORD_TOKEN)
