import os
import shutil
import zipfile
from tkinter import Tk, filedialog, Button, Text, Scrollbar, Frame, END, VERTICAL, BOTH, X
import itertools
import threading
import ctypes

# Enable High DPI Awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)

def select_folder():
    folder_selected = filedialog.askdirectory()
    return folder_selected

def find_mods_without_ru(folder, log):
    mods_without_ru = []
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
    return mods_without_ru

def copy_mods_to_folder(mods, src_folder, dest_folder, log):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    total_files = len(mods)
    for i, mod in enumerate(mods, 1):
        shutil.copy(os.path.join(src_folder, mod), dest_folder)
        log(f"Скопировано {i}/{total_files} ({(i / total_files) * 100:.2f}%)")

def write_mods_to_file(mods, filepath, log):
    with open(filepath, 'w') as file:
        for mod in mods:
            file.write(f"{mod}\n")

def get_unique_path(base_path):
    if not os.path.exists(base_path):
        return base_path
    base, ext = os.path.splitext(base_path)
    for i in itertools.count(1):
        new_path = f"{base}_{i}{ext}"
        if not os.path.exists(new_path):
            return new_path

def process_mods(log):
    mods_folder = select_folder()
    if mods_folder:
        log("Выбрана папка: " + mods_folder)
        mods_without_ru = find_mods_without_ru(mods_folder, log)
        unique_mods_folder = get_unique_path('./mods')
        unique_list_file = get_unique_path('./mods_list.txt')
        log("Копирование модов...")
        copy_mods_to_folder(mods_without_ru, mods_folder, unique_mods_folder, log)
        log("Запись списка модов в файл...")
        write_mods_to_file(mods_without_ru, unique_list_file, log)
        log("Обработка завершена. Проверьте созданные папки и файлы.")

def run_process(log):
    threading.Thread(target=process_mods, args=(log,)).start()

from translate import Translator
def translate_text(text, src_lang='en', dest_lang='ru'):
    translator = Translator(from_lang=src_lang, to_lang=dest_lang)
    translation = translator.translate(text)
    return translation

import json
from tkinter import Toplevel, Listbox, Label, Entry, Button
import shutil
import zipfile

def open_translation_editor(mod_path):
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
        new_translations = {key: entry.get() for key, entry in entries.items()}
        ru_ru_path = en_us_path.replace('en_us.json', 'ru_ru.json')
        with zipfile.ZipFile(mod_path, 'a') as jar:
            jar.writestr(ru_ru_path, json.dumps(new_translations, ensure_ascii=False, indent=4))
        shutil.copy(mod_path, os.path.join('translated_mods', os.path.basename(mod_path)))
        update_translated_list(os.path.basename(mod_path))
        editor_window.destroy()

    save_button = Button(editor_window, text="Сохранить перевод", command=save_translation)
    save_button.grid(row=row, column=0, columnspan=2)

def update_translated_list(mod_name):
    list_path = './translated_mods_list.txt'
    with open(list_path, 'a') as file:
        file.write(f"{mod_name}\n")

def select_mod_for_translation():
    mods_folder = select_folder()
    if mods_folder:
        mod_files = [f for f in os.listdir(mods_folder) if f.endswith(".jar")]
        list_window = Toplevel(root)
        list_window.title("Выбор мода для перевода")
        listbox = Listbox(list_window)
        listbox.pack(fill=BOTH, expand=True)

        for mod in mod_files:
            listbox.insert(END, mod)

        def on_select(event):
            selected_mod = listbox.get(listbox.curselection())
            mod_path = os.path.join(mods_folder, selected_mod)
            open_translation_editor(mod_path)
            list_window.destroy()

        listbox.bind('<<ListboxSelect>>', on_select)



def main():
    global root
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

    def log(message):
        log_text.insert(END, message + "\n")
        log_text.see(END)

    button1 = Button(frame_buttons, text="Выбрать папку и обработать моды", command=lambda: run_process(log))
    button1.pack(side='left', padx=5, pady=5)

    button_translate = Button(frame_buttons, text="Перевести мод", command=select_mod_for_translation)
    button_translate.pack(side='left', padx=5, pady=5)

    button2 = Button(frame_buttons, text="Кнопка 2")
    button2.pack(side='left', padx=5, pady=5)

    button3 = Button(frame_buttons, text="Кнопка 3")
    button3.pack(side='left', padx=5, pady=5)

    button4 = Button(frame_buttons, text="Кнопка 4")
    button4.pack(side='left', padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()