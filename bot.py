import os
import sys
import json
from twitchio.ext import commands
from twitchio.ext.commands.errors import CommandNotFound, CommandError
from twitchio.dataclasses import Channel
from twitchio.client import Client
import random
from phue import Bridge
from rgbxy import Converter
import webcolors
import asyncio
import time
import math

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

async def sub_colors():
    colors = [
        {'on': True, 'bri': 254, 'xy': converter.hex_to_xy('ff0000')},
        {'on': True, 'bri': 254, 'xy': converter.hex_to_xy('0000ff')},
        {'on': True, 'bri': 254, 'xy': converter.hex_to_xy('00ff00')},
        {'on': True, 'bri': 254, 'xy': converter.hex_to_xy('ffff00')}
    ]
    colors = colors * 4
    for color in colors:
        bridge.set_group(2, color)
        await asyncio.sleep(.5)

    bridge.set_group(2, {'on': True, 'bri': 254, 'xy': converter.hex_to_xy('ffffff')})


class myChannel(Channel):

    def __init__(self):
        super().__init__(
            name = os.environ.get('CHANNEL'),
            ws = bot._ws,
            http = 'https://www.twitch.tv/itzchauncey'
        )


class myClient(Client):
    def __init__(self):
        super().__init__(
            loop = None,
            client_id = os.environ.get('CLIENT_ID')
        )

    # async def get_chatters(self, channel=os.environ.get('CHANNEL')):

class ChaunceyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            irc_token = os.environ.get('TMI_TOKEN'),
            client_id = os.environ.get('CLIENT_ID'),
            nick = os.environ.get('BOT_NICK'),
            prefix = os.environ.get('BOT_PREFIX'),
            initial_channels = [os.environ.get('CHANNEL')]
            )

    ### BOT SETUP ###
    # Advanced commands for command recognition
    advanced_commands = ['!chaunceybot', '!braincells', '!coinflip', '!watchtime']

    # List of users that were already welcomed per stream
    welcomed = []

    # Load commands from json file
    with open('simple_commands.json') as json_file:
        simple_commands = json.load(json_file)
    print('Commands Loaded')

    ### COROUTINES ###
    async def send_message(self, text):
        ws = self._ws
        await ws.send_privmsg(os.environ.get('CHANNEL'), text)


    async def event_ready(self):
        'Called once the bot goes online'
        print(f"{os.environ.get('BOT_NICK')} is online")
        await self.add_watchtime()
                    

    async def add_watchtime(self):
        'Adds 1 minute to each user in channel every 1 minute to watchtime.json'
        while True:
            await asyncio.sleep(60)
            chatters = await myClient.get_chatters(self, os.environ.get('CHANNEL'))
            
            with open('watchtime.json') as json_file:
                data = json.load(json_file)

            for user in chatters[1]:
                if user in data['users']:
                    data['users'][user] += 1
                else:
                    data['users'][user] = 0
            
            with open('watchtime.json', 'w') as json_file:
                json.dump(data, json_file, indent=4)
        

    async def add_points(self):
        'Adds 10 points to each user in channel every 5 minute to watchtime.json'
        while True:
            await asyncio.sleep(10)
            chatters = await myClient.get_chatters(self, os.environ.get('CHANNEL'))
            
            with open('points.json') as json_file:
                data = json.load(json_file)

            for user in chatters[1]:
                if user in data['users']:
                    data['users'][user] += 10
                else:
                    data['users'][user] = 0
            
            with open('watchtime.json', 'w') as json_file:
                json.dump(data, json_file, indent=4)


    async def event_message(self, ctx):
        'Runs every time a message is sent in chat'
        
        
        if ctx.author.name.lower() == os.environ.get('BOT_NICK').lower():
            return

        if 'custom-reward-id' in ctx.tags.keys():
            if ctx.tags['custom-reward-id'] == 'c97a0082-1237-4971-a05a-385189b1fa08':
                change_light_color(ctx.content)

        if ctx.content[0] == '!':
            message = ctx.content.lower().split()
            command = message[0].strip('!')
            if message[0] not in self.advanced_commands:
                if command in self.simple_commands.keys():
                    await self.send_message(self.simple_commands[command])
                else:
                    await self.send_message(f'@{ctx.author.name} --> Command "{command}" not recognized.')
            else:
                await self.handle_commands(ctx)
        

    async def event_join(self, user):

        text = f'Welcome to the channel @{user.name}, I am Chauncey\'s Personal Bot!'

        if user.name.lower().strip() in self.welcomed:
            return
        else:
            self.welcomed.append(user.name.lower().strip())

        await self.send_message(text)


    async def event_usernotice_subscription(self, data):
        await sub_colors()
        await self.send_message(f'Thank you {data.user.name} for subscribing!')


    async def event_command_error(self, context, error):
        await context.send(error)


    ### ADVANCED COMMANDS ###
    @commands.command(name='chaunceybot')
    async def edit_commands(self, ctx):
        # Grab command message and split into list
        command_msg = ctx.content.split()
        command_type = command_msg[1].lower()
        command_name = command_msg[2].lower().strip('!')
        command_content = ' '.join(command_msg[3:])

        # Check if person creating command is a moderator
        if ctx.author.is_mod != True:
            await ctx.send(f'@{ctx.author} --> You don\'t have permission')
            return

        # Adding a command
        if command_type == 'add':
            
            # Check if command exists
            if command_name in self.simple_commands.keys():
                await ctx.send(f"@{ctx.author.name} --> That command already exists")
                return

            # Add the command to the simple_commands dict
            self.simple_commands[command_name] = command_content
            
            # Verify creation of command
            await ctx.send(f'@{ctx.author.name} --> The {command_name} command has been created!')

        # Deleting Commands
        if command_type[:3] == 'del':

            # Check if command exists
            if command_name not in self.simple_commands.keys():
                await ctx.send(f"@{ctx.author.name} --> There is no command with the name {command_name}")
                return
            
            # Delete the command
            del self.simple_commands[command_name]
            
            # Verify deletion of command
            await ctx.send(f'@{ctx.author.name} --> The {command_name} command has been deleted!')


        # Editing Commands
        if command_type == 'edit':
            
            # Check if command exits
            if command_name in self.simple_commands.keys():
                self.simple_commands[command_name] = command_content
                await ctx.send(f"@{ctx.author.name} -->  '{command_name}' updated")
                return
            else:
                await ctx.send(f"@{ctx.author.name} --> There is no command with the name {command_name}")
            
            # Change command value
            self.simple_commands[command_name] = command_content


        # Update the json
        with open('simple_commands.json', 'w') as json_file:
            json.dump(self.simple_commands, json_file)


    @commands.command(name='coinflip')
    async def coinflip(self, ctx):
        await ctx.send(f"@{ctx.author.name} {'Heads' if random.randint(1, 2) == 1 else 'Tails'}")


    @commands.command(name='braincells')
    async def braincells(self, ctx):
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


    @commands.command(name='watchtime')
    async def watchtime(self, ctx):
        w_command = ctx.content.split()
        if len(w_command) == 1:
            user = ctx.author.name
        elif w_command[1][0] == '@':
            user = w_command[1][1:].lower()
            
        with open('watchtime.json') as json_file:
            data = json.load(json_file)

        user_watchtime = data['users'][user]

        days_raw = user_watchtime / 1440
        days = math.floor(days_raw)

        hours_raw = (days_raw - days) * 24
        hours = math.floor(hours_raw)

        minutes_raw = (hours_raw - hours) * 60
        minutes = round(minutes_raw)

        if days >= 1:
            await ctx.send(f'@{user} has spent {days} days {hours} hours {minutes} minutes watching ItzChauncey')
        elif hours >= 1:
            await ctx.send(f'@{user} has spent {hours} hours {minutes} minutes watching ItzChauncey')
        elif minutes >= 1:
            await ctx.send(f'@{user} has spent {minutes} minutes watching ItzChauncey')
        else:
            await ctx.send(f'@{user} watchtime not found REEEEEE')


    @commands.command(name='points')
    async def points(self, ctx):
        w_command = ctx.content.split()
        if len(w_command) == 1:
            user = ctx.author.name
        elif w_command[1][0] == '@':
            user = w_command[1][1:].lower()
            
        with open('points.json') as json_file:
            data = json.load(json_file)

        user_points = data['users'][user]


bot = ChaunceyBot()
bot.run()