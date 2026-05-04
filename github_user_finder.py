import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import urllib.request
import urllib.error
import ssl

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Загрузка избранных пользователей
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Верхняя панель поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(search_frame, text="Поиск пользователя GitHub:").grid(row=0, column=0, padx=5)
        
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_user())
        
        self.search_button = ttk.Button(search_frame, text="Поиск", command=self.search_user)
        self.search_button.grid(row=0, column=2, padx=5)
        
        # Панель с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        # Вкладка результатов поиска
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Результаты поиска")
        
        # Вкладка избранного
        self.favorites_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.favorites_tab, text="Избранное")
        
        # Создание таблиц для отображения результатов
        self.create_search_results()
        self.create_favorites_list()
        
        # Настройка веса колонок для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
    def create_search_results(self):
        # Создание Treeview для результатов поиска
        columns = ("Username", "Name", "Repos", "Followers")
        
        # Фрейм для поиска
        search_frame = ttk.Frame(self.search_tab)
        search_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(search_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_tree = ttk.Treeview(search_frame, columns=columns, show="headings", 
                                        yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.search_tree.yview)
        
        # Настройка колонок
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=150)
        
        self.search_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка для добавления в избранное
        button_frame = ttk.Frame(search_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Добавить выбранного в избранное", 
                  command=self.add_to_favorites).pack(side=tk.LEFT, padx=5)
        
    def create_favorites_list(self):
        # Фрейм для избранного
        fav_frame = ttk.Frame(self.favorites_tab)
        fav_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(fav_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ("Username", "Name", "Repos", "Followers", "Added Date")
        self.favorites_tree = ttk.Treeview(fav_frame, columns=columns, show="headings", 
                                           yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.favorites_tree.yview)
        
        # Настройка колонок
        for col in columns:
            self.favorites_tree.heading(col, text=col)
            self.favorites_tree.column(col, width=130)
        
        self.favorites_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления избранным
        btn_frame = ttk.Frame(fav_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Удалить выбранного", command=self.remove_from_favorites).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_favorites_display).pack(side=tk.LEFT, padx=5)
        
        # Отображение избранных
        self.refresh_favorites_display()
    
    def make_api_request(self, url):
        """Выполнение HTTP запроса с использованием urllib (встроенная библиотека)"""
        try:
            # Создаём контекст SSL (нужен для HTTPS)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Выполняем запрос
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GitHub User Finder/1.0')
            
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except urllib.error.HTTPError as e:
            messagebox.showerror("Ошибка API", f"HTTP ошибка: {e.code}")
            return None
        except urllib.error.URLError as e:
            messagebox.showerror("Ошибка сети", f"Ошибка соединения: {e.reason}")
            return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            return None
        
    def search_user(self):
        username = self.search_entry.get().strip()
        
        # Проверка на пустое поле
        if not username:
            messagebox.showwarning("Ошибка", "Поле поиска не может быть пустым!")
            return
        
        # Очистка предыдущих результатов
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        # Поиск пользователей через GitHub API
        url = f"https://api.github.com/search/users?q={username}"
        data = self.make_api_request(url)
        
        if data and 'items' in data:
            users = data.get('items', [])[:10]  # Показываем первых 10 пользователей
            
            if not users:
                messagebox.showinfo("Результаты", "Пользователи не найдены")
                return
            
            # Получение дополнительной информации о каждом пользователе
            for user in users:
                user_url = user['url']
                user_data = self.make_api_request(user_url)
                
                if user_data:
                    # Добавление в таблицу
                    self.search_tree.insert("", tk.END, values=(
                        user_data.get('login', ''),
                        user_data.get('name', 'Н/Д'),
                        user_data.get('public_repos', 0),
                        user_data.get('followers', 0)
                    ), iid=user_data.get('login', ''))
    
    def add_to_favorites(self):
        selected = self.search_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя для добавления в избранное!")
            return
        
        username = selected[0]
        
        # Проверка, не добавлен ли уже пользователь
        if username in self.favorites:
            messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном!")
            return
        
        # Получение информации о пользователе
        url = f"https://api.github.com/users/{username}"
        user_data = self.make_api_request(url)
        
        if user_data:
            favorite_user = {
                "username": user_data.get('login', ''),
                "name": user_data.get('name', 'Н/Д'),
                "repos": user_data.get('public_repos', 0),
                "followers": user_data.get('followers', 0),
                "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.favorites[username] = favorite_user
            self.save_favorites()
            self.refresh_favorites_display()
            messagebox.showinfo("Успех", f"Пользователь {username} добавлен в избранное!")
    
    def remove_from_favorites(self):
        selected = self.favorites_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя для удаления из избранного!")
            return
        
        username = selected[0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {username} из избранного?"):
            del self.favorites[username]
            self.save_favorites()
            self.refresh_favorites_display()
            messagebox.showinfo("Успех", f"Пользователь {username} удален из избранного!")
    
    def refresh_favorites_display(self):
        # Очистка таблицы
        for item in self.favorites_tree.get_children():
            self.favorites_tree.delete(item)
        
        # Добавление избранных пользователей
        for username, data in self.favorites.items():
            self.favorites_tree.insert("", tk.END, values=(
                data.get('username', ''),
                data.get('name', ''),
                data.get('repos', 0),
                data.get('followers', 0),
                data.get('added_date', '')
            ), iid=username)
    
    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_favorites(self):
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()