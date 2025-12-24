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
        await update.message.reply_text("Usage: /tag create|add|ping [...]")
        return

    action = context.args[0]
    tags.setdefault(chat_id, {})

    if action == "create":
        if not is_admin(member):
            await update.message.reply_text("Admins only.")
            return

        if len(context.args) < 2:
            await update.message.reply_text("Usage: /tag create <tag_name>")
            return

        tag = context.args[1].lower()  # Optional: make tags case-insensitive
        if tag in tags[chat_id]:
            await update.message.reply_text("Tag already exists.")
            return

        tags[chat_id][tag] = set()
        await update.message.reply_text(f"Tag '{tag}' created.")

    elif action == "add":
        if not is_admin(member):
            await update.message.reply_text("Admins only.")
            return

        if len(context.args) < 2:
            await update.message.reply_text("Usage: /tag add <tag> [@username1 ...] or reply to a message")
            return

        tag = context.args[1].lower()
        if tag not in tags[chat_id]:
            await update.message.reply_text("Tag does not exist.")
            return

        added_count = 0
        added_names = []

        # First, try to add from usernames in args (starting from index 2)
        for arg in context.args[2:]:
            if not arg.startswith("@") or len(arg) < 2:
                continue  # Skip invalid

            username = arg[1:]  # without @
            try:
                target_chat = await context.bot.get_chat(f"@{username}")
                target_id = target_chat.id
                target_name = target_chat.full_name or target_chat.username or f"User {target_id}"
                if target_chat.username:
                    target_name = f"@{target_chat.username}"

                if target_id in tags[chat_id][tag]:
                    added_names.append(f"{target_name} (already in tag)")
                else:
                    tags[chat_id][tag].add(target_id)
                    added_names.append(target_name)
                    added_count += 1
            except Exception as e:
                added_names.append(f"{arg} (not found or error)")

        # If no usernames provided in args, fall back to reply-to-message
        if added_count == 0 and len(added_names) == 0:
            if not update.message.reply_to_message:
                await update.message.reply_text("Provide at least one @username or reply to a user's message.")
                return

            target = update.message.reply_to_message.from_user
            target_id = target.id
            target_name = target.full_name or target.username or f"User {target_id}"
            if target.username:
                target_name = f"@{target.username}"

            if target_id in tags[chat_id][tag]:
                await update.message.reply_text(f"{target_name} is already in #{tag}.")
                return

            tags[chat_id][tag].add(target_id)
            await update.message.reply_text(
                f"{target_name} added to #{tag}"
            )
        else:
            # Feedback for username additions
            await update.message.reply_text(
                f"Added {added_count} user(s) to #{tag}:\n" + "\n".join(added_names)
            )

    elif action == "ping":
        # (unchanged, except optional lower() for tag)
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /tag ping <tag> [message]")
            return

        tag = context.args[1].lower()
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
