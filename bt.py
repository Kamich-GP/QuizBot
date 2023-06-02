from telebot import types

def admin_buttons():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('Изменить имя')
    button1 = types.KeyboardButton('Удалить всех учеников')

    kb.add(button, button1)

    return kb

def yes_no():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    yes = types.KeyboardButton('Да')
    no = types.KeyboardButton('Нет')

    kb.add(yes, no)

    return kb
