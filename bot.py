import os
import sys
from twitchio.ext import commands
from twitchio.dataclasses import Channel
import random
from phue import Bridge
from rgbxy import Converter
import webcolors
import asyncio

bridge = Bridge(os.environ.get('BRIDGE_IP'))
bridge.connect()
converter = Converter()

def restart():
    import sys
    print("argv was",sys.argv)
    print("sys.executable was", sys.executable)
    print("restart now")

    import os
    os.execv(sys.executable, ['python'] + sys.argv)

def change_light_color(color):
    try:
        color_choice = webcolors.name_to_hex(color)
    except:
        color_choice = webcolors.name_to_hex('yellow')

    settings = {'transitiontime': 1, 'on': True, 'bri': 254, 'xy': converter.hex_to_xy(color_choice.strip('#'))}
    bridge.set_group(2, settings)

# Bot credentials
bot = commands.Bot(
    irc_token = os.environ.get('TMI_TOKEN'),
    client_id = os.environ.get('CLIENT_ID'),
    nick = os.environ.get('BOT_NICK'),
    prefix = os.environ.get('BOT_PREFIX'),
    initial_channels = [os.environ.get('CHANNEL')]
)

channel = Channel(os.environ.get('CHANNEL'), bot._ws, 'https://www.twitch.tv/itzchauncey')

@bot.event
async def event_ready():
    'Called once the bot goes online'
    print(f"{os.environ.get('BOT_NICK')} is online")

@bot.event
async def event_message(ctx):
    'Runs every time a message is sent in chat'
    
    if ctx.author.name.lower() == os.environ.get('BOT_NICK').lower():
        return

    if 'custom-reward-id' in ctx.tags.keys():
        if ctx.tags['custom-reward-id'] == 'c97a0082-1237-4971-a05a-385189b1fa08':
            change_light_color(ctx.content)

    await bot.handle_commands(ctx)

@bot.event
async def event_join(user):
    print(dir(user))
    print(user._mod)
    text = f'Welcome to the channel @{user.name}, I am Chauncey\'s Personal Bot!'

    bots = ['chaunceybot', 'tressino', 'streamelements', 'commanderroot',
    'aten', 'nightbot', 'itzchauncey', 'feet', 'anotherttvviewer']
    if user.name.lower().strip() in bots:
        return

    await channel.send(text)

@bot.command(name='chaunceybot')
async def commands_command(ctx):
    # Grab command message and split into list
    command_msg = ctx.content.split()
    content = []

    # Check if person creating command is a moderator
    if ctx.author.is_mod != True:
        await ctx.send(f'@{ctx.author} --> You don\'t have permission')
        return


    # Adding a command
    if command_msg[1].lower() == 'add':

        # Take current file and "save" it
        with open('bot.py', 'r') as f:
            for line in f:
                content.append(line)

        command_exists = [i for i, x in enumerate(content) if x == f"@bot.command(name='{command_msg[2].lower().strip('!')}')\n"]

        if command_exists:
            await ctx.send(f'@{ctx.author.name} --> \"{command_msg[2].lower()}\" command already exists')
            return

        # Insert command into file
        content.insert(-3, f"@bot.command(name='{command_msg[2].lower().strip('!')}')\n")
        content.insert(-3, f"async def {command_msg[2].lower().strip('!')}(ctx):\n")
        content.insert(-3, f"    await ctx.send('{' '.join(command_msg[3:])}')\n")
        content.insert(-3, "\n")

        # Save the new file with the new command
        with open('bot.py', 'w') as f:
            for i in range(len(content)):
                f.write(content[i])

        # Send confirmation message
        await ctx.send(f'@{ctx.author.name} --> \"{command_msg[2].lower()}\" command successfully created')
        # Restart the bot with updated command
        restart()
    

    # Deleting Commands
    if command_msg[1][:3].lower() == 'del':

        # Take current file and "save" it
        with open('bot.py', 'r') as f:
            for line in f:
                content.append(line)

        # Find where the command is within the file
        start_delete = [i for i, x in enumerate(content) if x == f"@bot.command(name='{command_msg[2].lower().strip('!')}')\n"]

        # if command found, delete, else, dont attempt and tell user
        if start_delete:
            # Delete that code
            del content[start_delete[0]:start_delete[0]+4]

            # Overwrite file without the command
            with open('bot.py', 'w') as f:
                for i in range(len(content)):
                    f.write(content[i])

            await ctx.send(f'@{ctx.author.name} --> \"{command_msg[2].lower()}\" command successfully deleted')
            # Restart bot without the command
            restart()
        else:
            await ctx.send(f'\"{command_msg[2].lower()}\" command not found')

    else:
        await ctx.send(f'@{ctx.author.name} --> Command not recognized try !commands add/delete')


#### COMMANDS ####

@bot.command(name='restart')
async def bot_restart(ctx):
    if ctx.author.is_mod == True:
        await ctx.send(f'@{ctx.author.name} --> ChaunceyBot has restarted!')
        restart()
    else:
        await ctx.send(f'@{ctx.author.name} --> You do not have permission to use this command.')

@bot.command(name='coinflip')
async def coinflip(ctx):
    await ctx.send(f"@{ctx.author.name} {'Heads' if random.randint(1, 2) == 1 else 'Tails'}")

@bot.command(name='braincells')
async def testing982(ctx):
    bc = random.randint(0, 100001)
    if len(ctx.content.split()) > 1:
        if ctx.content.split()[1][0] == '@':
            if ctx.content.split()[1].strip('@').lower() == 'itzchauncey':
                bc = 1000000
            await ctx.send(f'{ctx.content.split()[1]} has {bc} braincells!')
    else:
        if ctx.author.name.lower() == 'itzchauncey':
            bc = 1000000

        await ctx.send(f'@{ctx.author.name} has {bc} braincells!')

@bot.command(name='riot')
async def riot(ctx):
    await ctx.send('itzchauncey#ttv')

@bot.command(name='twitter')
async def twitter(ctx):
    await ctx.send('ItzChaunceyBoi on Twitter!')

@bot.command(name='chance')
async def chance(ctx):
    await ctx.send('cool guy')

@bot.command(name='rank')
async def rank(ctx):
    await ctx.send('Plat 3')


if __name__ == '__main__':
    bot.run()