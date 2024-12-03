import sys
import datetime
import sqlite3
from themes import *
from pydoc import describe

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QTextEdit, QPushButton, QListWidget, QLabel, QFileDialog,
    QComboBox, QMessageBox, QDialog, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QImage, QIcon, QPalette
from PyQt6.QtCore import Qt, QTimer


class NewsPost():
    def __init__(self, username, topic, description, category, image_path=''):
        self.username = username
        self.topic = topic
        self.description = description
        self.category = category
        self.image_path = image_path
        
        # Текущее время и дата
        self.time = str(datetime.datetime.now())
        self.time = self.time[self.time.index(' ') + 1:self.time.index(' ') + 6]
        self.date = str(datetime.datetime.now())
        self.date = '.'.join(self.date[:self.date.index(' ')].split('-')[::-1])

    def __str__(self):
        return f"{self.username} ({self.time}  {self.date}):\n{self.category}\n{self.topic}\n{self.description}\n\n"


class NewsFeedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лента Новостей")
        self.setGeometry(100, 80, 1000, 700)

        self.layout = QVBoxLayout()

        self.post_button = QPushButton('Добавить пост', self)
        self.post_button.clicked.connect(self.add_post)
        self.layout.addWidget(self.post_button)

        icon = QIcon("images/add.svg")
        self.post_button.setIcon(icon)


        self.category_combo_filter = QComboBox(self)
        self.category_combo_filter.addItems(["Все", "Технологии", "Политика", "Спорт", "Развлечения", "Образование"])
        self.category_combo_filter.currentTextChanged.connect(self.filter_posts)
        self.layout.addWidget(self.category_combo_filter)

        # Список постов
        self.posts_list = QListWidget(self)
        self.posts_list.itemClicked.connect(self.show_post_image)
        self.layout.addWidget(self.posts_list)

        self.txt_button = QPushButton("Экспортировать в TXT", self)
        self.txt_button.clicked.connect(self.export_txt_button)
        self.layout.addWidget(self.txt_button)

        self.theme_button = QPushButton("Выбрать тему", self)
        self.theme_button.clicked.connect(self.show_theme_dialog)
        self.layout.addWidget(self.theme_button)

        # Устанавливаем основной layout
        self.setLayout(self.layout)

        # Переменная для хранения выбранного изображения
        self.selected_image_path = ""
        
        # Список для хранения всех постов
        self.posts = []
        self.posts_for_txt = []

        con = sqlite3.connect('about_posts.VN')

        cur = con.cursor()

        result = cur.execute("""SELECT * FROM info_posts""").fetchall()
        for elem in result:
            new_post = NewsPost(elem[1], elem[3], elem[4], elem[2], elem[6])
            self.posts.append(new_post)
            self.posts_for_txt.append(str(new_post))
        con.close()

        self.display_posts()
        
        self.setStyleSheet(light_theme)
        self.background_image = QPixmap('images/bg.jpg')
        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(self.background_image))
        self.setPalette(palette)
        self.update()

    def add_post(self):
        post_dialog = PostItem(self)
        post_dialog.exec()

        new_post = post_dialog.get_post_data()
        if new_post != None:
            self.posts.append(new_post)
            self.posts_for_txt.append(str(new_post))
            self.display_posts()
            self.insert_varible_into_table(new_post.username, new_post.category, new_post.topic,
                                           new_post.description, 'time', new_post.image_path)

    def insert_varible_into_table(self, username, category, topic, description, time, image):
        try:
            con = sqlite3.connect('about_posts.VN')

            cur = con.cursor()

            result = cur.execute("""SELECT id FROM info_posts""").fetchall()

            id_post = len(result) + 1

            con.close()


            sqlite_connection = sqlite3.connect('about_posts.VN')

            cursor = sqlite_connection.cursor()

            sqlite_insert_with_param = """INSERT INTO info_posts
                                  (id, username, category, topic, description, time, image)
                                  VALUES (?, ?, ?, ?, ?, ?, ?);"""

            data_tuple = (id_post, username, category, topic, description, time, image)
            cursor.execute(sqlite_insert_with_param, data_tuple)
            sqlite_connection.commit()
            print("Переменные Python успешно вставлены в таблицу sqlitedb_developers")

            cursor.close()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()
                print("Соединение с SQLite закрыто")

    def filter_posts(self):
        """Фильтрация постов по выбранной категории."""
        selected_category = self.category_combo_filter.currentText()

        # Отображаем посты с выбранной категорией
        self.display_posts(selected_category)

    def display_posts(self, category="Все"):
        """Отображение постов в зависимости от выбранной категории."""
        self.posts_list.clear()
        # Фильтруем посты по категории
        for post in self.posts:
            if category == "Все" or post.category == category:
                self.posts_list.addItem(str(post))

    def show_post_image(self, item):
        # Получаем индекс поста по названию
        post_text = item.text()
        for post in self.posts:
            if str(post) == post_text:
                image_path = post.image_path
                if image_path:
                    # Отображаем картинку в диалоговом окнo
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        post_dialog = PostDialog(post, self)
                        post_dialog.exec()

    def export_txt_button(self):
        if self.posts:
            file = open('news_history', 'w', encoding='utf-8')
            file.write('-------------------------------------------------\n')
            for item in self.posts_for_txt:
                file.write(item)
                image = self.posts[self.posts_for_txt.index(item)].image_path
                if image:
                    file.write(f'Путь до изображения: {image}\n')
                file.write('-------------------------------------------------\n')
            file.close()
            info_message = 'Экспорт новостей в TXT завершен!\n\nНовости находятся в файле "news_history.txt".'
            QMessageBox.information(self, "Экспорт в TXT", info_message)
        else:
            QMessageBox.information(self, "Предупреждение", "Лента новостей пуста.")

    def show_theme_dialog(self):
        """Показ диалогового окна для выбора темы."""
        theme_dialog = ThemeDialog(self)
        theme_dialog.exec()


class PostDialog(QDialog):
    def __init__(self, post, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Изображение поста")
        self.setGeometry(200, 200, 400, 350)

        self.layout = QVBoxLayout()

        pixmap = QPixmap(post.image_path)
        scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
        image_label = QLabel(self)
        image_label.setPixmap(scaled_pixmap)

        self.layout.addWidget(image_label)

        self.setLayout(self.layout)

        self.selected_image_path = ""

class PostItem(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление поста")
        self.setGeometry(200, 200, 400, 350)

        self.layout = QVBoxLayout()

        # Поля ввода для данных
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        self.layout.addWidget(self.username_input)

        self.topic_input = QLineEdit(self)
        self.topic_input.setPlaceholderText("Тема поста")
        self.layout.addWidget(self.topic_input)

        # Выпадающий список для выбора категории
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(["Технологии", "Политика", "Спорт", "Развлечения", "Образование"])
        self.layout.addWidget(self.category_combo)

        # Описание поста
        self.description_input = QTextEdit(self)
        self.description_input.setPlaceholderText("Описание поста")
        self.description_input.setFixedHeight(77)
        self.layout.addWidget(self.description_input)

        # Кнопка для загрузки изображения
        self.upload_button = QPushButton("Выбрать изображение", self)
        self.upload_button.clicked.connect(self.upload_image)
        self.layout.addWidget(self.upload_button)

        # Кнопка добавления поста
        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.accept)  # Принять и закрыть диалог
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

        self.selected_image_path = ""

    def get_post_data(self):
        """Получить данные из формы и вернуть новый пост."""
        username = self.username_input.text()
        topic = self.topic_input.text()
        description = self.description_input.toPlainText()
        category = self.category_combo.currentText()
        if username and topic and description:
            if len(username) > 50:
                QMessageBox.information(self, "Предупреждение", """Имя пользователя не должно превышать 50 символов.\n
Если Вы Пабло Пикассо, свяжитесь с нами.""")
            elif len(topic) > 50:
                QMessageBox.information(self, "Предупреждение", "Тема новости не должна превышать 50 символов.")
            else:
                return NewsPost(username, topic, description, category, self.selected_image_path)

    def upload_image(self):
        """Загрузка изображения для поста."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.bmp)")
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.selected_image_path = file_paths[0]
                self.upload_button.setText("Изображение выбрано")


class ThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор темы")
        self.setGeometry(200, 200, 350, 500)
        
        # Создаем layout для размещения элементов
        self.layout = QVBoxLayout()

        # Для темы 1
        theme1_layout = QHBoxLayout()  # Горизонтальный макет для картинки и кнопки
        self.theme1_image = QLabel()
        self.theme1_image.setPixmap(QPixmap("images/light_theme.jpg").scaled(200, 143, Qt.AspectRatioMode.KeepAspectRatio))  # Замените на реальные пути
        self.theme1_button = QPushButton("Выбрать")
        self.theme1_button.clicked.connect(lambda: self.select_theme("Тема 1"))
        theme1_layout.addWidget(self.theme1_image)
        theme1_layout.addWidget(self.theme1_button)
        style_for_border_light = """
                border-radius: 5.5px;
                border: 2px solid #B5B8B1;"""
        self.theme1_image.setStyleSheet(style_for_border_light)

        # Для темы 2
        theme2_layout = QHBoxLayout()  # Горизонтальный макет для картинки и кнопки
        self.theme2_image = QLabel()
        self.theme2_image.setPixmap(QPixmap("images/dark_theme.jpg").scaled(200, 143, Qt.AspectRatioMode.KeepAspectRatio))  # Замените на реальные пути
        self.theme2_button = QPushButton("Выбрать")
        self.theme2_button.clicked.connect(lambda: self.select_theme("Тема 2"))
        theme2_layout.addWidget(self.theme2_image)
        theme2_layout.addWidget(self.theme2_button)
        self.theme2_image.setStyleSheet(style_for_border_light)

        # Для темы 3
        theme3_layout = QHBoxLayout()  # Горизонтальный макет для картинки и кнопки
        self.theme3_image = QLabel()
        self.theme3_image.setPixmap(QPixmap("images/custom_theme.jpg").scaled(200, 143, Qt.AspectRatioMode.KeepAspectRatio))  # Замените на реальные пути
        self.theme3_button = QPushButton("Выбрать")
        self.theme3_button.clicked.connect(lambda: self.select_theme("Тема 3"))
        theme3_layout.addWidget(self.theme3_image)
        theme3_layout.addWidget(self.theme3_button)
        self.theme3_image.setStyleSheet(style_for_border_light)

        # Для темы 4
        theme4_layout = QHBoxLayout()  # Горизонтальный макет для картинки и кнопки
        self.theme4_image = QLabel()
        self.theme4_image.setPixmap(QPixmap("images/custom_theme_new.jpg").scaled(200, 143, Qt.AspectRatioMode.KeepAspectRatio))  # Замените на реальные пути
        self.theme4_button = QPushButton("Выбрать")
        self.theme4_button.clicked.connect(lambda: self.select_theme("Тема 4"))
        theme4_layout.addWidget(self.theme4_image)
        theme4_layout.addWidget(self.theme4_button)
        self.theme4_image.setStyleSheet(style_for_border_light)

        # Добавляем горизонтальные макеты в основной layout
        self.layout.addLayout(theme1_layout)
        self.layout.addLayout(theme2_layout)
        self.layout.addLayout(theme3_layout)
        self.layout.addLayout(theme4_layout)
        # Устанавливаем layout
        self.setLayout(self.layout)

    def select_theme(self, theme_name):
        if theme_name == "Тема 1":
            self.parent().setStyleSheet(light_theme)
            style_for_border_light = """
                border-radius: 5px;
                border: 2px solid black;"""
        elif theme_name == "Тема 2":
            self.parent().setStyleSheet(dark_theme)
        elif theme_name == "Тема 3":
            self.parent().setStyleSheet(custom_theme)
        elif theme_name == "Тема 4":
            self.parent().setStyleSheet(custom_theme_new)
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NewsFeedApp()
    window.show()
    sys.exit(app.exec())