import telebot
from telebot import types
import pandas as pd
import os
import random
import string
from datetime import datetime

# Инициализация бота
bot = telebot.TeleBot('YOUR_TOKEN')

# Создание DataFrame для хранения информации о сотрудниках
data = pd.DataFrame(columns=['ID', 'Фамилия', 'Имя', 'Отчество','Должность', 'Проект', 'Дата прихода', 'Аватарка'])

# Папка для хранения аватарок
avatar_folder = 'Avatars'

csv_file_path = 'employees.csv'

# Проверка наличия папки для аватарок
if not os.path.exists(avatar_folder):
    os.makedirs(avatar_folder)
    

def write_dataframe_to_csv(dataframe):
    try:
        dataframe.to_csv(csv_file_path, index=False)
    except FileNotFoundError:
        # Если файл не существует, создаем его и сохраняем данные
        dataframe.to_csv(csv_file_path, index=False)

def read_csv_to_dataframe():
    try:
        dataframe = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        # Если файл не существует, создаем его и возвращаем пустой DataFrame
        dataframe = pd.DataFrame(columns=['ID', 'Фамилия', 'Имя', 'Отчество', 'Должность', 'Проект', 'Дата прихода', 'Аватарка'])
        dataframe.to_csv(csv_file_path, index=False)
    return dataframe


# Генерация уникального ID для сотрудника
def generate_employee_id():
    now = datetime.now()
    date_part = now.strftime("%d%m%y%H%M")
    random_part = str(random.randint(10, 99))
    return date_part + random_part


def show_cancel_button(message, text="Выберите действие:"):
    keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data="cancel")
    keyboard.add(cancel_button)
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

# Функция для отображения клавиатуры с кнопками
def show_keyboard(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_search = telebot.types.KeyboardButton("Поиск")
    item_add = telebot.types.KeyboardButton("Добавить")
    item_delete = telebot.types.KeyboardButton("Удалить")
    item_edit = telebot.types.KeyboardButton("Редактировать")
    markup.row(item_search, item_add)
    markup.row(item_delete, item_edit)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Вы в главном меню.")
    show_keyboard(message)
    

# Обработчик для обработки инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "search":
        search_employee(call.message)
    elif call.data == "add":
        add_employee(call.message)
    elif call.data == "delete":
        delete_employee(call.message)
    elif call.data == "edit":
        edit_employee(call.message)
    elif call.data == "cancel":
        start(call.message)


# Обработчик команды /add
@bot.message_handler(func=lambda message: message.text == "Добавить")
def add_employee(message):
    bot.send_message(message.chat.id, "Введите данные сотрудника в формате: "
                                      "Фамилия Имя Должность Проект Отчество(опционально)")
    bot.register_next_step_handler(message, process_employee_info)


# Обработчик ввода данных сотрудника
def process_employee_info(message):
    try:
        employee_info = list(map(str, message.text.split()))
        if len(employee_info) < 4:
            bot.send_message(message.chat.id, "Неверный формат ввода. Введите данные сотрудника в формате: "
                                              "Фамилия Имя Должность Проект [Отчество]")
            return

        last_name, first_name, position, project = employee_info[:4]
        hire_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        patronymic = None if len(employee_info) < 5 or employee_info[4] == '0' else employee_info[4]

        # Генерация уникального ID для сотрудника
        employee_id = generate_employee_id()

        bot.send_message(message.chat.id, f"Отлично! Теперь загрузите аватарку для сотрудника {first_name} {last_name}. Если не хотите ее загружать введите 0.")

        bot.register_next_step_handler(message, process_employee_avatar, employee_id, last_name, first_name, patronymic, position, project, hire_date)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка.")

# Обработчик загрузки аватарки сотрудника
def process_employee_avatar(message, employee_id, last_name, first_name, patronymic, position, project, hire_date):
    data = read_csv_to_dataframe()
    try:
        if message.photo:
            # Получение файла с аватаркой
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path

            # Генерация имени файла на основе ID сотрудника
            avatar_filename = f"{employee_id}.jpg"
            avatar_file_path = os.path.join(avatar_folder, avatar_filename)

            # Загрузка аватарки и сохранение её с новым именем
            with open(avatar_file_path, 'wb') as avatar_file:
                avatar_file.write(bot.download_file(file_path))

        else:
            # Если аватарка не была загружена, устанавливаем значение None
            avatar_filename = None

        # Добавление информации о сотруднике в DataFrame
        data.loc[len(data)] = [employee_id, last_name, first_name, patronymic, position, project, hire_date, avatar_filename]
        write_dataframe_to_csv(data)
        
        bot.send_message(message.chat.id, "Сотрудник успешно добавлен!")

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при загрузке аватарки.")



# Обработчик команды /search
@bot.message_handler(func=lambda message: message.text == "Поиск")
def search_employee(message):
    bot.send_message(message.chat.id, "Введите фамилию или имя сотрудника для поиска.")
    bot.register_next_step_handler(message, process_search_employee)

# Обработчик поиска сотрудника
def process_search_employee(message):
    query = message.text.lower()
    data = read_csv_to_dataframe()
    data['Фамилия'] = data['Фамилия'].astype(str)
    data['Имя'] = data['Имя'].astype(str)
    result = data[(data['Фамилия'].str.lower().str.contains(query)) | (data['Имя'].str.lower().str.contains(query))]
    if not result.empty:
        bot.send_message(message.chat.id, "Результаты поиска:")
        for _, row in result.iterrows():
            bot.send_message(message.chat.id,f"Фамилия: {row['Фамилия']}\n"
                                             f"Имя: {row['Имя']}\n"
                                             f"Отчество: {row['Отчество']}\n"
                                             f"Должность: {row['Должность']}\n"
                                             f"Проект: {row['Проект']}\n"
                                             f"Дата прихода: {row['Дата прихода']}")
            if not pd.isna(row['Аватарка']) and isinstance(row['Аватарка'], (str, bytes)):
                bot.send_photo(message.chat.id, open(os.path.join(avatar_folder, row['Аватарка']), 'rb'))
            else:
                bot.send_message(message.chat.id, "Аватарка не найдена.")

    else:
        bot.send_message(message.chat.id, "Сотрудники не найдены.")


# Обработчик команды /delete
@bot.message_handler(func=lambda message: message.text == "Удалить")
def delete_employee(message):
    bot.send_message(message.chat.id, "Введите имя и фамилию сотрудника, которого хотите удалить (например, Иван Иванов).")
    bot.register_next_step_handler(message, process_delete_employee)

# Обработчик выбора сотрудника для удаления
def process_delete_employee(message):
    data = read_csv_to_dataframe()
    data['Фамилия'] = data['Фамилия'].astype(str)
    data['Имя'] = data['Имя'].astype(str)
    try:
        full_name = message.text.split()
        if len(full_name) != 2:
            bot.send_message(message.chat.id, "Неверный формат ввода. Введите имя и фамилию сотрудника через пробел (например, Иван Иванов).")
            bot.register_next_step_handler(message, process_delete_employee)

        first_name, last_name = full_name
        print(first_name, last_name)
        result = data[(data['Фамилия'].str.lower()) | (data['Имя'].str.lower())]
        if not result.empty:
            if len(result) > 1:
                bot.send_message(message.chat.id, "Найдено несколько сотрудников с таким именем и фамилией. Выберите сотрудника для удаления по ID:")
                for index, row in result.iterrows():
                    bot.send_message(message.chat.id, f"ID: {row['ID']} Фамилия: {row['Фамилия']} Имя: {row['Имя']}\n"
                                                     f"Должность: {row['Должность']} Проект: {row['Проект']}\n"
                                                     f"Дата прихода: {row['Дата прихода']}\n"
                                                     f"Аватарка: {row['Аватарка']}")
                bot.register_next_step_handler(message, process_select_employee_for_delete, result)
            else:
                # Удаление сотрудника из DataFrame
                data.drop(result.index, inplace=True)
                bot.send_message(message.chat.id, "Сотрудник успешно удален.")
        else:
            bot.send_message(message.chat.id, "Сотрудник с таким именем и фамилией не найден.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте снова.")

# Обработчик выбора сотрудника для удаления
def process_select_employee_for_delete(message, result):
    data = read_csv_to_dataframe()
    try:
        selected_id = int(message.text)
        employee = result[result['ID'] == selected_id]
        if not employee.empty:
            # Удаление сотрудника из DataFrame
            data.drop(employee.index, inplace=True)
            write_dataframe_to_csv(data)
            bot.send_message(message.chat.id, "Сотрудник успешно удален.")
        else:
            bot.send_message(message.chat.id, "Сотрудник с таким ID не найден.")
    except ValueError:
        bot.send_message(message.chat.id, "ID введен не корректно.")


# Обработчик команды /edit
@bot.message_handler(func=lambda message: message.text == "Редактировать")
def edit_employee(message):
    bot.send_message(message.chat.id, "Введите имя и фамилию сотрудника, которого хотите отредактировать (например, Иван Иванов).")
    bot.register_next_step_handler(message, process_edit_employee)

# Обработчик выбора сотрудника для редактирования
def process_edit_employee(message):
    data = read_csv_to_dataframe()
    try:
        full_name = message.text.split()
        if len(full_name) != 2:
            bot.send_message(message.chat.id, "Неверный формат ввода. Введите имя и фамилию сотрудника через пробел (например, Иван Иванов).")
            bot.register_next_step_handler(message, process_edit_employee)

        first_name, last_name = full_name
        result = data[(data['Фамилия'].str.lower()) | (data['Имя'].str.lower())]
        if not result.empty:
            if len(result) > 1:
                bot.send_message(message.chat.id, "Найдено несколько сотрудников с таким именем и фамилией. Выберите сотрудника по ID:")
                for index, row in result.iterrows():
                    bot.send_message(message.chat.id, f"ID: {row['ID']} Фамилия: {row['Фамилия']} Имя: {row['Имя']}\n"
                                                     f"Должность: {row['Должность']} Проект: {row['Проект']}\n"
                                                     f"Дата прихода: {row['Дата прихода']}\n"
                                                     f"Аватарка: {row['Аватарка']}")
                bot.register_next_step_handler(message, process_select_employee_for_edit, result)
            else:
                bot.send_message(message.chat.id, "Выберите, что вы хотите отредактировать:")
                bot.send_message(message.chat.id, "1. Фамилия")
                bot.send_message(message.chat.id, "2. Имя")
                bot.send_message(message.chat.id, "3. Отчество")
                bot.send_message(message.chat.id, "4. Должность")
                bot.send_message(message.chat.id, "5. Проект")
                bot.send_message(message.chat.id, "6. Дата прихода")
                bot.send_message(message.chat.id, "7. Аватарка")
                bot.send_message(message.chat.id, "8. Главное меню")
                bot.register_next_step_handler(message, process_edit_employee_option, result)
        else:
            bot.send_message(message.chat.id, "Сотрудник с таким именем и фамилией не найден.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка.")

# Обработчик выбора сотрудника для редактирования
def process_select_employee_for_edit(message, result):
    try:
        selected_id = int(message.text)
        employee = result[result['ID'] == selected_id]
        if not employee.empty:
            bot.send_message(message.chat.id, "Выберите, что вы хотите отредактировать:")
            bot.send_message(message.chat.id, "1. Фамилия")
            bot.send_message(message.chat.id, "2. Имя")
            bot.send_message(message.chat.id, "3. Отчество")
            bot.send_message(message.chat.id, "4. Должность")
            bot.send_message(message.chat.id, "5. Проект")
            bot.send_message(message.chat.id, "6. Дата прихода")
            bot.send_message(message.chat.id, "7. Аватарка")
            bot.send_message(message.chat.id, "8. Главное меню")
            bot.register_next_step_handler(message, process_edit_employee_option, employee)
        else:
            bot.send_message(message.chat.id, "Сотрудник с таким ID не найден.")
    except ValueError:
        bot.send_message(message.chat.id, "ID введен не корректно.")

# Обработчик выбора опции для редактирования сотрудника
def process_edit_employee_option(message, employee):
    try:
        selected_option = int(message.text)
        if 1 <= selected_option <= 7:
            field = 'Фамилия' if selected_option == 1 else 'Имя' if selected_option == 2 else 'Отчество' if selected_option == 3 else \
                'Должность' if selected_option == 4 else 'Проект' if selected_option == 5 else 'Дата прихода' if selected_option == 6 else 'Аватарка'

            if selected_option == 7:
                bot.send_message(message.chat.id, "Загрузите новую аватарку:")
                bot.register_next_step_handler(message, process_employee_avatar_edit, employee, field)
            else:
                bot.send_message(message.chat.id, f"Введите новое значение для поля '{field}':")
                bot.register_next_step_handler(message, process_edit_employee_value, employee, field)
        else:
            if selected_option == 8:
                bot.send_message(message.chat.id, "Вы вернулись в главное меню.")
                start(message)
            else:
                bot.send_message(message.chat.id, "Выберите корректную опцию (1-8).")
                bot.register_next_step_handler(message, process_edit_employee_option, employee)
    except ValueError:
        bot.send_message(message.chat.id, "Опция введена не корректно")

# Обработчик ввода нового значения для редактирования сотрудника
def process_edit_employee_value(message, employee, field):
    data = read_csv_to_dataframe()
    new_value = message.text
    data.loc[employee.index[0], field] = new_value
    write_dataframe_to_csv(data)
    bot.send_message(message.chat.id, f"Сотрудник успешно отредактирован. Новое значение для '{field}': {new_value}")
    bot.send_message(message.chat.id, "Выберите, что вы хотите отредактировать:")
    bot.send_message(message.chat.id, "1. Фамилия")
    bot.send_message(message.chat.id, "2. Имя")
    bot.send_message(message.chat.id, "3. Отчество")
    bot.send_message(message.chat.id, "4. Должность")
    bot.send_message(message.chat.id, "5. Проект")
    bot.send_message(message.chat.id, "6. Дата прихода")
    bot.send_message(message.chat.id, "7. Аватарка")
    bot.send_message(message.chat.id, "8. Главное меню")
    bot.register_next_step_handler(message, process_edit_employee_option, employee)

# Обработчик загрузки новой аватарки
def process_employee_avatar_edit(message, employee, field):
    try:
        if message.photo:
            # Получение файла с аватаркой
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path

            # Генерация имени файла на основе ID сотрудника
            avatar_filename = f"{employee['ID'].values[0]}.jpg"
            avatar_file_path = os.path.join(avatar_folder, avatar_filename)

            # Удаление предыдущей аватарки, если она существует
            if os.path.exists(avatar_file_path):
                os.remove(avatar_file_path)

            # Загрузка новой аватарки и сохранение её с новым именем
            with open(avatar_file_path, 'wb') as avatar_file:
                avatar_file.write(bot.download_file(file_path))

            # Обновление информации о сотруднике в DataFrame
            data = read_csv_to_dataframe()
            data.loc[employee.index[0], 'Аватарка'] = avatar_filename
            write_dataframe_to_csv(data)

            bot.send_message(message.chat.id, "Аватарка успешно обновлена!")
        else:
            bot.send_message(message.chat.id, "Вы не загрузили новую аватарку. Попробуйте снова.")
            bot.register_next_step_handler(message, process_employee_avatar, employee, field)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при загрузке аватарки.")


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)


