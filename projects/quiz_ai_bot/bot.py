import json
import random
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# Load questions from JSON
with open('questions.json') as f:
    questions = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Quiz Bot! Используйте /algoquiz или /guess_techno для начала."
    )

async def algoquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send algorithm complexity quiz question as a poll"""
    question = random.choice(questions['algorithm_questions'])
    options = [f"{chr(65+i)}) {opt}" for i, opt in enumerate(question['options'])]
    correct_option = ord(question['correct']) - 65  # Convert A=0, B=1, etc.
    
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=f"Какая временная сложность у:\n{question['description']}",
        options=options,
        type="quiz",
        correct_option_id=correct_option,
        is_anonymous=False,
        explanation=f"Правильный ответ: {question['correct']}) {question['options'][correct_option]}"
    )

async def guess_techno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send technology description for guessing"""
    question = random.choice(questions['technology_questions'])
    await update.message.reply_text(
        f"Угадайте технологию:\n\n{question['description']}"
    )
    context.user_data['correct_technology'] = question['technology']
    if 'accepted_answers' in question:
        context.user_data['accepted_answers'] = question['accepted_answers']

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user's answer to technology guessing questions"""
    if 'correct_technology' in context.user_data:
        user_guess = update.message.text.lower()
        correct = context.user_data['correct_technology'].lower()
        accepted_answers = [a.lower() for a in context.user_data.get('accepted_answers', [])]
        
        if user_guess == correct or user_guess in accepted_answers:
            await update.message.reply_text("Правильно! 🎉")
        else:
            await update.message.reply_text(f"Неверно! Правильный ответ: {correct}.")
        del context.user_data['correct_technology']
        if 'accepted_answers' in context.user_data:
            del context.user_data['accepted_answers']

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("algoquiz", algoquiz))
    app.add_handler(CommandHandler("guess_techno", guess_techno))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    
    app.run_polling()

if __name__ == "__main__":
    main()