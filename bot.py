from vkbottle import User, load_blueprints_from_package
import os

token_user = os.getenv("USER")
bot = User(token=token_user)

for bp in load_blueprints_from_package('blueprints'):
    bp.load(bot)

bot.run_forever()