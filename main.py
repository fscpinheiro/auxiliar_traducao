import tkinter as tk
from tkinter import filedialog, ttk
import json
import pandas as pd
import os
import shutil
import threading
from translate import Translator

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ajudante de Tradução")
        self.base_file_path = None
        self.trans_file_paths = []
        self.columns = ['ID', 'Chave', 'Valor']
        self.analysis_results_tree = None
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
        # Vincula o evento de clique com o botão direito do mouse ao menu de contexto
        self.bind("<Button-3>", self.show_context_menu)
        # Maximizar a janela
        self.state('zoomed')

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

    def analyze_files(self):
        only_missing = self.show_only_divergent.get()
        ignore_dicts = not self.show_indirect_keys.get()

        if not self.base_file_path or not self.trans_file_paths:
            print("Por favor, selecione o arquivo base e os arquivos de tradução antes de analisar.")
            return

        # Limpa o Treeview existente, se houver
        for widget in self.analysis_results_tab.winfo_children():
            widget.destroy()

        # Cria um novo Treeview dentro de um Frame com Scrollbars
        tree_frame = tk.Frame(self.analysis_results_tab)
        tree_frame.pack(fill='both', expand=True)

        tree_scrollbar_y = tk.Scrollbar(tree_frame)
        tree_scrollbar_y.pack(side='right', fill='y')

        tree_scrollbar_x = tk.Scrollbar(tree_frame, orient='horizontal')
        tree_scrollbar_x.pack(side='bottom', fill='x')


        # Limpa as colunas existentes e adiciona as novas
        self.columns = ['ID', 'Chave', 'Valor']
        self.columns.extend([path.split('/')[-1].replace('.json', '').upper() for path in self.trans_file_paths])

        self.analysis_results_tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings',
                                                  yscrollcommand=tree_scrollbar_y.set,
                                                  xscrollcommand=tree_scrollbar_x.set)
        self.analysis_results_tree.pack(expand=1, fill='both')

        tree_scrollbar_y.config(command=self.analysis_results_tree.yview)
        tree_scrollbar_x.config(command=self.analysis_results_tree.xview)
        #self.analysis_results_tree.bind("<Button-3>", self.show_context_menu)

        # Configura as colunas
        self.analysis_results_tree.column('ID', width=110, anchor='center')
        self.analysis_results_tree.column('Chave', width=200, anchor='w')
        self.analysis_results_tree.column('Valor', width=200, anchor='w')
        for column_name in self.columns[3:]:  # Configura as colunas para cada arquivo de tradução
            self.analysis_results_tree.column(column_name, width=100, anchor='center')

        # Configura os cabeçalhos
        self.analysis_results_tree.heading('ID', text='ID')
        self.analysis_results_tree.heading('Chave', text='Chave')
        self.analysis_results_tree.heading('Valor', text='Valor')
        for column_name in self.columns[3:]:  # Configura os cabeçalhos para cada arquivo de tradução
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

        # Adiciona um rodapé com a quantidade de chaves e chaves faltantes
        footer_frame = tk.Frame(self.analysis_results_tab)
        footer_frame.pack(fill='x')

        total_keys_label = tk.Label(footer_frame, text=f"Total de chaves: {total_keys}")
        total_keys_label.pack(side='left')

        for path, count in missing_keys.items():
            missing_keys_label = tk.Label(footer_frame, text=f"Chaves faltantes em {path}: {count}")
            missing_keys_label.pack(side='left')

        # Adiciona um botão para adicionar a chave faltante
        add_key_button = tk.Button(self.analysis_results_tab, text="Adicionar chave faltante",
                                   command=self.add_missing_key)
        add_key_button.pack()
        #self.analysis_results_tree.bind('<Button-3>', self.copy_to_clipboard)

    def analyze(self):
        self.analyze_files(only_missing=False)

    def analyze_missing(self):
        self.analyze_files(only_missing=True)

    def add_missing_key(self):
        if not self.base_file_path or not self.trans_file_paths:
            print("Por favor, selecione o arquivo base e os arquivos de tradução antes de adicionar.")
            return

        # Itera sobre todas as linhas na tabela de resultados
        for selected_item in self.analysis_results_tree.get_children():
            values = self.analysis_results_tree.item(selected_item)['values']
            key = values[1]
            for path in self.trans_file_paths:
                column_name = path.split('/')[-1]
                if values[self.columns.index(column_name)] == 'OPS':
                    # Cria um backup do arquivo antes de modificar
                    backup_dir = 'temp'
                    os.makedirs(backup_dir, exist_ok=True)  # Cria o diretório se ele não existir
                    backup_path = os.path.join(backup_dir, 'backup_' + os.path.basename(path))
                    shutil.copyfile(path, backup_path)

                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    keys = key.split('.')
                    sub_data = data
                    for k in keys[:-1]:
                        if k not in sub_data:
                            sub_data[k] = {}
                        elif not isinstance(sub_data[k], dict):
                            sub_data[k] = {}
                        sub_data = sub_data[k]
                    sub_data[keys[-1]] = "..." + "@@@"

                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

        # Atualiza a análise
        self.analyze_missing()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copiar", command=self.copy_to_clipboard)
        self.context_menu.add_command(label="Traduzir para inglês", command=self.translate_to_english)
        self.context_menu.add_command(label="Traduzir para espanhol", command=self.translate_to_spanish)

    def show_context_menu(self, event):
        # Identifica a linha sob o cursor
        row_id = self.analysis_results_tree.identify_row(event.y)
        column_id = self.analysis_results_tree.identify_column(event.x)

        # Se nenhuma linha foi identificada, não faz nada
        if row_id == "":
            return

        # Seleciona a linha sob o cursor
        self.analysis_results_tree.selection_set(row_id)

        # Armazena a linha e coluna selecionada
        self.selected_row = row_id
        self.selected_col = column_id

        # Mostra o menu de contexto
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_to_clipboard(self):
        # Obtém a linha e coluna selecionada
        row_id = self.selected_row
        column_id = self.selected_col

        # Obtém o valor da célula
        cell_value = self.analysis_results_tree.set(row_id, column_id)

        # Copia o valor para a área de transferência
        self.clipboard_clear()
        self.clipboard_append(cell_value)

        # Cria uma janela de diálogo para mostrar a mensagem
        dialog = tk.Toplevel(self)
        dialog.title("Copiado para a área de transferência")
        tk.Label(dialog, text=f"Valor copiado: {cell_value}").pack()

        # Centraliza a janela de diálogo na parte superior da tela
        window_width = dialog.winfo_reqwidth()
        window_height = dialog.winfo_reqheight()
        position_right = int(dialog.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(dialog.winfo_screenheight() / 3 - window_height / 2)
        dialog.geometry("+{}+{}".format(position_right, position_down))

        # Fecha a janela de diálogo após 2 segundos
        def close_dialog():
            dialog.destroy()

        threading.Timer(2, close_dialog).start()

    @staticmethod
    def to_english(text):
        translator = Translator(from_lang="pt", to_lang="en")
        translation = translator.translate(text)
        return translation

    @staticmethod
    def to_spanish(text):
        translator = Translator(from_lang="pt", to_lang="es")
        translation = translator.translate(text)
        return translation

    def translate_to_english(self):
        # Verifica se uma linha está selecionada
        selected_items = self.analysis_results_tree.selection()
        if not selected_items:
            tk.messagebox.showinfo("Aviso", "Por favor, selecione uma linha para traduzir.")
            return

        # Obtém a linha selecionada
        selected_item = selected_items[0]

        # Obtém o valor da célula na coluna "Valor"
        cell_value = self.analysis_results_tree.set(selected_item, '#3')

        # Traduz o valor para o inglês
        translated_value = self.to_english(cell_value)

        # Mostra o valor em um alerta
        tk.messagebox.showinfo("Tradução para inglês", f"Valor da chave: {translated_value}")

    def translate_to_spanish(self):
        # Verifica se uma linha está selecionada
        selected_items = self.analysis_results_tree.selection()
        if not selected_items:
            tk.messagebox.showinfo("Aviso", "Por favor, selecione uma linha para traduzir.")
            return

        # Obtém a linha selecionada
        selected_item = selected_items[0]

        # Obtém o valor da célula na coluna "Valor"
        cell_value = self.analysis_results_tree.set(selected_item, '#3')

        # Traduz o valor para o espanhol
        translated_value = self.to_spanish(cell_value)

        # Mostra o valor em um alerta
        tk.messagebox.showinfo("Tradução para espanhol", f"Valor da chave: {translated_value}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
