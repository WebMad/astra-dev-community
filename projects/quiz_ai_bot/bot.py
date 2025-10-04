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
    sent_message = await update.message.reply_text(
        f"Угадайте технологию (у вас 3 попытки):\n\n{question['description']}"
    )
    context.user_data['current_question'] = {
        'correct_technology': question['technology'],
        'attempts_left': 3,
        'message_id': sent_message.message_id  # Store the sent message's ID
    }
    if 'accepted_answers' in question:
        context.user_data['current_question']['accepted_answers'] = question['accepted_answers']

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user's answer to technology guessing questions"""
    if 'current_question' not in context.user_data:
        return
        
    # Get the reply info if available
    reply_to = getattr(update.message, 'reply_to_message', None)
    if not reply_to or reply_to.message_id != context.user_data['current_question']['message_id']:
        return
        
    user_guess = update.message.text.lower()
    correct = context.user_data['current_question']['correct_technology'].lower()
    accepted_answers = [a.lower() for a in context.user_data['current_question'].get('accepted_answers', [])]
    
    if user_guess == correct or user_guess in accepted_answers:
        try:
            await context.bot.set_message_reaction(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                reaction=["🎉"]
            )
        except Exception as e:
            print(f"Error setting reaction: {e}")
        del context.user_data['current_question']
    else:
        context.user_data['current_question']['attempts_left'] -= 1
        if context.user_data['current_question']['attempts_left'] > 0:
            try:
                await context.bot.set_message_reaction(
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id,
                    reaction=["👎"]
                )
            except Exception as e:
                print(f"Error setting reaction: {e}")
        else:
            try:
                await context.bot.set_message_reaction(
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id,
                    reaction=["🤡"]
                )
                await update.message.reply_text(
                    f"Попытки закончились! Правильный ответ: {correct}."
                )
                del context.user_data['current_question']
            except Exception as e:
                print(f"Error setting reaction: {e}")

def main():
    # Create application with post_init callback
    async def post_init(application):
        commands = [
            ("start", "Начало работы с ботом"),
            ("algoquiz", "Викторина по алгоритмам"),
            ("guess_techno", "Угадай технологию")
        ]
        await application.bot.set_my_commands(commands)
    
    app = Application.builder() \
        .token(os.getenv("TELEGRAM_BOT_TOKEN")) \
        .post_init(post_init) \
        .build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("algoquiz", algoquiz))
    app.add_handler(CommandHandler("guess_techno", guess_techno))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    
    app.run_polling()

if __name__ == "__main__":
    main()