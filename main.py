import tkinter as tk
from tkinter import filedialog, ttk
import json
import pandas as pd
import os
import shutil
import threading
from translate import Translator
from googletrans import Translator

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ajudante de Tradução")
        self.base_file_path = None
        self.trans_file_paths = []
        self.trans_file_langs = {}
        self.columns = ['ID', 'Chave', 'Valor']
        self.analysis_results_tree = None
        self.create_menu()
        # Frame para seleção de arquivos base
        self.base_file_frame = tk.Frame(self)
        self.base_file_frame.pack(fill='x')
        self.base_file_button = tk.Button(self.base_file_frame, text="Escolher arquivo", command=self.select_base_file)
        self.base_file_button.pack(side='left')
        self.base_file_clear_button = tk.Button(self.base_file_frame, text="Limpar seleção",
                                                command=self.clear_base_file)
        self.base_file_clear_button.pack(side='left')
        self.base_file_label = tk.Label(self.base_file_frame, text="Arquivo base:", bg="black", fg="white",
                                        font=("Arial", 12, "bold"))
        self.base_file_label.pack(side='left', fill='x', expand=True)
        # Frame para seleção de arquivos de tradução
        self.trans_file_frame = tk.Frame(self)
        self.trans_file_frame.pack(fill='x')
        self.trans_file_button = tk.Button(self.trans_file_frame, text="Escolher arquivos",
                                           command=self.select_trans_files)
        self.trans_file_button.pack(side='left')
        self.trans_file_clear_button = tk.Button(self.trans_file_frame, text="Limpar seleção",
                                                 command=self.clear_trans_files)
        self.trans_file_clear_button.pack(side='left')
        self.trans_file_label = tk.Label(self.trans_file_frame, text="Arquivos de tradução:", bg="black", fg="white",
                                         font=("Arial", 12, "bold"))
        self.trans_file_label.pack(side='left', fill='x', expand=True)
        # Frame para opções de análise
        self.options_frame = tk.Frame(self)
        self.options_frame.pack(fill='x')
        # Checkboxes para opções de análise
        self.show_only_divergent = tk.BooleanVar()
        self.show_only_divergent_check = tk.Checkbutton(self.options_frame, text="Mostrar apenas chaves divergentes",
                                                        variable=self.show_only_divergent)
        self.show_only_divergent_check.pack(side='left')
        self.show_indirect_keys = tk.BooleanVar()
        self.show_indirect_keys_check = tk.Checkbutton(self.options_frame, text="Mostrar chaves Indiretas",
                                                       variable=self.show_indirect_keys)
        self.show_indirect_keys_check.pack(side='left')
        # Botão de análise
        self.analyze_button = tk.Button(self.options_frame, text="Analisar", command=self.analyze_files)
        self.analyze_button.pack(side='left')
        # Abas de relatório
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')
        self.analysis_results_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.analysis_results_tab, text='Resultado da Análise')
        # Aba de visualização
        self.files_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.files_tab, text='Arquivos')
        self.view_notebook = ttk.Notebook(self.files_tab)
        self.view_notebook.pack(expand=1, fill='both')
        # Cria o menu de contexto
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copiar", command=self.copy_to_clipboard)
        self.context_menu.add_command(label="Traduzir para inglês", command=self.translate_to_english)
        self.context_menu.add_command(label="Traduzir para espanhol", command=self.translate_to_spanish)
        self.bind("<Button-3>", self.show_context_menu)
        self.state('zoomed')

    def create_menu(self):
        menu_bar = tk.Menu(self)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Definir idiomas",
                                  command=self.set_trans_file_langs)  
        menu_bar.add_cascade(label="Configurações",
                             menu=settings_menu)  

        self.config(menu=menu_bar)

    def get_keys(self, dic, parent_key = ''):
        keys = []
        for k, v in dic.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            keys.append(new_key)
            if isinstance(v, dict):
                keys.extend(self.get_keys(v, new_key))
        return keys

    def get_value(self, dic, key):
        keys = key.split('.')
        val = dic
        for k in keys:
            val = val.get(k, None)
            if val is None:
                return None
        return val

    def check_keys(self, file_path1, file_path2):
        with open(file_path1, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(file_path2, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        keys1 = self.get_keys(data1)
        keys2 = self.get_keys(data2)
        result = []
        for key in keys1:
            value = self.get_value(data1, key)
            if isinstance(value, dict):
                value = "{ ... }"
            result.append({
                'key': key,
                'PT': value,
                file_path2.split('/')[-1]: 'OK' if key in keys2 else 'OPS',
            })
        df = pd.DataFrame(result)
        return df

    def select_base_file(self):
        self.base_file_path = filedialog.askopenfilename()
        self.base_file_label['text'] = f"Arquivo base: {self.base_file_path}"
        self.update_view_tab()

    def clear_base_file(self):
        self.base_file_path = None
        self.base_file_label['text'] = "Arquivo base:"
        self.update_view_tab()

    def select_trans_files(self):
        self.trans_file_paths = filedialog.askopenfilenames()
        self.trans_file_label['text'] = f"Arquivos de tradução: {', '.join(self.trans_file_paths)}"
        self.update_view_tab()

    def clear_trans_files(self):
        self.trans_file_paths = []
        self.trans_file_label['text'] = "Arquivos de tradução:"
        self.update_view_tab()

    def update_view_tab(self):
        for tab in self.view_notebook.tabs():
            self.view_notebook.forget(tab)
        if self.base_file_path:
            base_tab = ttk.Frame(self.view_notebook)
            self.view_notebook.add(base_tab, text=f'Base: {self.base_file_path.split("/")[-1]}')
            base_text = tk.Text(base_tab)
            base_text.pack(expand=1, fill='both')
            with open(self.base_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                base_text.insert(tk.END, content)
                base_text.config(state='disabled')
                line_count = content.count('\n') + 1
                base_text.insert(tk.END, f"\n\n--- Total de linhas: {line_count} ---")
        for path in self.trans_file_paths:
            trans_tab = ttk.Frame(self.view_notebook)
            self.view_notebook.add(trans_tab, text=path.split('/')[-1])
            trans_text = tk.Text(trans_tab)
            trans_text.pack(expand=1, fill='both')
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                trans_text.insert(tk.END, content)
                trans_text.config(state='disabled')
                line_count = content.count('\n') + 1
                trans_text.insert(tk.END, f"\n\n--- Total de linhas: {line_count} ---")

    def set_trans_file_langs(self):
        lang_window = tk.Toplevel(self)
        lang_window.title("Configurações")
        base_frame = tk.Frame(lang_window)
        base_frame.pack(fill='x')
        base_label = tk.Label(base_frame, text=self.base_file_path)
        base_label.pack(side='left')
        base_var = tk.StringVar()
        base_var.set(
            self.trans_file_langs.get(self.base_file_path, "")) 
        base_option_menu = tk.OptionMenu(base_frame, base_var, "pt", "en",
                                         "es")  
        base_option_menu.pack(side='left')
        base_var.trace("w",
                       lambda name, index, mode, p=self.base_file_path, v=base_var: self.save_trans_file_lang(p, v))

        for i, path in enumerate(self.trans_file_paths):
            frame = tk.Frame(lang_window)
            frame.pack(fill='x')
            label = tk.Label(frame, text=path)
            label.pack(side='left')
            var = tk.StringVar()
            var.set(self.trans_file_langs.get(path, ""))  
            option_menu = tk.OptionMenu(frame, var, "pt", "en", "es")  
            option_menu.pack(side='left')
            var.trace("w", lambda name, index, mode, p=path, v=var: self.save_trans_file_lang(p, v))
    def save_trans_file_lang(self, path, var):
        self.trans_file_langs[path] = var.get()
        print(f"Idioma do arquivo {path} definido como {var.get()}")
    def analyze_files(self):
        only_missing = self.show_only_divergent.get()
        ignore_dicts = not self.show_indirect_keys.get()
        if not self.base_file_path or not self.trans_file_paths:
            print("Por favor, selecione o arquivo base e os arquivos de tradução antes de analisar.")
            return
        for widget in self.analysis_results_tab.winfo_children():
            widget.destroy()
        tree_frame = tk.Frame(self.analysis_results_tab)
        tree_frame.pack(fill='both', expand=True)
        tree_scrollbar_y = tk.Scrollbar(tree_frame)
        tree_scrollbar_y.pack(side='right', fill='y')
        tree_scrollbar_x = tk.Scrollbar(tree_frame, orient='horizontal')
        tree_scrollbar_x.pack(side='bottom', fill='x')
        self.columns = ['ID', 'Chave', 'Valor']
        self.columns.extend([path.split('/')[-1].replace('.json', '').upper() for path in self.trans_file_paths])
        self.analysis_results_tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings',
                                                  yscrollcommand=tree_scrollbar_y.set,
                                                  xscrollcommand=tree_scrollbar_x.set)
        self.analysis_results_tree.pack(expand=1, fill='both')
        tree_scrollbar_y.config(command=self.analysis_results_tree.yview)
        tree_scrollbar_x.config(command=self.analysis_results_tree.xview)
        self.analysis_results_tree.column('ID', width=110, anchor='center')
        self.analysis_results_tree.column('Chave', width=200, anchor='w')
        self.analysis_results_tree.column('Valor', width=200, anchor='w')
        for column_name in self.columns[3:]: 
            self.analysis_results_tree.column(column_name, width=100, anchor='center')
        self.analysis_results_tree.heading('ID', text='ID')
        self.analysis_results_tree.heading('Chave', text='Chave')
        self.analysis_results_tree.heading('Valor', text='Valor')
        for column_name in self.columns[3:]:  
            self.analysis_results_tree.heading(column_name, text=column_name)
        total_keys = 0
        missing_keys = {path.split('/')[-1].replace('.json', '').upper(): 0 for path in self.trans_file_paths}
        with open(self.base_file_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
        base_keys = self.get_keys(base_data)
        for index, key in enumerate(base_keys):
            value = self.get_value(base_data, key)
            if isinstance(value, dict):
                if ignore_dicts:
                    continue
                value = "{ ... }"
                missing = False
            values = [index + 1, key, value]
            missing = False
            for path in self.trans_file_paths:
                column_name = path.split('/')[-1].replace('.json', '').upper()
                with open(path, 'r', encoding='utf-8') as f:
                    trans_data = json.load(f)
                if key in self.get_keys(trans_data):
                    values.append('OK')
                else:
                    values.append('OPS')
                    missing = True
                    missing_keys[column_name] += 1
            if missing or not only_missing:
                self.analysis_results_tree.insert('', 'end', values=values)

        total_keys = len(base_keys)
        footer_frame = tk.Frame(self.analysis_results_tab)
        footer_frame.pack(fill='x')
        total_keys_label = tk.Label(footer_frame, text=f"Total de chaves: {total_keys}")
        total_keys_label.pack(side='left')
        for path, count in missing_keys.items():
            missing_keys_label = tk.Label(footer_frame, text=f"Chaves faltantes em {path}: {count}")
            missing_keys_label.pack(side='left')
        add_key_button = tk.Button(self.analysis_results_tab, text="Adicionar chave faltante",
                                   command=self.add_missing_key)
        add_key_button.pack()

    def analyze(self):
        self.analyze_files(only_missing=False)

    def analyze_missing(self):
        self.analyze_files(only_missing=True)

    def add_key(self, dic, key_path, value):
        keys = key_path.split('.')
        for key in keys[:-1]:
            if not isinstance(dic, dict):
                dic = {}
            if key not in dic or not isinstance(dic[key], dict):
                dic[key] = {}
            dic = dic[key]
        if isinstance(dic, dict):
            dic[keys[-1]] = value
        else:
            dic = {keys[-1]: value}

    def add_missing_key(self):
        if not self.base_file_path or not self.trans_file_paths:
            tk.messagebox.showinfo("Aviso", "Por favor, selecione o arquivo base e pelo menos um arquivo de tradução.")
            return
        with open(self.base_file_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
        def translate_value(value, from_lang, to_lang):
            translator = Translator()
            if isinstance(value, str):
                return translator.translate(value, src=from_lang, dest=to_lang).text
            elif isinstance(value, dict):
                return {k: translate_value(v, from_lang, to_lang) for k, v in value.items()}
            else:
                return value

        for trans_file_path in self.trans_file_paths:
            with open(trans_file_path, 'r', encoding='utf-8') as f:
                trans_data = json.load(f)
            from_lang = self.trans_file_langs.get(self.base_file_path, "pt")
            to_lang = self.trans_file_langs.get(trans_file_path, "en")
            for key in self.get_keys(base_data):
                if key not in self.get_keys(trans_data):
                    value = self.get_value(base_data, key)
                    translated_value = translate_value(value, from_lang, to_lang)
                    self.add_key(trans_data, key, translated_value)
            with open(trans_file_path, 'w', encoding='utf-8') as f:
                json.dump(trans_data, f, ensure_ascii=False, indent=4)
        tk.messagebox.showinfo("Informação", "A adição das chaves e seus valores traduzidos foi concluída.")
        self.analyze_files()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copiar", command=self.copy_to_clipboard)
        self.context_menu.add_command(label="Traduzir para inglês", command=self.translate_to_english)
        self.context_menu.add_command(label="Traduzir para espanhol", command=self.translate_to_spanish)

    def show_context_menu(self, event):
        row_id = self.analysis_results_tree.identify_row(event.y)
        column_id = self.analysis_results_tree.identify_column(event.x)
        if row_id == "":
            return
        self.analysis_results_tree.selection_set(row_id)
        self.selected_row = row_id
        self.selected_col = column_id
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_to_clipboard(self):
        row_id = self.selected_row
        column_id = self.selected_col
        cell_value = self.analysis_results_tree.set(row_id, column_id)
        self.clipboard_clear()
        self.clipboard_append(cell_value)
        dialog = tk.Toplevel(self)
        dialog.title("Copiado para a área de transferência")
        tk.Label(dialog, text=f"Valor copiado: {cell_value}").pack()
        window_width = dialog.winfo_reqwidth()
        window_height = dialog.winfo_reqheight()
        position_right = int(dialog.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(dialog.winfo_screenheight() / 3 - window_height / 2)
        dialog.geometry("+{}+{}".format(position_right, position_down))
        def close_dialog():
            dialog.destroy()

        threading.Timer(4, close_dialog).start()

    @staticmethod
    def to_english(text, from_lang):
        translator = Translator(from_lang=from_lang, to_lang="en")
        translation = translator.translate(text)
        return translation

    @staticmethod
    def to_spanish(text, from_lang):
        translator = Translator(from_lang=from_lang, to_lang="es")
        translation = translator.translate(text)
        return translation

    def translate_to_english(self):
        selected_items = self.analysis_results_tree.selection()
        if not selected_items:
            tk.messagebox.showinfo("Aviso", "Por favor, selecione uma linha para traduzir.")
            return
        from_lang = self.trans_file_langs.get(self.base_file_path, "pt")
        selected_item = selected_items[0]
        cell_value = self.analysis_results_tree.set(selected_item, '#3')
        translated_value = self.to_english(cell_value, from_lang)
        tk.messagebox.showinfo("Tradução para inglês", f"Valor da chave: {translated_value}")

    def translate_to_spanish(self):
        selected_items = self.analysis_results_tree.selection()
        if not selected_items:
            tk.messagebox.showinfo("Aviso", "Por favor, selecione uma linha para traduzir.")
            return
        from_lang = self.trans_file_langs.get(self.base_file_path, "pt")
        selected_item = selected_items[0]
        cell_value = self.analysis_results_tree.set(selected_item, '#3')
        translated_value = self.to_spanish(cell_value, from_lang)
        tk.messagebox.showinfo("Tradução para espanhol", f"Valor da chave: {translated_value}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
