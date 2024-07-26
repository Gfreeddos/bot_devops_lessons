# Подлючаем библиотеки
import json
import re
import os

import logging
from dotenv import load_dotenv
import paramiko

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext,
                          CallbackQueryHandler)

import psycopg2
from psycopg2 import Error

# Подключаем и вычитываем переменные из файла .env
load_dotenv()
TOKEN = os.getenv('TG_TOKEN')
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = int(os.getenv('SSH_PORT'))
SSH_USERNAME = os.getenv('SSH_USERNAME')
SSH_PASSWORD = os.getenv('SSH_PASSWORD')

PG_USER = os.getenv('PG_USER')
PG_PASSWD = os.getenv('PG_PASSWD')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = int(os.getenv('PG_PORT'))
PG_DB = os.getenv('PG_DB')

# Подключаем логирование стандартной конфигурацией
# Далее используем logger в процедурах для логирования
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Обработка /start
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')
    logger.info(f"User {user.full_name}(id={user.id}) get command /start")

# Обработка общего /help
def help_command(update: Update, context):
    user = update.effective_user
    update.message.reply_text(
        '''
/find_phone_number - найти номер телефона в тексте
/get_phone_numbers - вывести телефоны из БД
/find_email - найти email'ы в тексте
/get_emails - вывести email'ы из БД
/verify_password - проверка пароля
/get_help - вывод списка команд запросов SSH
/start - Начать работу с ботом
/help - Вызов этой справки
''')
    logger.info(f"User {user.full_name}(id={user.id}) get command /help")

# Обработка /get_help, вывод помощи команд ssh
def ssh_help_command(update: Update, context):
    user = update.effective_user
    wrapp_ssh = ssh_command_funct()
    update.message.reply_text(wrapp_ssh.help())
    logger.info(f"User {user.full_name}(id={user.id}) get command /get_help")

# Обработка команды /find_phone_number, с переходом в процедуру find_phone_number
def find_phone_number_command(update: Update, context):
    user = update.effective_user
    update.message.reply_text("Введите текст для поиска телефонных номеров: ")
    logger.info(f"User {user.full_name}(id={user.id}) get command /find_phone_number")
    return 'find_phone_number'

# Обработка команды /find_email, с переходом в процедуру find_email
def find_email_command(update: Update, context):
    user = update.effective_user
    update.message.reply_text("Введите текст для поиска email'ов: ")
    logger.info(f"User {user.full_name}(id={user.id}) get command /find_email")
    return 'find_email'

# Обработка команды /verify_password, с переходом в процедуру verify_password
def verify_password_command(update: Update, context):
    user = update.effective_user
    update.message.reply_text("Введите пароль для проверки: ")
    logger.info(f"User {user.full_name}(id={user.id}) get command /verify_password")
    return 'verify_password'

# Вариант обработки /get_app_list, где у пользователя спрашиваются пакеты для вывода информации
# def get_app_list_command(update: Update, context):
#     user = update.effective_user
#     wrapp_ssh = ssh_command_funct()
#     send_long_message(update,ssh_chek(wrapp_ssh('/get_app_list'), user))
#     update.message.reply_text("Введите имя приложения для выдачи информации по нему: ")
#     logger.info(f"User {user.full_name}(id={user.id}) get command /get_app_list")
#     return 'get_app_list'
#
# def get_app_list(update: Update, context):
#     user = update.effective_user
#     text = update.message.text
#
#     send_long_message(update, ssh_chek('dpkg -s ' + text, user))
#
#     logger.info(f"User {user.full_name}(id={user.id}) get ssh command - /get_app_list {text}")
#
#     return ConversationHandler.END

# Обработка уведомления о необходимости ввести команду (общий обработчик)
def without_command(update: Update, context):
    user = update.effective_user
    update.message.reply_text("Введите команду, /help поможет ")
    logger.warning(f"User {user.full_name}(id={user.id}) get unknown command, replace /help message")

# Процедура поиска телефонных номеров в тексте
def find_phone_number(update: Update, context):
    user = update.effective_user
    text = update.message.text

    # Регулярное вырожение для поиска номеров
    phone_pattern = re.compile(
        r'(\+?7|8)[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}|\+7-\d{3}-\d{3}-\d{2}-\d{2}'
    )

    # Сбор всех номеров, приводим к единому формату и убираем дубли
    cleaned_numbers = []
    for match in re.finditer(phone_pattern, text):
        number = match.group()
        cleaned_number = re.sub(r'[-.\s()]', '', number)
        cleaned_numbers.append(cleaned_number)
    cleaned_numbers=list(dict.fromkeys(cleaned_numbers))

    if len(cleaned_numbers) > 0:
        result_text = '\n'.join(cleaned_numbers)
        update.message.reply_text("Твои телефонные номера:\n"+result_text)
        logger.info(f"User {user.full_name}(id={user.id}) find {len(cleaned_numbers)} phone numbers")

        data_json = { "type":"phone_yes", "used_id": user.id, "data": list(cleaned_numbers) }
        json_str = json.dumps(data_json)

        context.user_data[f"phone_{user.id}"] = json_str

        keyboard = [
            [
                InlineKeyboardButton("ДА", callback_data='phone_yes'),
                InlineKeyboardButton("НЕТ", callback_data='phone_no')
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('Добавить номера в БД?', reply_markup=reply_markup)

    else:
        update.message.reply_text("Телефоны в тексте не найдены")
        logger.info(f"User {user.full_name}(id={user.id}) don't find phone numbers")

    return ConversationHandler.END


def buttons(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    query = update.callback_query
    query.answer()

    # Получаю данные из callback_data
    choice = query.data
    # Отправляю пользователю ответ о выборе и результате
    if choice == 'phone_yes':
        user_data = json.loads(context.user_data.get(f"phone_{user.id}"))
        query.edit_message_text("Вы выбрали: Добавить")
        logger.info(f"User {user.full_name}(id={user.id}) choice add phone to DB")
        query.message.reply_text(db_bot_request(update,context,'insert_phones',user_data["data"]))
        context.user_data.clear()
    elif choice == 'phone_no':
        query.edit_message_text(text="Вы выбрали: Не добавлять")
        logger.info(f"User {user.full_name}(id={user.id}) choice don't add phones to DB")
    elif choice == 'email_yes':
        user_data = json.loads(context.user_data.get(f"email_{user.id}"))
        query.edit_message_text("Вы выбрали: Добавить")
        logger.info(f"User {user.full_name}(id={user.id}) choice add email to DB")
        txt_str = db_bot_request(update, context, 'insert_emails', user_data["data"])
        query.message.reply_text(txt_str)
        context.user_data.clear()
    elif choice == 'email_no':
        query.edit_message_text(text="Вы выбрали: Не добавлять")
        logger.info(f"User {user.full_name}(id={user.id}) choice don't add emails to DB")

# Процедура вывода номер телефона из БД
def db_bot_request(update: Update, context, query, insert=[]):
    user = update.effective_user
    result_text = ''
    connection = None # Определяю переменную коннекта т.к. использую finally
    sg = '\'' # Это необходимо потому что для python 3.8 в f-строках нельзя использовать обратный слэш

    dict_query = {'get_phone_numbers':["select", "phone numbers", "Твои телефонные номера из БД:",
                                       f"SELECT * FROM phones WHERE id_user='{user.id}'"],
                  'get_emails':["select", "emails", "Твои email'ы из БД:",
                                       f"SELECT * FROM emails WHERE id_user='{user.id}'"],
                  'insert_phones': ["insert", "phones", "Телефоны добавлены в БД",
                                 f"INSERT INTO phones (phone,id_user) VALUES {','.join('('+str(item)+','+str(user.id)+')' for item in insert)}"],
                  'insert_emails': ["insert", "emails", "Email'ы добавлены в БД",
                                    f"INSERT INTO emails (email,id_user) VALUES {','.join(f'({sg}{str(item)}{sg},{sg}{str(user.id)}{sg})' for item in insert)}"]
                  }

    try:
        connection = psycopg2.connect(user=PG_USER,
                                      password=PG_PASSWD,
                                      host=PG_HOST,
                                      port=PG_PORT,
                                      database=PG_DB)

        cursor = connection.cursor()

        cursor.execute(dict_query[query][3])

        if (dict_query[query][0]=='select'):
            data = cursor.fetchall()
            for row in data:
                result_text = result_text + '\n' + row[1]
            logger.info(f"User {user.full_name}(id={user.id}) {dict_query[query][0]} {dict_query[query][1]} from DB")
            return (f"{dict_query[query][2]}{result_text}")
        elif (dict_query[query][0]=='insert'):
            connection.commit()
            logger.info(f"User {user.full_name}(id={user.id}) {dict_query[query][0]} {dict_query[query][1]} to DB")
            return (f"{dict_query[query][2]}")
    except (Exception, Error) as error:
        logger.info(f"User {user.full_name}(id={user.id}) get error from PostgreSQL, {error}")
        return (f"Ошибка при работе с PostgreSQL: {error}")
    finally:
        if connection is not None:
          cursor.close()
          connection.close()

    return ConversationHandler.END

# Процедура поиска email'ов в тексте
def find_email(update: Update, context):
    user = update.effective_user
    text = update.message.text

    # Регулярное выражение для поиска email'ов
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    emails = []
    for match in re.finditer(email_pattern, text):
        emails.append(match.group())
    emails = list(dict.fromkeys(emails))

    if len(emails) > 0:
        result_text = '\n'.join(emails)
        update.message.reply_text("Твои email'ы:\n"+result_text)
        logger.info(f"User {user.full_name}(id={user.id}) find {len(emails)} emails")

        # JSON строка которая будет содержать тип запроса пользователя, его id и emailы
        data_json = {"type": "email_yes", "used_id": user.id, "data": list(emails)}
        json_str = json.dumps(data_json)

        # В контекст пользователя записываю данные json для добавления данных
        context.user_data[f"email_{user.id}"] = json_str

        # Вывод кнопок пользователю для добавления данных или отказа
        keyboard = [
            [
                InlineKeyboardButton("ДА", callback_data='email_yes'),
                InlineKeyboardButton("НЕТ", callback_data='email_no')
            ]
        ]

        # Описываю сообщение-запрос пользователю с уточнением
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Добавить email'ы в БД?", reply_markup=reply_markup)

    else:
        update.message.reply_text("Email'ы в тексте не найдены")
        logger.info(f"User {user.full_name}(id={user.id}) don't find emails")

    return ConversationHandler.END

# Процедура проверки паролей
def verify_password(update: Update, context):
    user = update.effective_user
    password = update.message.text

    # Регулярные выражения по критериям
    pattern = re.compile(
        r'^(?=.*[A-Z])'  # Наличие заглавной буквы
        r'(?=.*[a-z])'  # Наличие строчной буквы
        r'(?=.*\d)'  # Наличие цифры
        r'(?=.*[!@#$%^&*()])'  # Наличие спецсимфола
        r'.{8,}$'  # Восемь символов
    )

    if (pattern.match(password)):
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")

    logger.info(f"User {user.full_name}(id={user.id}) check password")

    return ConversationHandler.END

# Процедура обработки поиска информации для /get_* по SSH командам
# Можно вернуть .help - список команд и их описание.
# Можно вернуть .list - для проверок наличия валидных команд
# И основное это вернуть SSH команду по каоманде для бота
def ssh_command_funct():
    # Собираем структур {'<бот команда>':['<Описание команды help>', <SSH команда>]}
    dict_command={'/get_release':['Вывести релиз',
                                  '''cat /etc/*-release | grep DISTRIB_DESCRIPTION | sed 's/.*="\(.*\)"/\\1/' '''],
            '/get_uname': ['Архитектура процессора, имя хоста, версии ядра',
                           '''echo -n "Processor: " && uname -p && echo -n "Hostname: " && uname -n && echo -n "Arch: " && uname -v '''],
            '/get_uptime': ['Uptime системы',
                            '''echo -n 'Time: ' && uptime -p '''],
            '/get_df': ['Состояние файловой системы',
                        '''df -h | awk \'NR==1 {next} {print "FS: "$1"\\nSize: "$2"\\nUsed:\
"$3", Avail: "$4"\\nUse%: "$5"\\nMount: "$6"\\n"}' '''],
            '/get_free': ['Состояние памяти',
                          '''free -h | awk 'NR==1 {next} {print ""$1" \\ntotal: "$2"\\nused: "$3", free: "$4"\\n\
shared: "$5"\\nbuff: "$6"\\navailable: "$7"\\n"}' '''],
            '/get_mpstat': ['Состояние производительности',
                            ''' mpstat | awk '/^CPU/ {head} /^[0-9]/ \
            {print $3"\t"$4"\t"$5"\t"$6"\t"$7"\t"$8"\t"$9"\t"$10"\t"$11"\t"$12"\t"$13}' \
            | awk 'NR==1 {next} {print "CPU: "$1"\\n%usr: "$2"\\n%nice: "$3"\\n%sys: "$4"\\n%iowain: "$5"\\n%irq: "$6"\
\\n%soft: "$7"\\n%steal: "$8"\\n%guest: "$9"\\n%gnice: "$10"\\n%idle: "$11}' '''],
            '/get_w': ['Текущие пользователи',
                       ''' w -h | awk '!seen[$1, $3, $4]++ {print "username: \
"$1"\\nfrom: "$3"\\nlog in: "$4"\\n"}' '''],
            '/get_auths': ['Последние 10 входов в систему',
                           ''' last -n 10 |grep -vE '^(reboot|system boot|wtmp begins|down|gone|^$)' \
            | awk '{print "user: "$1"\\nfrom :"$3"\\nat: "$7"\\n"}' '''],
            '/get_critical': ['Последние 5 критических ошибок','''journalctl -p crit -n 5 '''],
            '/get_ps': ['Запущенные процессы',
                        '''ps | awk 'NR==1 {next} {print "pid: "$1"\\ncmd: "$4"\\n"}' '''],
            '/get_ss': ['Используемые порты','''ss -tuln4 | awk 'NR==1 {next} !seen[$1,$5]++ {print "type: "$1; split($5,a,":"); \
            print "adress: "a[1]"\\nport: "a[2]"\\n"}' '''],
            '/get_app_list': ['Список пакетов (/get_app_list <имя пакета> - информация о пакете','''dpkg --get-selections \
            | awk 'NR==0 {next} !seen[$1]++ {print $1}' '''],
            '/get_services':['Запущенные сервисы','''service --status-all | awk 'NR==0 {next} { if ($2 == "+") print $4}' '''],
            '/get_repl_logs':['Логи репликации','''sudo docker logs ''' + PG_HOST + ''' |& grep "replication" \
            | awk 'NR==0 {next} {print "date: "$1"\\ntime: "$2" "$3} {for (i=6; i<=NF; i++) printf "%s ", $i} {printf "\\n\\n"}' '''],
	    '/get_help': ['Вызывает справку по ssh запросам']
        }

    # для .list список ключей (они же команды)
    def get_list():
        return list(dict_command.keys())

    # для .help вернем список команд и их описание
    def get_list_help():
        return "\n".join([f"{key} - {dict_command[key][0]}" for key in dict_command])

    # Возвращаем SSH команду для выполнения
    def get_ssh_command(req):
        return dict_command[req][1]

    # Определение методов
    get_ssh_command.list = get_list
    get_ssh_command.help = get_list_help

    return get_ssh_command

# Обработчик выполнения команд бота для запросов по SSH
def ssh_chek_command(update: Update, context):
    user = update.effective_user
    text = update.message.text
    wrapp_ssh = ssh_command_funct() # определили для формирования ssh команд
    if (text == '/get_help'):
        update.message.reply_text(wrapp_ssh.help()) # возвращаем список команд с описанием по /get_help
        logger.info(f"User {user.full_name}(id={user.id}) get ssh /get_help command")
    elif (re.search(r"/get_app_list .+",text)): # обработаем более убодный вариант /get_app_list <имя пакета>
        list_app = text.split()[1:]
        send_long_message(update, ssh_chek('dpkg -s '+' '.join(list_app),user))
        logger.info(f"User {user.full_name}(id={user.id}) get ssh command - /get_app_list {list_app}")
    elif (text == '/get_phone_numbers'): # Обработка /get_phone_numbers
        logger.info(f"User {user.full_name}(id={user.id}) get command /get_phone_numbers")
        send_long_message(update, db_bot_request(update,context,'get_phone_numbers'))
    elif (text == '/get_emails'):  # Обработка /get_emails
        logger.info(f"User {user.full_name}(id={user.id}) get command /get_emails")
        send_long_message(update, db_bot_request(update, context, 'get_emails'))
    elif (text in wrapp_ssh.list()): # Обработка команд /get_*
        ssh_command = wrapp_ssh(text)
        send_long_message(update, ssh_chek(ssh_command,user))
        logger.info(f"User {user.full_name}(id={user.id}) get ssh command - {text}")
    else: # Ошибка если комыды /get_* не найдено
        update.message.reply_text('Команда не найдена. /help поможет')
        logger.warning(f"User {user.full_name}(id={user.id}) get unknown ssh command, replace /get_help message")
    return ConversationHandler.END

# Процедура выполнения SSH команды на сервере
def ssh_chek(command,tg_user):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD, port=SSH_PORT)
    try:
        stdin, stdout, stderr = client.exec_command(command)
    except Exception as e:
        logger.error()
    data = stdout.read() + stderr.read()
    client.close()
    if (data):
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        logger.info(f"User {tg_user.full_name}(id={tg_user.id}) get ssh command data")
    else:
        data = "Не нашлось данных"
        logger.warning(f"User {tg_user.full_name}(id={tg_user.id}) ssh command not data")

    return data

# Процедура разбиения сообщения на несколько из-за ограничений telegram
def split_text(text, max_length=4096):
    parts = []
    current_part = ""

    # Разбиваем с учетом перехода строки
    for line in text.split('\n'):
        while len(line) > max_length:
            part = line[:max_length]
            line = line[max_length:]
            parts.append(part)

        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line
        else:
            if current_part:
                current_part += "\n"
            current_part += line

    if current_part:
        parts.append(current_part)

    return parts


# Функция для отправки длинного сообщения
def send_long_message(update: Update, text, max_length=4096):
    parts = split_text(text, max_length)
    for part in parts:
        update.message.reply_text(part)

# Обработка ошибки в логировании
def error(update, context):
    logger.warning(f"User {update.effective_user.full_name}(id={update.effective_user.id}) send command \
{update.message.text}. Error: {context.error}")
    update.message.reply_text('Внутренняя ошибка бота, обратитесь к администратору')

def main():

    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик find_phone_number
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_number_command)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
        },
        fallbacks=[]
    )

    # Обработчик find_email
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
        },
        fallbacks=[]
    )
    # Обработчик verify_password
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    # Обработчик для /get_app_list где у пользователя спрашивают про подробности о пакете
    # convHandlerGetAppList = ConversationHandler(
    #     entry_points=[CommandHandler('get_app_list', get_app_list_command)],
    #     states={
    #         'get_app_list': [MessageHandler(Filters.text & ~Filters.command, get_app_list)],
    #     },
    #     fallbacks=[]
    # )

    # Обработчик для /get_*, по паттерну проверяем get_ команды для SSH
    get_command = range(1)
    get_command_pattern = re.compile(r'/get_.+')
    convHandlerGetSSH = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(get_command_pattern),ssh_chek_command)
        ],
        states={
            get_command: [MessageHandler(Filters.text & ~Filters.command, ssh_chek_command)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    # Регистрация обработчика /get_app_list с диалогом пользователя
    #dp.add_handler(convHandlerGetAppList)
    dp.add_handler(convHandlerGetSSH)

    # Обработчик ответа пользователя по внопке
    dp.add_handler(CallbackQueryHandler(buttons))

    # Регистрируем обработчик если не было команды
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, without_command))

    # Обработка ошибки в лог
    dp.add_error_handler(error)

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
