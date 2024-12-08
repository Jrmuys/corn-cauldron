import discord
import os # default module
from dotenv import load_dotenv
from mathces import get_dota_matches

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="Match 10239581",
        description="This is a test",
        color=discord.Colour.brand_red(),
    )
    embed.add_field(name="A Normal Field", value="A really nice field with some information. **The description as well as the fields support markdown!**")

    embed.add_field()

    embed.add_field(name="Inline Field 1", value="Inline Field 1", inline=True)
    embed.add_field(name="Inline Field 2", value="Inline Field 2", inline=True)
    embed.add_field(name="Inline Field 3", value="Inline Field 3", inline=True)
 
    embed.set_footer(text="Footer! No markdown here.") # footers can have icons too
    embed.set_author(name="Pycord Team", icon_url="https://example.com/link-to-my-image.png")
    embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
    embed.set_image(url="https://example.com/link-to-my-banner.png")
    await ctx.respond("Hey!", embed=embed)

bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token