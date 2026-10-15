import logging

from telegram import Update
from telegram.ext import ContextTypes

from .keyboards import group_keyboard, main_keyboard
from .messages import format_schedule

logger = logging.getLogger(__name__)


class BotHandlers:
    def __init__(self, service, repository):
        self.service = service
        self.repository = repository

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        group = self.repository.get_selected_group(user_id)
        if group in self.service.groups:
            await update.message.reply_text(f"Grupa selectată: {group}", reply_markup=main_keyboard())
            return
        await update.message.reply_text(
            "Bun venit! Alege grupa:",
            reply_markup=group_keyboard(self.service.groups),
        )

    async def text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.message.text
        user_id = update.effective_user.id
        if text in self.service.groups:
            self.repository.save_selected_group(user_id, text)
            await update.message.reply_text(f"Grupa {text} a fost salvată.", reply_markup=main_keyboard())
            return
        group = self.repository.get_selected_group(user_id)
        if text == "⚙️ Schimbă grupa":
            await update.message.reply_text("Alege grupa:", reply_markup=group_keyboard(self.service.groups))
        elif not group:
            await update.message.reply_text("Alege mai întâi grupa.", reply_markup=group_keyboard(self.service.groups))
        elif text == "📅 Program azi":
            entries = self.service.today(group)
            await update.message.reply_text(
                format_schedule(entries, self.service.breaks(group)),
                reply_markup=main_keyboard(),
            )
        elif text == "🕐 Acum":
            status, entries, minutes = self.service.current_status(group)
            if status == "active":
                message = f"🟢 Acum\n\n{format_schedule(entries)}"
            elif status == "break":
                message = f"☕ Pauză acum · încă {minutes} min\n\n{format_schedule(entries)}"
            elif status == "next":
                message = f"Următoarea activitate:\n{format_schedule(entries)}"
            else:
                message = "Nu mai sunt activități azi."
            await update.message.reply_text(message, reply_markup=main_keyboard())
