import os
import shutil
import zipfile
from tkinter import Tk, filedialog, Button, Text, Scrollbar, Frame, END, VERTICAL, BOTH, X, Canvas, Radiobutton, IntVar
import itertools
import threading
import ctypes
import json
import logging
from googletrans import Translator
from tkinter import Toplevel, Listbox, Label, Entry

# Enable High DPI Awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='program.log', filemode='w')

def log(message):
    log_text.insert(END, message + "\n")
    log_text.see(END)
    print(message)
    logging.debug(message)

def select_folder():
    log("Выбор папки...")
    folder_selected = filedialog.askdirectory()
    log(f"Папка выбрана: {folder_selected}")
    return folder_selected

def find_mods_without_ru(folder, log):
    log("Поиск модов без ru_ru...")
    mods_without_ru = []
    try:
        for filename in os.listdir(folder):
            if filename.endswith(".jar"):
                jar_path = os.path.join(folder, filename)
                with zipfile.ZipFile(jar_path, 'r') as jar:
                    lang_folder_exists = any(
                        'assets/' in name and '/lang/' in name
                        for name in jar.namelist()
                    )
                    if not lang_folder_exists:
                        continue
                    contains_ru = any(
                        'assets/' in name and '/lang/ru_ru.json' in name
                        for name in jar.namelist()
                    )
                    if not contains_ru:
                        mods_without_ru.append(filename)
                log(f"Сканирован {filename}")
    except Exception as e:
        log(f"Ошибка при сканировании модов: {e}")
    return mods_without_ru

def copy_mods_to_folder(mods, src_folder, dest_folder, log):
    log("Копирование модов в папку...")
    try:
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        total_files = len(mods)
        for i, mod in enumerate(mods, 1):
            shutil.copy(os.path.join(src_folder, mod), dest_folder)
            log(f"Скопировано {i}/{total_files} ({(i / total_files) * 100:.2f}%)")
    except Exception as e:
        log(f"Ошибка при копировании модов: {e}")

def write_mods_to_file(mods, filepath, log):
    log("Запись модов в файл...")
    try:
        with open(filepath, 'w') as file:
            for mod in mods:
                file.write(f"{mod}\n")
    except Exception as e:
        log(f"Ошибка при записи модов в файл: {e}")

def get_unique_path(base_path):
    if not os.path.exists(base_path):
        return base_path
    base, ext = os.path.splitext(base_path)
    for i in itertools.count(1):
        new_path = f"{base}_{i}{ext}"
        if not os.path.exists(new_path):
            return new_path

def process_mods(log):
    log("Обработка модов...")
    try:
        mods_folder = select_folder()
        if mods_folder:
            log("Папка выбрана: " + mods_folder)
            mods_without_ru = find_mods_without_ru(mods_folder, log)
            unique_mods_folder = get_unique_path('./mods')
            unique_list_file = get_unique_path('./mods_list.txt')
            log("Копирование модов...")
            copy_mods_to_folder(mods_without_ru, mods_folder, unique_mods_folder, log)
            log("Запись списка модов в файл...")
            write_mods_to_file(mods_without_ru, unique_list_file, log)
            log("Обработка завершена. Проверьте созданные папки и файлы.")
    except Exception as e:
        log(f"Ошибка в процессе обработки модов: {e}")

def run_process(log):
    log("Запуск процесса...")
    threading.Thread(target=process_mods, args=(log,)).start()

def translate_text(text, src_lang='en', dest_lang='ru'):
    log(f"Перевод текста с {src_lang} на {dest_lang}: {text}")
    try:
        translator = Translator(from_lang=src_lang, to_lang=dest_lang)
        translation = translator.translate(text)
        if translation is None:
            raise ValueError("Translation returned None")
        log(f"Перевод: {translation}")
        return translation
    except Exception as e:
        log(f"Ошибка при переводе текста: {e}")
        return text
        
def open_translation_editor(mod_path, dest_folder):
    log(f"Открытие редактора перевода для: {mod_path}")
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            en_us_path = [name for name in jar.namelist() if 'lang/en_us.json' in name][0]
            with jar.open(en_us_path) as file:
                original_text = json.load(file)

        translations = {}
        for key, value in original_text.items():
            if key.startswith("a.lang."):
                translations[key] = value
            else:
                translations[key] = translate_text(value)
        
        editor_window = Toplevel(root)
        editor_window.title("Редактор перевода")

        original_label = Label(editor_window, text="Оригинальный текст")
        original_label.grid(row=0, column=0)
        translated_label = Label(editor_window, text="Переведенный текст")
        translated_label.grid(row=0, column=1)

        row = 1
        entries = {}
        for key, value in translations.items():
            Label(editor_window, text=key).grid(row=row, column=0)
            original_entry = Entry(editor_window, width=50)
            original_entry.insert(0, value)
            original_entry.grid(row=row, column=1)
            entries[key] = original_entry
            row += 1

        def save_translation():
            log("Сохранение перевода...")
            try:
                new_translations = {key: entry.get() for key, entry in entries.items()}
                ru_ru_path = en_us_path.replace('en_us.json', 'ru_ru.json')
                with zipfile.ZipFile(mod_path, 'a') as jar:
                    jar.writestr(ru_ru_path, json.dumps(new_translations, ensure_ascii=False, indent=4))
                shutil.copy(mod_path, os.path.join(dest_folder, os.path.basename(mod_path)))
                update_translated_list(os.path.basename(mod_path))
                editor_window.destroy()
            except Exception as e:
                log(f"Ошибка при сохранении перевода: {e}")

        save_button = Button(editor_window, text="Сохранить перевод", command=save_translation)
        save_button.grid(row=row, column=0, columnspan=2)
    except Exception as e:
        log(f"Ошибка при открытии редактора перевода: {e}")

def update_translated_list(mod_name):
    log(f"Обновление списка переведенных модов: {mod_name}")
    try:
        list_path = './translated_mods_list.txt'
        with open(list_path, 'a') as file:
            file.write(f"{mod_name}\n")
    except Exception as e:
        log(f"Ошибка при обновлении списка переведенных модов: {e}")

def scan_mod_files(mods_folder):
    for f in os.listdir(mods_folder):
        if f.endswith(".jar"):
            yield f

def select_mod_for_translation(log):
    log("Выбор мода для перевода...")
    mods_folder = select_folder()
    if not mods_folder:
        return

    mod_files = list(scan_mod_files(mods_folder))
    list_window = Toplevel(root)
    list_window.title("Выбор мода для перевода")
    list_window.geometry("600x600")

    canvas = Canvas(list_window)
    scrollbar = Scrollbar(list_window, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas)

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_configure)

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill=BOTH, expand=True)

    selected_mod = IntVar()
    for idx, mod in enumerate(mod_files):
        radio = Radiobutton(scrollable_frame, text=mod, variable=selected_mod, value=idx)
        radio.pack(anchor='w')
        list_window.update_idletasks()  # Обновление интерфейса

    def on_translate():
        selected_idx = selected_mod.get()
        log(f"Выбранный индекс: {selected_idx}")
        if selected_idx >= 0 and selected_idx < len(mod_files):
            mod_path = os.path.join(mods_folder, mod_files[selected_idx])
            dest_folder = select_folder()
            if not dest_folder:
                dest_folder = os.getcwd()
            open_translation_editor(mod_path, dest_folder)
            list_window.destroy()
        else:
            log("Неверный индекс выбора!")

    translate_button = Button(list_window, text="Перевести", command=on_translate)
    translate_button.pack(side="top", anchor="ne", padx=10, pady=10)

def main():
    global root, log_text
    root = Tk()
    root.title("Переводчик модов для Minecraft")

    frame_buttons = Frame(root)
    frame_buttons.pack(side='top', fill=X)

    frame_console = Frame(root)
    frame_console.pack(side='bottom', fill=BOTH, expand=True)

    log_text = Text(frame_console, wrap='word')
    log_text.pack(side='left', fill=BOTH, expand=True)

    scrollbar = Scrollbar(frame_console, command=log_text.yview, orient=VERTICAL)
    scrollbar.pack(side='right', fill='y')
    log_text.config(yscrollcommand=scrollbar.set)

    button1 = Button(frame_buttons, text="Выбрать папку и обработать моды", command=lambda: run_process(log))
    button1.pack(side='left', padx=5, pady=5)

    button_translate = Button(frame_buttons, text="Перевести мод", command=lambda: select_mod_for_translation(log))
    button_translate.pack(side='left', padx=5, pady=5)

    log("Программа запущена")
    root.mainloop()
    log("Программа остановлена")

if __name__ == "__main__":
    main()