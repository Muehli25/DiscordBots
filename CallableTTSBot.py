import discord

from gtts import gTTS
import uuid
import os
import queue

DATA_FOLDER = "data"


class SummonableTTSBot(discord.Client):

    def __init__(self, language="en"):
        super().__init__()
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        self.CurrentConnection = None
        self.language = language
        self.queue = queue.Queue()
        self.play_next()

    async def call_bot(self, channel):
        self.CurrentConnection = await channel.connect()
        self.play_next()

    async def goodbye_bot(self):
        await self.CurrentConnection.disconnect()
        self.CurrentConnection = None
        self.queue = queue.Queue()

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    def delete_file(self, filename):
        os.remove(filename)

    def play_next(self):
        if self.CurrentConnection is not None and not self.CurrentConnection.is_playing() and not self.queue.empty():
            to_play = self.queue.get()
            self.CurrentConnection.play(discord.FFmpegPCMAudio(to_play),
                                        after=lambda e: self.delete_file(filename=to_play))
        if self.CurrentConnection is not None:
            self.loop.call_later(0.5, self.play_next)

    def abort_playback(self):
        file = ""
        self.CurrentConnection.stop()
        while True:
            try:
                file = self.queue.get(block=False)
            except queue.Empty:
                break
        self.delete_file(file)
        self.queue = queue.Queue()

    def play(self, file):
        self.CurrentConnection.play(file)

    async def on_message(self, message):
        if message.author == self.user:
            return

        elif message.content == "!call":
            await message.channel.send('Hello!')
            await self.call_bot(message.author.voice.channel)

        elif message.content == '!bye' and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            await message.channel.send('Goodbye!')
            await self.goodbye_bot()

        elif message.content == "!abort":
            self.abort_playback()

        else:
            if self.CurrentConnection is not None \
                    and self.CurrentConnection.is_connected():
                lang = self.language
                text = user_input = message.content
                if user_input[0] == "+":
                    divider = user_input.find(" ")
                    lang = user_input[1:divider]
                    text = user_input[(divider + 1):]
                # Create uuid as filename
                name = uuid.uuid1()
                # Play the requested text
                try:
                    filename = f'{DATA_FOLDER}/{name}.mp3'
                    tts = gTTS(text, lang=lang)
                    tts.save(filename)
                    self.queue.put(filename)
                except ValueError:
                    await message.channel.send(f"Language not supported or no Text provided.")


# Create new bot
client = SummonableTTSBot()
if os.getenv("LANG") is not None:
    client = SummonableTTSBot(os.environ['LANG'])
# run Bot with provided discord token
client.run(os.environ['TOKEN'])
