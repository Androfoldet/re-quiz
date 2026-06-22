import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from questions import QUESTIONS
from characters import CHARACTERS
from matcher import get_winner, build_result_text

BOT_TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher(storage=MemoryStorage())

class QuizState(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    q7 = State()
    q8 = State()
    result = State()


STATES = [
    QuizState.q1, QuizState.q2, QuizState.q3, QuizState.q4,
    QuizState.q5, QuizState.q6, QuizState.q7, QuizState.q8,
]


def make_question_keyboard(question):
    buttons = []
    for a in question["answers"]:
        buttons.append([InlineKeyboardButton(
            text=a["text"],
            callback_data=f"quiz:q{question['id']}:{a['idx']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def make_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Начать тест", callback_data="quiz:start")]
    ])


def make_replay_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Пройти тест снова", callback_data="quiz:start")]
    ])


@dp.message(Command("start", "restart"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🧟 *Добро пожаловать в Resident Evil Quiz!*\n\n"
        "Тебя ждут 8 вопросов из мира биотеррора. "
        "Отвечай честно — и узнай, кто ты в этой вселенной.",
        parse_mode="Markdown",
        reply_markup=make_start_keyboard(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Это викторина по вселенной Resident Evil. "
        "Ответь на 8 вопросов — и узнай, какой ты персонаж.\n\n"
        "/start — начать\n"
        "/restart — начать заново"
    )


@dp.callback_query(F.data == "quiz:start")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizState.q1)

    scores = {cid: 0 for cid in CHARACTERS}
    await state.update_data(scores=scores)

    q = QUESTIONS[0]
    await callback.message.answer(
        f"*Вопрос 1 из 8*\n\n{q['text']}",
        parse_mode="Markdown",
        reply_markup=make_question_keyboard(q),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("quiz:q"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    parts = callback.data.split(":")
    q_num = int(parts[1][1:])
    answer_idx = int(parts[2])

    # Бот перезапустился — нет активного состояния
    if current_state is None:
        await callback.answer()
        await callback.message.answer(
            "Похоже, бот перезапустился. Нажми /start, чтобы начать заново."
        )
        return

    # Устаревшая кнопка от другого вопроса
    expected = f"QuizState:q{q_num}"
    if current_state != expected:
        await callback.answer()
        return

    q = QUESTIONS[q_num - 1]
    answer = next(a for a in q["answers"] if a["idx"] == answer_idx)

    data = await state.get_data()
    scores = data["scores"]
    for char_id, points in answer["scores"].items():
        scores[char_id] += points
    await state.update_data(scores=scores)

    if q_num < 8:
        next_q = QUESTIONS[q_num]
        await state.set_state(STATES[q_num])
        await callback.message.answer(
            f"*Вопрос {q_num + 1} из 8*\n\n{next_q['text']}",
            parse_mode="Markdown",
            reply_markup=make_question_keyboard(next_q),
        )
    else:
        await state.set_state(QuizState.result)
        winner_id = get_winner(scores)
        character = CHARACTERS[winner_id]
        result_text = build_result_text(winner_id, character)
        await callback.message.answer(
            result_text,
            parse_mode="Markdown",
            reply_markup=make_replay_keyboard(),
        )

    await callback.answer()



async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
