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

async def fetch_errors():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://theerrorexe.github.io/errors.json') as response:
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

@bot.command(help="!error : Wii Error Codes. How to use: !error InsertErrorCodeHere")
async def error(ctx, *, query: str):
    errors = await fetch_errors()
    results = search_errors(errors, query)
    if results:
        await ctx.send('\n'.join(results))
    else:
        await ctx.send('No Error Codes found.')

@bot.command(help="!about : Shows Information about the bot.")
async def about(ctx):
    await ctx.send('This bot was developed by TheErrorExe. Source Code: https://github.com/ReviveMii/discordbot')

@bot.command(help="!website : Shows the Website of the Developer.")
async def website(ctx):
    await ctx.send('ReviveMii: https://revivemii.fr.to\nTheErrorExe-Homepage: https://theerrorexe.github.io\nTools: https://theerrorexe-tools.github.io')

@bot.command(help="!ping : Ping Pong!")
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(help="!status : Check the operational status of the website.")
async def status(ctx):
    # Initial status message
    status_msg = await ctx.send(
        "Website : Checking...\n"
        "More Information at https://revivemii.fr.to/status/"
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
    
    https_status = await check_website("https://revivemii.fr.to")
     
    # Update the status message with the results
    await status_msg.edit(
        content=(
            f"Website : {'Operational' if https_status == 'Operational' else 'Server Down'}\n"
            "More Information at https://revivemii.fr.to/status/"
        )
    )

# Read the token from token.txt
with open('token.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)