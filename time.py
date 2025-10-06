import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import pyautogui
import time
import os
import json
import pyperclip  # Для работы с буфером обмена

# Словарь перевода должностей (полный словарь как выше)
ROLE_TRANSLATION = {
    "атмосферный техник": "JobAtmosphericTechnician",
    "бармен": "JobBartender",
    "киборг": "JobBorg",
    "ботаник": "JobBotanist",
    "боксёр": "JobBoxer",
    "капитан": "JobCaptain",
    "грузчик": "JobCargoTechnician",
    "представитель центком": "JobCentralCommandOfficial",
    "священник": "JobChaplain",
    "шеф-повар": "JobChef",
    "химик": "JobChemist",
    "старший инженер": "JobChiefEngineer",
    "главный врач": "JobChiefMedicalOfficer",
    "клоун": "JobClown",
    "детектив": "JobDetective",
    "бригмедик": "JobBrigmedic",
    "священник обр": "JobERTChaplain",
    "инженер обр": "JobERTEngineer",
    "уборщик обр": "JobERTJanitor",
    "лидер обр": "JobERTLeader",
    "медик обр": "JobERTMedical",
    "офицер безопасности обр": "JobERTSecurity",
    "глава персонала": "JobHeadOfPersonnel",
    "глава службы безопасности": "JobHeadOfSecurity",
    "уборщик": "JobJanitor",
    "адвокат": "JobLawyer",
    "библиотекарь": "JobLibrarian",
    "врач": "JobMedicalDoctor",
    "интерн": "JobMedicalIntern",
    "мим": "JobMime",
    "музыкант": "JobMusician",
    "парамедик": "JobParamedic",
    "пассажир": "JobPassenger",
    "психолог": "JobPsychologist",
    "квартирмейстер": "JobQuartermaster",
    "репортёр": "JobReporter",
    "научный ассистент": "JobResearchAssistant",
    "научный руководитель": "JobResearchDirector",
    "утилизатор": "JobSalvageSpecialist",
    "учёный": "JobScientist",
    "кадет сб": "JobSecurityCadet",
    "офицер сб": "JobSecurityOfficer",
    "сервисный работник": "JobServiceWorker",
    "станционный ии": "JobStationAi",
    "инженер": "JobStationEngineer",
    "технический ассистент": "JobTechnicalAssistant",
    "посетитель": "JobVisitor",
    "смотритель": "JobWarden",
    "зоотехник": "JobZookeeper"
}

# Словарь вариантов написания единиц времени
TIME_UNITS = {
    "ч": ["ч", "Ч", "h", "H", "час", "часов"],
    "м": ["м", "М", "m", "M", "мин", "минут", "минуты"],
    "с": ["с", "С", "s", "S", "сек", "секунд", "секунды"]
}


def find_tesseract():
    """Поиск Tesseract в стандартных местах"""
    paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract"
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def setup_tesseract():
    """Настройка пути к Tesseract"""
    try:
        pytesseract.get_tesseract_version()
        return True
    except EnvironmentError:
        tesseract_path = find_tesseract()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            return True
        return False


def preprocess_image(image):
    """Предварительная обработка изображения для улучшения распознавания"""
    # Увеличение контрастности
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Преобразование в черно-белое
    image = image.convert('L')

    # Применение фильтра для увеличения резкости
    image = image.filter(ImageFilter.SHARPEN)

    # Бинаризация (пороговая обработка)
    threshold = 150
    image = image.point(lambda p: 255 if p > threshold else 0)

    return image


def normalize_role(role_str):
    """Нормализует строку должности для поиска в словаре"""
    role_str = role_str.lower().replace('ё', 'е').replace('.', '').strip()
    return role_str


def normalize_time_unit(unit):
    """Нормализует единицу времени"""
    unit = unit.lower().strip()

    # Ищем единицу в словаре вариантов
    for standard_unit, variants in TIME_UNITS.items():
        if unit in variants:
            return standard_unit

    return unit


def time_to_seconds(time_str):
    """Конвертирует строку времени в секунды с поддержкой разных форматов"""
    total_seconds = 0

    # Очищаем строку от лишних пробелов
    time_str = time_str.strip()

    # Обработка формата "число число+единица" (например, "164 40m")
    # Ищем шаблон: число [пробел] число+единица
    double_num_match = re.match(r'^(\d+)\s+(\d+)(\w+)$', time_str)
    if double_num_match:
        num1 = int(double_num_match.group(1))
        num2 = int(double_num_match.group(2))
        unit = normalize_time_unit(double_num_match.group(3))

        # Интерпретация зависит от единицы измерения
        if unit == 'ч':
            # Оба числа в часах (например, "164 40ч" = 164 часа + 40 часов)
            total_seconds += (num1 + num2) * 3600
        elif unit == 'м':
            # Первое число - часы, второе - минуты (например, "164 40м" = 164 часа + 40 минут)
            total_seconds += num1 * 3600 + num2 * 60
        elif unit == 'с':
            # Первое число - часы, второе - секунды (например, "164 40с" = 164 часа + 40 секунд)
            total_seconds += num1 * 3600 + num2
        return total_seconds

    # Обработка формата без пробелов (например, "16ч4м")
    # Ищем шаблон: число+единица число+единица
    compact_match = re.match(r'^(\d+)(\w+)(\d+)(\w+)$', time_str)
    if compact_match:
        num1 = int(compact_match.group(1))
        unit1 = normalize_time_unit(compact_match.group(2))
        num2 = int(compact_match.group(3))
        unit2 = normalize_time_unit(compact_match.group(4))

        # Обрабатываем первое число
        if unit1 == 'ч':
            total_seconds += num1 * 3600
        elif unit1 == 'м':
            total_seconds += num1 * 60
        elif unit1 == 'с':
            total_seconds += num1

        # Обрабатываем второе число
        if unit2 == 'ч':
            total_seconds += num2 * 3600
        elif unit2 == 'м':
            total_seconds += num2 * 60
        elif unit2 == 'с':
            total_seconds += num2

        return total_seconds

    # Обработка формата с явными единицами (например, "166ч 40м")
    # Ищем все пары число+единица
    time_parts = re.findall(r'(\d+)\s*(\w+)', time_str)

    for num_str, unit in time_parts:
        num = int(num_str)
        unit = normalize_time_unit(unit)

        if unit == 'ч':
            total_seconds += num * 3600
        elif unit == 'м':
            total_seconds += num * 60
        elif unit == 'с':
            total_seconds += num

    # Если не найдено ни одной единицы, но есть числа, предполагаем что это минуты
    if total_seconds == 0:
        numbers = re.findall(r'(\d+)', time_str)
        if numbers:
            # Берем последнее найденное число как минуты
            total_seconds = int(numbers[-1]) * 60

    return total_seconds


def process_text(text, player_nickname):
    """Обрабатывает текст и генерирует команды"""
    commands = []

    # Разделение текста на строки
    lines = text.split('\n')

    # Обрабатываем каждую строку
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Ищем время в строке - улучшенное регулярное выражение
        time_match = re.search(r'((?:\d+\s*\w+\s*)+|\d+\s+\d+\s*\w+|\d+\w+\d+\w+|\d+\s*\w+|\d+\s+\d+)', line)
        if not time_match:
            continue

        time_str = time_match.group(1)
        role_str = line.replace(time_str, '').strip()

        # Конвертация времени
        seconds = time_to_seconds(time_str)
        if seconds == 0:
            continue

        # Перевод должности
        normalized_role = normalize_role(role_str)
        role_en = ROLE_TRANSLATION.get(normalized_role)
        if not role_en:
            print(f"Неизвестная должность: {role_str}")
            continue

        # Формирование команды
        command = f"playtime_addrole {player_nickname} {role_en} {seconds}"
        commands.append(command)
        print(f"Сгенерирована команда: {command}")
        print(f"  Время: {time_str} -> {seconds} секунд")

    return commands


def process_image(image_path, player_nickname):
    """Обрабатывает изображение и генерирует команды"""
    try:
        # Открываем и обрабатываем изображение
        image = Image.open(image_path)
        processed_image = preprocess_image(image)

        # Распознавание текста с улучшенными параметрами
        custom_config = r'--oem 3 --psm 6 -l rus+eng'
        text = pytesseract.image_to_string(processed_image, config=custom_config)

        return text, process_text(text, player_nickname)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обработать изображение: {str(e)}")
        return "", []


class SettingsDialog(tk.Toplevel):
    """Диалог настроек выполнения команд"""

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Настройки выполнения команд")
        self.geometry("400x300")
        self.settings = settings.copy()
        self.result = None

        # Создаем интерфейс
        self.create_widgets()

    def create_widgets(self):
        # Задержки
        delay_frame = tk.Frame(self)
        delay_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(delay_frame, text="Задержка между командами (сек):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cmd_delay_var = tk.StringVar(value=str(self.settings.get('command_delay', 1.0)))
        cmd_delay_entry = tk.Entry(delay_frame, textvariable=self.cmd_delay_var, width=10)
        cmd_delay_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        tk.Label(delay_frame, text="Задержка перед Enter (сек):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.enter_delay_var = tk.StringVar(value=str(self.settings.get('enter_delay', 0.5)))
        enter_delay_entry = tk.Entry(delay_frame, textvariable=self.enter_delay_var, width=10)
        enter_delay_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Способ ввода
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(input_frame, text="Способ ввода команд:").pack(side=tk.LEFT, padx=5)
        self.input_method_var = tk.StringVar(value=self.settings.get('input_method', 'clipboard'))
        tk.Radiobutton(input_frame, text="Буфер обмена", variable=self.input_method_var, value='clipboard').pack(
            side=tk.LEFT, padx=5)
        tk.Radiobutton(input_frame, text="Прямой ввод", variable=self.input_method_var, value='direct').pack(
            side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="Сохранить", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def save_settings(self):
        try:
            self.settings['command_delay'] = float(self.cmd_delay_var.get())
            self.settings['enter_delay'] = float(self.enter_delay_var.get())
            self.settings['input_method'] = self.input_method_var.get()
            self.result = self.settings
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Неверное значение задержки")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор команд для должностей")
        self.root.geometry("1000x700")

        # Переменные
        self.commands = []
        self.execution_in_progress = False
        self.current_command_index = 0

        # Настройки по умолчанию
        self.settings = {
            'command_delay': 1.0,
            'enter_delay': 0.5,
            'input_method': 'clipboard'  # 'clipboard' или 'direct'
        }

        # Элементы интерфейса
        # Верхняя панель с вводом ника и выбором файла
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(top_frame, text="Ник игрока:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.nickname_entry = tk.Entry(top_frame, width=30)
        self.nickname_entry.grid(row=0, column=1, padx=5)

        tk.Button(top_frame, text="Выбрать изображение", command=self.select_image).grid(row=0, column=2, padx=5)
        tk.Button(top_frame, text="Настройки", command=self.open_settings).grid(row=0, column=3, padx=5)

        # Путь к файлу
        self.image_path_var = tk.StringVar()
        tk.Label(top_frame, textvariable=self.image_path_var, wraplength=500).grid(row=1, column=0, columnspan=4,
                                                                                   sticky=tk.W, padx=5)

        # Кнопки генерации
        button_frame = tk.Frame(top_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)

        tk.Button(button_frame, text="Сгенерировать команды из изображения", command=self.generate_from_image,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Пересобрать команды из текста", command=self.generate_from_text, bg="#2196F3",
                  fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Редактировать должности", command=self.edit_roles).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Редактировать единицы времени", command=self.edit_time_units).pack(side=tk.LEFT,
                                                                                                         padx=5)

        # Поле с распознанным текстом
        debug_frame = tk.LabelFrame(root, text="Распознанный текст (можно редактировать)", padx=5, pady=5)
        debug_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.debug_text = scrolledtext.ScrolledText(debug_frame, height=10, width=80)
        self.debug_text.pack(fill=tk.BOTH, expand=True)

        # Поле с командами
        commands_frame = tk.LabelFrame(root, text="Сгенерированные команды", padx=5, pady=5)
        commands_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.commands_listbox = tk.Listbox(commands_frame, height=10, width=80)
        self.commands_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(commands_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.commands_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.commands_listbox.yview)

        # Нижняя панель с кнопками выполнения
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=10, padx=10, fill=tk.X)

        # Кнопки выполнения
        self.execute_button = tk.Button(bottom_frame, text="Выполнить все команды", command=self.start_execution,
                                        bg="#FF9800", fg="white")
        self.execute_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(bottom_frame, text="Остановить", command=self.stop_execution, state=tk.DISABLED,
                                     bg="#F44336", fg="white")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Информация о настройках
        input_method_text = "Буфер обмена" if self.settings['input_method'] == 'clipboard' else "Прямой ввод"
        self.info_label = tk.Label(bottom_frame, text=f"Способ ввода: {input_method_text}")
        self.info_label.grid(row=0, column=2, padx=10)

        # Статус выполнения
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.image_path_var.set(file_path)

    def generate_from_image(self):
        nickname = self.nickname_entry.get().strip()
        image_path = self.image_path_var.get()

        if not nickname:
            messagebox.showwarning("Предупреждение", "Введите ник игрока")
            return

        if not image_path:
            messagebox.showwarning("Предупреждение", "Выберите изображение")
            return

        self.status_var.set("Обработка изображения...")
        self.root.update()

        text, commands = process_image(image_path, nickname)

        # Выводим распознанный текст в отладочное поле
        self.debug_text.delete(1.0, tk.END)
        self.debug_text.insert(tk.END, text)

        if not commands:
            messagebox.showinfo("Информация", "Не удалось распознать команды на изображении")
            self.status_var.set("Готов к работе")
            return

        self.commands = commands

        # Очищаем список и добавляем команды
        self.commands_listbox.delete(0, tk.END)
        for i, cmd in enumerate(self.commands, 1):
            self.commands_listbox.insert(tk.END, f"{i}. {cmd}")

        self.status_var.set(f"Сгенерировано команд: {len(self.commands)}")

    def generate_from_text(self):
        nickname = self.nickname_entry.get().strip()
        text = self.debug_text.get(1.0, tk.END).strip()

        if not nickname:
            messagebox.showwarning("Предупреждение", "Введите ник игрока")
            return

        if not text:
            messagebox.showwarning("Предупреждение", "Нет текста для обработки")
            return

        self.status_var.set("Обработка текста...")
        self.root.update()

        self.commands = process_text(text, nickname)

        if not self.commands:
            messagebox.showinfo("Информация", "Не удалось распознать команды в тексте")
            self.status_var.set("Готов к работе")
            return

        # Очищаем список и добавляем команды
        self.commands_listbox.delete(0, tk.END)
        for i, cmd in enumerate(self.commands, 1):
            self.commands_listbox.insert(tk.END, f"{i}. {cmd}")

        self.status_var.set(f"Сгенерировано команд: {len(self.commands)}")

    def open_settings(self):
        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog)

        if dialog.result:
            self.settings = dialog.result
            input_method_text = "Буфер обмена" if self.settings['input_method'] == 'clipboard' else "Прямой ввод"
            self.info_label.config(text=f"Способ ввода: {input_method_text}")

    def edit_roles(self):
        # Здесь можно добавить диалог для редактирования должностей
        messagebox.showinfo("Информация", "Функция редактирования должностей в разработке")

    def edit_time_units(self):
        # Здесь можно добавить диалог для редактирования единиц времени
        messagebox.showinfo("Информация", "Функция редактирования единиц времени в разработке")

    def start_execution(self):
        if not self.commands:
            messagebox.showwarning("Предупреждение", "Сначала сгенерируйте команды")
            return

        if self.execution_in_progress:
            return

        # Показываем инструкцию
        input_method_text = "через буфер обмена (Ctrl+V)" if self.settings[
                                                                 'input_method'] == 'clipboard' else "прямым вводом"
        messagebox.showinfo("Выполнение команд",
                            f"1. Наведите курсор на командную строку\n"
                            f"2. Нажмите ОК\n"
                            f"3. Все команды будут выполнены автоматически {input_method_text}")

        # Начинаем выполнение
        self.execution_in_progress = True
        self.current_command_index = 0
        self.execute_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Ожидание начала выполнения...")

        # Запускаем выполнение в отдельном потоке, чтобы не блокировать интерфейс
        self.root.after(1000, self.execute_all_commands)

    def execute_all_commands(self):
        if not self.execution_in_progress:
            return

        # Выполняем команды по очереди
        for i, cmd in enumerate(self.commands):
            if not self.execution_in_progress:
                break

            # Обновляем статус
            self.status_var.set(f"Выполнение команды {i + 1}/{len(self.commands)}: {cmd}")
            self.commands_listbox.selection_clear(0, tk.END)
            self.commands_listbox.selection_set(i)
            self.commands_listbox.see(i)
            self.root.update()

            # Выбираем способ ввода
            if self.settings['input_method'] == 'clipboard':
                # Копируем команду в буфер обмена
                pyperclip.copy(cmd)

                # Небольшая задержка для надежности
                time.sleep(0.1)

                # Вставляем из буфера обмена (Ctrl+V)
                pyautogui.hotkey('ctrl', 'v')
            else:
                # Прямой ввод команды
                pyautogui.write(cmd)

            # Задержка перед нажатием Enter
            time.sleep(self.settings['enter_delay'])

            # Нажимаем Enter
            pyautogui.press('enter')

            # Задержка между командами
            time.sleep(self.settings['command_delay'])

        # Завершение выполнения
        self.stop_execution()
        messagebox.showinfo("Завершено", "Все команды выполнены!")

    def stop_execution(self):
        self.execution_in_progress = False
        self.current_command_index = 0

        self.execute_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Выполнение остановлено")


if __name__ == "__main__":
    # Настройка Tesseract
    if not setup_tesseract():
        messagebox.showerror(
            "Ошибка Tesseract",
            "Tesseract OCR не установлен или не найден!\n\n"
            "Пожалуйста, установите Tesseract OCR:\n"
            "1. Скачайте с https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. Установите программу\n"
            "3. Перезапустите это приложение"
        )
        exit(1)

    # Устанавливаем pyperclip, если не установлен
    try:
        import pyperclip
    except ImportError:
        import subprocess
        import sys

        messagebox.showinfo("Установка зависимости",
                            "Устанавливаем библиотеку pyperclip для работы с буфером обмена...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
        import pyperclip

    root = tk.Tk()
    app = App(root)
    root.mainloop()