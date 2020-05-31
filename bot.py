import os
import sys
import json
import random
import time
import math
import asyncio
import db

from twitchio.ext import commands
from twitchio.ext.commands.errors import CommandNotFound, CommandError
from twitchio.dataclasses import Channel
from twitchio.client import Client


class ChaunceyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            irc_token = os.environ.get('IRC_TOKEN'),
            client_id = os.environ.get('CLIENT_ID'),
            nick = os.environ.get('BOT_NICK'),
            prefix = os.environ.get('BOT_PREFIX'),
            initial_channels = [os.environ.get('CHANNEL')],
            api_token = os.environ.get('API_TOKEN'),
            scopes = [
                'analytics:read:extensions',
                'analytics:read:games',
                'bits:read',
                'channel:edit:commercial',
                'channel:read:subscriptions',
                'clips:edit',
                'user:edit',
                'user:edit:broadcast',
                'user:edit:follows',
                'user:read:broadcast',
                'user:read:email'
            ]
        )


    ### COROUTINES/TASKS ###
    async def send_message(self, text):
        ws = self._ws
        await ws.send_privmsg(os.environ.get('CHANNEL'), text)


    async def event_ready(self):
        'Called once the bot goes online'
        print(f"{os.environ.get('BOT_NICK')} is online")
        self.loop.create_task(self.add_watchtime())
        self.loop.create_task(self.add_points())


    async def add_watchtime(self):
        'Adds 1 minute to each user in channel every 1 minute to watchtime table'
        print('Started watchtime counter')
        while True:
            await asyncio.sleep(60)
            chatters = await self.get_chatters(os.environ.get('CHANNEL'))
            
            if await self.get_stream('itzchauncey'):
                for user in chatters[1]:
                    if db.check_user(user, 'watchtime'):
                        db.update_user(user, 'watchtime', 1)
                    else:
                        db.add_user(user, 'watchtime')
        

    async def add_points(self):
        'Adds 10 points to each user in channel every 5 minute to points table'
        print('Started point counter')
        while True:
            await asyncio.sleep(300)
            chatters = await self.get_chatters(os.environ.get('CHANNEL'))

            if await self.get_stream('itzchauncey'):
                for user in chatters[1]:
                    if db.check_user(user, 'points'):
                        db.update_user(user, 'points', 10)
                    else:
                        db.add_user(user, 'points')


    async def event_message(self, ctx):
        'Runs every time a message is sent in chat'
        # advance commands list
        advanced_commands = ['!chaunceybot', '!braincells', '!coinflip', '!watchtime', '!points']
        
        if ctx.author.name.lower() == os.environ.get('BOT_NICK').lower():
            return

        if ctx.content[0] == '!':
            message = ctx.content.lower().split()
            command = message[0].strip('!')
            if message[0] not in advanced_commands:
                if command in db.get_all_commands():
                    await self.send_message(db.get_command(command))
                else:
                    await self.send_message(f'@{ctx.author.name} --> Command "{command}" not recognized.')
            else:
                await self.handle_commands(ctx)
        

    async def event_join(self, user):

        text = f'Welcome to the channel @{user.name}, I am Chauncey\'s Personal Bot!'

        if user.name.lower().strip() in db.get_users():
            return

        await self.send_message(text)


    async def event_usernotice_subscription(self, data):
        # await sub_colors()
        await self.send_message(f'Thank you {data.user.name} for subscribing!')


    async def event_command_error(self, context, error):
        await context.send(error)


    ### ADVANCED COMMANDS ###
    @commands.command(name='chaunceybot')
    async def edit_commands(self, ctx):
        # Grab command message and split into list
        command_msg = ctx.content.split()
        if len(command_msg) < 2:
            await ctx.send(f"@{ctx.author.name} --> try using add/edit/delete (!chaunceybot add !command message)")
            return
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
            if db.check_command(command_name):
                await ctx.send(f"@{ctx.author.name} --> That command already exists")
                return

            # Add the command to the commands table
            db.add_command(command_name, command_content)
            
            # Verify creation of command
            await ctx.send(f'@{ctx.author.name} --> The {command_name} command has been created!')


        # Deleting Commands
        if command_type[:3] == 'del':

            # Check if command exists
            if db.check_command(command_name):
                # Delete the command
                db.delete_command(command_name)

                # Verify deletion of command
                await ctx.send(f'@{ctx.author.name} --> The {command_name} command has been deleted!')
            else:
                await ctx.send(f"@{ctx.author.name} --> There is no command with the name {command_name}")
                return
            

        # Editing Commands
        if command_type == 'edit':
            
            # Check if command exits
            if db.check_command(command_name):
                db.edit_command(command_name, command_content)
                await ctx.send(f"@{ctx.author.name} -->  '{command_name}' updated")
                return
            else:
                await ctx.send(f"@{ctx.author.name} --> There is no command with the name {command_name}")


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

        user_watchtime = db.get_info(user, 'watchtime')

        days_raw = user_watchtime / 1440
        days = math.floor(days_raw)

        hours_raw = (days_raw - days) * 24
        hours = math.floor(hours_raw)

        minutes_raw = (hours_raw - hours) * 60
        minutes = round(minutes_raw)

        if user == ctx.author.name:
            if days >= 1:
                await ctx.send(f'@{user} has spent {days} days {hours} hours {minutes} minutes watching ItzChauncey')
            elif hours >= 1:
                await ctx.send(f'@{user} has spent {hours} hours {minutes} minutes watching ItzChauncey')
            elif minutes >= 1:
                await ctx.send(f'@{user} has spent {minutes} minutes watching ItzChauncey')
            else:
                await ctx.send(f'@{user} watchtime not found REEEEEE')
        else:
            if days >= 1:
                await ctx.send(f'@{ctx.author.name} --> {user} has spent {days} days {hours} hours {minutes} minutes watching ItzChauncey')
            elif hours >= 1:
                await ctx.send(f'@{ctx.author.name} --> {user} has spent {hours} hours {minutes} minutes watching ItzChauncey')
            elif minutes >= 1:
                await ctx.send(f'@{ctx.author.name} --> {user} has spent {minutes} minutes watching ItzChauncey')
            else:
                await ctx.send(f'@{ctx.author.name} --> {user} watchtime not found REEEEEE')


    @commands.command(name='points')
    async def points(self, ctx):
        w_command = ctx.content.split()
        if len(w_command) == 1:
            user = ctx.author.name
        elif w_command[1][0] == '@':
            user = w_command[1][1:].lower()

        user_points = db.get_info(user, 'points')
        if user == ctx.author.name:
            await ctx.send(f"@{user} --> You have {user_points} points!")
        else:
            await ctx.send(f"@{ctx.author.name} --> {user} has {user_points} points!")


bot = ChaunceyBot()
bot.run()