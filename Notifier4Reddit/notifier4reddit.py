import discord
from discord.ext import commands
import praw
import asyncio
from random import choice as randchoice
import os
import time
import json

class Notifier4Reddit:
    def __init__(self, bot):
        self.bot = bot
        self.is_polling = False
        self.poll_rate = 60
        self.channels = set()
        self.subreddits = set()
        self.last_checked_times = dict()
        try:
            config = json.load(open('./data/Notifier4Reddit/config.json'))
            self.reddit = praw.Reddit(client_id=config['client_id'],
                                    client_secret=config['client_secret'],
                                    user_agent=config['user_agent'],
                                    username=config['username'],
                                    password=config['password'])
        except:
            await self.bot.say("Failed to create Praw instance.")

    @commands.command(pass_context=True)
    async def n4radd(self, ctx, *, subreddit):
        """Adds a subreddit to poll from"""
        if subreddit in self.subreddits:
            await self.bot.say("Already subscribed to " + subreddit)
            return

        try:
            # Check if valid subreddit
            test = self.reddit.subreddit(subreddit).description

            self.subreddits.add(subreddit)
            self.last_checked_times[subreddit] = time.time()
            await self.bot.say("Added " + subreddit + " to list.")
        except:
            await self.bot.say("Failed to add " + subreddit + " to list.")

    @commands.command()
    async def n4rlist(self):
        """List of subscribed subreddits"""
        subreddits = ', '.join(sorted(self.subreddits))
        msg = subreddits if len(subreddits) > 0 else "No subreddits added."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def n4rrm(self, ctx, *, subreddit):
        """Removes a subreddit from polling list"""
        if subreddit in self.subreddits:
            self.subreddits.remove(subreddit)
            self.last_checked_times.pop(subreddit, None)
            await self.bot.say("Removed " + subreddit + " from list.")
        else:
            await self.bot.say(subreddit + " not in list.")

    @commands.command(pass_context=True)
    async def n4rrate(self, ctx, *, rate):
        """Sets the polling rate"""
        self.poll_rate = rate
        await self.bot.say("Polling rate set to " + self.poll_rate)

    @commands.command(pass_context=True)
    async def n4rstart(self, ctx):
        """Updates state to start polling"""

        self.is_polling = True
        self.channels.add(ctx.message.channel)
        await self.bot.say("Ok, started polling!")

    @commands.command()
    async def n4rstop(self):
        """Changes state to stop polling"""

        self.is_polling = False
        await self.bot.say("Ok, stopped polling!")

    async def polling(self):
        while True:
            if self.is_polling:
                for x in self.subreddits:
                    last_checked = self.last_checked_times[x]
                    next_check_time = last_checked
                    try:
                        subreddit = self.reddit.subreddit(x)
                        for submission in subreddit.new(limit=10):
                            next_check_time = max(next_check_time, submission.created_utc)
                            if last_checked < submission.created_utc:
                                print(submission.title)
                                colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
                                colour = int(colour, 16)
                                em = discord.Embed(title=submission.title,
                                                colour=discord.Colour(value=colour),
                                                url=submission.url,
                                                description=submission.shortlink)
                                for channel in self.channels:
                                    await self.bot.send_message(channel, embed=em)
                            else:
                                break
                        self.last_checked_times[x] = next_check_time
                    except:
                        continue
            await asyncio.sleep(self.poll_rate)

def setup(bot):
    if os.path.isfile('./data/Notifier4Reddit/config.json'):
        notifier = Notifier4Reddit(bot)
        loop = asyncio.get_event_loop()
        loop.create_task(notifier.polling())
        bot.add_cog(notifier)
    else:
        print("Failed to find config file for Notifier4Reddit.")