import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

tags = {}


def is_admin(member):
    return member.status in ("administrator", "creator")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tag bot is running.")


async def tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    member = await update.effective_chat.get_member(user.id)

    if not context.args:
        await update.message.reply_text("Usage: /tag create|add|ping")
        return

    action = context.args[0]
    tags.setdefault(chat_id, {})

    if action == "create":
        if not is_admin(member):
            await update.message.reply_text("Admins only.")
            return

        tag = context.args[1]
        if tag in tags[chat_id]:
            await update.message.reply_text("Tag already exists.")
            return

        tags[chat_id][tag] = set()
        await update.message.reply_text(f"Tag '{tag}' created.")

    elif action == "add":
        if not is_admin(member):
            await update.message.reply_text("Admins only.")
            return

        tag = context.args[1]
        if tag not in tags[chat_id]:
            await update.message.reply_text("Tag does not exist.")
            return

        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a user to add them.")
            return

        target = update.message.reply_to_message.from_user
        tags[chat_id][tag].add(target.id)

        await update.message.reply_text(
            f"{target.mention_html()} added to #{tag}",
            parse_mode="HTML"
        )

    elif action == "ping":
        tag = context.args[1]
        message = " ".join(context.args[2:])

        if tag not in tags[chat_id]:
            await update.message.reply_text("Tag does not exist.")
            return

        mentions = [
            f"<a href='tg://user?id={uid}'>•</a>"
            for uid in tags[chat_id][tag]
        ]

        if not mentions:
            await update.message.reply_text("Tag is empty.")
            return

        await update.message.reply_text(
            f"{''.join(mentions)}\n{message}",
            parse_mode="HTML"
        )


async def hashtag_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    if not text.startswith("#"):
        return

    tag = text.split()[0][1:]
    chat_id = update.effective_chat.id

    if tag not in tags.get(chat_id, {}):
        return

    mentions = [
        f"<a href='tg://user?id={uid}'>•</a>"
        for uid in tags[chat_id][tag]
    ]

    if mentions:
        await update.message.reply_text(
            "".join(mentions),
            parse_mode="HTML"
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tag", tag_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, hashtag_listener)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
