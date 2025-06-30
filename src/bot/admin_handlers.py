from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from src.application.channel_manager import ChannelManager


class RssStates(StatesGroup):
    waiting_rss_add = State()
    waiting_rss_remove = State()
    waiting_interval = State()


def admin_router(channel_manager: ChannelManager) -> Router:
    router = Router()

    def get_channel_kb(channel):
        kb = [
            [InlineKeyboardButton(
                text="Выключить" if channel.enabled else "Включить",
                callback_data=f"toggle_{channel.id}"
            )],
            [InlineKeyboardButton(
                text="Добавить RSS",
                callback_data=f"add_rss_{channel.id}"
            )],
        ]
        if channel.rss_links:
            kb.append([InlineKeyboardButton(
                text="Удалить RSS",
                callback_data=f"remove_rss_{channel.id}"
            )])
        kb.append([InlineKeyboardButton(
            text="Настроить интервал обработки",
            callback_data=f"set_interval_{channel.id}"
        )])
        kb.append([InlineKeyboardButton(text="Назад", callback_data="list_channels")])
        return InlineKeyboardMarkup(inline_keyboard=kb)

    async def safe_edit(call: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
        msg = call.message
        if msg is None or not hasattr(msg, "edit_text"):
            await call.answer("Нет сообщения для обновления.", show_alert=True)
            return
        try:
            if getattr(msg, "text", None) == text and getattr(msg, "reply_markup", None) == kb:
                await call.answer("Без изменений.")
                return
            await msg.edit_text(text, reply_markup=kb)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise

    @router.message(Command("admin"))
    async def admin_menu(message: Message):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Список каналов", callback_data="list_channels")]
            ]
        )
        await message.answer("Админ-меню:", reply_markup=kb)

    @router.callback_query(F.data == "admin_menu")
    async def back_to_admin_menu(call: CallbackQuery):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Список каналов", callback_data="list_channels")]
            ]
        )
        await safe_edit(call, "Админ-меню:", kb)

    @router.callback_query(F.data == "list_channels")
    async def list_channels(call: CallbackQuery):
        channels = await channel_manager.channel_service.get_all_channels()
        if not channels:
            await safe_edit(call, "Каналов нет.", InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="admin_menu")]]
            ))
            return
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{c.title} ({'✅' if c.enabled else '❌'})",
                callback_data=f"channel_{c.id}"
            )] for c in channels
        ] + [[InlineKeyboardButton(text="Назад", callback_data="admin_menu")]])
        await safe_edit(call, "Список каналов:", kb)

    async def render_channel_info(channel):
        return (
            f"Канал: {channel.title}\n"
            f"ID: {channel.id}\n"
            f"Статус: {'Работает' if channel.enabled else 'Отключен'}\n"
            f"RSS: {', '.join(channel.rss_links) if channel.rss_links else 'нет'}\n"
            f"Интервал: {channel.work_interval_minutes} мин."
        )

    @router.callback_query(F.data.startswith("channel_"))
    async def channel_menu(call: CallbackQuery):
        data = call.data
        if not data or "_" not in data:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(data.split("_")[1])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if not channel:
            await call.answer("Канал не найден.", show_alert=True)
            return
        text = await render_channel_info(channel)
        await safe_edit(call, text, get_channel_kb(channel))

    @router.callback_query(F.data.startswith("toggle_"))
    async def toggle_channel(call: CallbackQuery):
        data = call.data
        if not data or "_" not in data:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(data.split("_")[1])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if not channel:
            await call.answer("Канал не найден.", show_alert=True)
            return
        if channel.enabled:
            await channel_manager.disable_channel(channel_id)
        else:
            await channel_manager.enable_channel(channel_id)
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if not channel:
            await call.answer("Канал не найден после изменения.", show_alert=True)
            return
        text = await render_channel_info(channel)
        await safe_edit(call, text, get_channel_kb(channel))

    @router.callback_query(F.data.startswith("add_rss_"))
    async def add_rss_start(call: CallbackQuery, state: FSMContext):
        data = call.data
        if not data or data.count("_") < 2:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(data.split("_")[2])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        await state.update_data(channel_id=channel_id)
        if call.message:
            await call.message.answer("Введите новую RSS-ссылку для этого канала:")
        await state.set_state(RssStates.waiting_rss_add)

    @router.message(RssStates.waiting_rss_add)
    async def add_rss_finish(message: Message, state: FSMContext):
        data = await state.get_data()
        channel_id = data.get("channel_id")
        if not isinstance(channel_id, int):
            await message.answer("Ошибка: не удалось определить канал.")
            await state.clear()
            return
        rss_url = (message.text or "").strip()
        if not rss_url.startswith("http"):
            await message.answer("Похоже, это не ссылка. Попробуйте ещё раз или отправьте корректный URL.")
            return
        ok = await channel_manager.add_rss(channel_id, rss_url)
        if ok:
            await message.answer("RSS-ссылка добавлена!")
        else:
            await message.answer("Ошибка при добавлении RSS или такая ссылка уже есть.")
        await state.clear()
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if channel:
            text = await render_channel_info(channel)
            await message.answer(text, reply_markup=get_channel_kb(channel))

    @router.callback_query(F.data.startswith("remove_rss_"))
    async def remove_rss_start(call: CallbackQuery, state: FSMContext):
        data = call.data
        if not data or data.count("_") < 2:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(data.split("_")[2])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if not channel or not channel.rss_links:
            await call.answer("Нет RSS для удаления.", show_alert=True)
            return
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=link, callback_data=f"confirm_remove_rss_{channel_id}_{i}")]
            for i, link in enumerate(channel.rss_links)
        ] + [[InlineKeyboardButton(text="Назад", callback_data=f"channel_{channel_id}")]])
        if call.message:
            await call.message.answer("Выберите RSS для удаления:", reply_markup=kb)

    @router.callback_query(F.data.startswith("confirm_remove_rss_"))
    async def remove_rss_confirm(call: CallbackQuery):
        data = call.data
        if not data:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        parts = data.split("_")
        if len(parts) < 5:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(parts[3])
            idx = int(parts[4])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if not channel or idx >= len(channel.rss_links):
            await call.answer("Ошибка!", show_alert=True)
            return
        rss_url = channel.rss_links[idx]
        ok = await channel_manager.remove_rss(channel_id, rss_url)
        if ok:
            await call.answer("RSS удалён.")
        else:
            await call.answer("Ошибка при удалении RSS.", show_alert=True)
        channel = await channel_manager.channel_service.get_channel(channel_id)
        if channel:
            text = await render_channel_info(channel)
            if call.message:
                await call.message.answer(text, reply_markup=get_channel_kb(channel))

    @router.callback_query(F.data.startswith("set_interval_"))
    async def set_interval_start(call: CallbackQuery, state: FSMContext):
        data = call.data
        if not data or data.count("_") < 2:
            await call.answer("Некорректные данные.", show_alert=True)
            return
        try:
            channel_id = int(data.split("_")[2])
        except Exception:
            await call.answer("Некорректный ID.", show_alert=True)
            return
        await state.update_data(channel_id=channel_id)
        if call.message:
            await call.message.answer("Введите интервал обработки канала в минутах (целое число):")
        await state.set_state(RssStates.waiting_interval)

    @router.message(RssStates.waiting_interval)
    async def set_interval_finish(message: Message, state: FSMContext):
        data = await state.get_data()
        channel_id = data.get("channel_id")
        if not isinstance(channel_id, int):
            await message.answer("Ошибка: не удалось определить канал.")
            await state.clear()
            return
        text = (message.text or "").strip()
        if not text.isdigit():
            await message.answer("Пожалуйста, введите целое число для интервала в минутах.")
            return
        interval = int(text)
        if interval <= 0:
            await message.answer("Интервал должен быть положительным числом.")
            return
        await channel_manager.set_work_interval(channel_id, interval)
        await message.answer(f"Интервал обработки канала установлен на {interval} минут.")
        await state.clear()

        channel = await channel_manager.channel_service.get_channel(channel_id)
        if channel:
            text = await render_channel_info(channel)
            await message.answer(text, reply_markup=get_channel_kb(channel))

    return router
