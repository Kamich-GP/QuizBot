import telebot
from pymongo import MongoClient
import bt

bot = telebot.TeleBot("6059362707:AAHV__YmJin22J1YL_IeVNAZvo4ddYn3ir0")

class DataBase:
    def __init__(self):
        cluster = MongoClient("mongodb+srv://admin:admin@cluster0.hsvm4dm.mongodb.net/?retryWrites=true&w=majority")

        self.db = cluster["QuizBot"]
        self.users = self.db["Users"]
        self.questions = self.db["Questions"]

        self.questions_count = len(list(self.questions.find({})))
    def get_user(self, chat_id):
        user = self.users.find_one({"chat_id": chat_id})

        if user is not None:
            return user
        user = {
            "chat_id": chat_id,
            "name_class": "",
            "is_passing": False,
            "is_passed": False,
            "question_index": None,
            "answers": []
        }
        self.users.insert_one(user)
        return user
    def del_all_users(self):
        self.users.delete_many({})
    def set_user(self, chat_id, update):
        self.users.update_one({"chat_id": chat_id}, {"$set": update})
    def set_name_class(self, name_class, update):
        self.users.update_one({"name_class": name_class, "$set": update})

    def get_questions(self, index):
        return self.questions.find_one({"id": index})

db = DataBase()

@bot.message_handler(commands=['start'])
def get_name(message):
    bot.send_message(message.from_user.id, 'Введите свое имя и класс\nПример: Иванов Иван 5А')
    bot.register_next_step_handler(message, start)
def start(message):
    user = db.get_user(message.chat.id)
    name = message.text
    if user["is_passed"]:
        bot.send_message(message.from_user.id, "Вы уже прошли этот тест. Второй раз проходить его нельзя.")
        return
    if user["is_passing"]:
        return
    db.set_user(message.chat.id, {"name_class": name})
    db.set_user(message.chat.id, {"question_index": 0, "is_passing": True})


    user = db.get_user(message.chat.id)
    post = get_question_message(user)
    if post is not None:
        bot.send_message(message.from_user.id, post["text"], reply_markup=post['kb'])
@bot.callback_query_handler(func=lambda query: query.data.startswith("?ans"))
def answered(query):
    user = db.get_user(query.message.chat.id)

    if user is None or user["is_passed"] or not user["is_passing"]:
        return

    user["answers"].append(int(query.data.split("&")[1]))
    db.set_user(query.message.chat.id, {"answers": user["answers"]})

    post = get_answered_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id, reply_markup=post["kb"])

@bot.callback_query_handler(func=lambda query: query.data == "?next")
def next(query):
    user = db.get_user(query.message.chat.id)

    if user["is_passed"] or not user["is_passing"]:
        return

    user["question_index"] += 1
    db.set_user(query.message.chat.id, {"question_index": user["question_index"]})

    post = get_question_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id, reply_markup=post["kb"])



def get_question_message(user):
    if user["question_index"] == db.questions_count:
        count = 0
        for question_index, question in enumerate(db.questions.find({})):
            if question['correct'] == user["answers"][question_index]:
                count += 1
        percents = round(100 * count / db.questions_count)

        if percents < 30:
            smile = "😥"
            score = 2
        elif percents < 50:
            smile = "😐"
            score = 3
        elif percents < 80:
            smile = "😃"
            score = 4
        else:
            smile = "😎"
            score = 5

        text = f"Вы ответили правильно на {percents}% вопросов, ваша оценка {score}{smile}"

        db.set_user(user["chat_id"], {"is_passed": True, "is_passing": False})

        return {
            "text": text,
            "kb": None
        }
    question = db.get_questions(user["question_index"])

    if question is None:
        return
    kb = telebot.types.InlineKeyboardMarkup()
    for answer_index, answer in enumerate(question["answers"]):
        kb.row(telebot.types.InlineKeyboardButton(f'{chr(answer_index + 97)}) {answer}',
                                                  callback_data=f'?ans&{answer_index}'))
    text = f'Вопрос №{user["question_index"] + 1}\n\n{question["text"]}'
    return {
        "text": text,
        "kb": kb
    }

def get_answered_message(user):
    question = db.get_questions(user["question_index"])

    text = f"Вопрос №{user['question_index'] + 1}\n\n{question['text']}\n"
    for answer_index, answer in enumerate(question["answers"]):
        text += f"{chr(answer_index + 97)}) {answer}"

        if answer_index == question["correct"]:
            text += "✔"
        elif answer_index == user["answers"][-1]:
            text += "❌"

        text += "\n"

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("Далее", callback_data="?next"))

    return {
        "text": text,
        "kb": kb
    }
@bot.message_handler(commands=['admin'])
def enter(message):
    bot.send_message(message.from_user.id, 'Введите пароль')
    bot.register_next_step_handler(message, check)

def check(message):
    user_pass = message.text
    password = '123'
    if user_pass == password:
        bot.send_message(message.from_user.id, 'Добро пожаловать в админ панель!', reply_markup=bt.admin_buttons())
        bot.register_next_step_handler(message, admin)
    else:
        bot.send_message(message.from_user.id, 'Пароль неверный!')
def admin(message):
    if message.text.lower() == 'изменить имя':
        bot.send_message(message.from_user.id, 'Кого вы хотите поменять?', reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, set_name_class1)
    elif message.text.lower() == 'удалить всех учеников':
        bot.send_message(message.from_user.id, 'Вы точно хотите очистить базу учеников?', reply_markup=bt.yes_no())
        bot.register_next_step_handler(message, del_check)
    else:
        bot.send_message(message.from_user.id, 'Нажимайте на кнопки!', reply_markup=bt.admin_buttons())
        bot.register_next_step_handler(message, admin)
def set_name_class1(message):
    name_class = message.text
    students = db.get_user(message.chat.id)
    if name_class == students["name_class"]:
        bot.send_message(message.from_user.id, 'Пишите новое имя и класс')
        bot.register_next_step_handler(message, set_name)
    else:
        bot.send_message(message.from_user.id, 'Такого ученика нет!')
        bot.register_next_step_handler(message, set_name_class1)

def del_check(message):
    if message.text == 'Да':
        db.del_all_users()
        bot.send_message(message.from_user.id, 'База учеников очищена!', reply_markup=bt.admin_buttons())
        bot.register_next_step_handler(message, admin)
    elif message.text == 'Нет':
        bot.send_message(message.from_user.id, 'Возвращаю вас обратно в главное меню', reply_markup=bt.admin_buttons())
        bot.register_next_step_handler(message, admin)

def set_name(message):
    new_name = message.text
    db.set_user(message.chat.id, {"name_class": new_name})
    bot.send_message(message.from_user.id, 'Ученик изменен!', reply_markup=bt.admin_buttons())
    bot.register_next_step_handler(message, admin)
bot.polling()