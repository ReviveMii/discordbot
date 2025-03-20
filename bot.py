import discord
from discord.ext import commands
from discord.ext.commands import DefaultHelpCommand
import aiohttp
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, description="Developed by TheErrorExe", help_command=DefaultHelpCommand())

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.tree.sync()

@bot.event
async def on_guild_join(guild):
    if guild.id != 1302694379299016764:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(
                        "This bot can only be in 'ReviveMii Trusted Servers'. "
                        "Please ensure you're in a trusted server. Leaving this server now..."
                    )
                    print(f"Sent leave message to {guild.name} before leaving.")
                    break
                except discord.Forbidden:
                    print(f"Bot doesn't have permission to send messages in {channel.name} of {guild.name}")
        
        await guild.leave()
        print(f"Left the server: {guild.name} (ID: {guild.id})")

async def fetch_errors():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://theerrorexe.dev/errors.json') as response:
            return await response.json()

def search_errors(errors, query):
    results = []
    query_regex = re.compile('^' + query.replace("X", "\\d").replace("y", "\\d") + '$', re.IGNORECASE)
    numeric_query = int(query)

    for code, description in errors.items():
        range_match = re.match(r'^(\d+)-(\d+)$', code)
        if range_match:
            start, end = map(int, range_match.groups())
            if start <= numeric_query <= end:
                results.append(f'{code}: {description}')
        else:
            if query_regex.match(code):
                results.append(f'{code}: {description}')
            pattern = code.replace('X', '[0-9]').replace('y', '[0-9]')
            special_regex = re.compile('^' + pattern + '$', re.IGNORECASE)
            if special_regex.match(query):
                results.append(f'{code}: {description}')
            if len(code) == len(query) and 'X' in code:
                prefix = code[:-4]
                if query.startswith(prefix):
                    results.append(f'{code}: {description}')
    return results

@bot.tree.command(name="error", description="Fetch Wii Error Codes")
async def error(interaction: discord.Interaction, query: str):
    errors = await fetch_errors()
    results = search_errors(errors, query)
    if results:
        await interaction.response.send_message('\n'.join(results))
    else:
        await interaction.response.send_message('No Error Codes found.')

@bot.tree.command(name="about", description="Shows Information about the bot.")
async def about(interaction: discord.Interaction):
    await interaction.response.send_message('This bot was developed by TheErrorExe. Source Code: https://github.com/ReviveMii/discordbot')

@bot.tree.command(name="website", description="Shows the Website of the Developer.")
async def website(interaction: discord.Interaction):
    await interaction.response.send_message('ReviveMii: https://revivemii.fr.to\nTheErrorExe-Homepage: https://theerrorexe.github.io\nTools: https://theerrorexe-tools.github.io')

@bot.tree.command(name="ping", description="Ping Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong!')

@bot.tree.command(name="status", description="Check the operational status of the website.")
async def status(interaction: discord.Interaction):
    status_msg = await interaction.response.send_message(
        "Website : Checking...\n"
        "More Information at https://revivemii.xyz/status/"
    )

    async def check_website(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status in [200, 301]:
                        return "Operational"
                    else:
                        return "Server Down"
        except Exception:
            return "Server Down"

    https_status = await check_website("https://revivemii.xyz")

    await status_msg.edit(
        content=(
            f"Website : {'Operational' if https_status == 'Operational' else 'Server Down'}\n"
            "More Information at https://revivemii.xyz/status/"
        )
    )

with open('token.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
