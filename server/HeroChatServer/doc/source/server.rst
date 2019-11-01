Server module
=================================================

Серверный модуль мессенджера. Обрабатывает словари - сообщения, хранит публичные ключи клиентов.

Использование

Модуль подерживает аргементы командной стороки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.
3. --no_gui Запуск только основных функций, без графической оболочки.

* В данном режиме поддерживается только 1 команда: exit - завершение работы.

Примеры использования:

``python server.py -p 8080``

*Запуск сервера на порту 8080*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

``python server.py --no-gui``

*Запуск без графической оболочки*

server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

	* адрес с которого принимать соединения
	* порт
	* флаг запуска GUI

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

core.py
~~~~~~~~~~~

.. automodule:: server.core

.. autoclass:: server.core.MessageProcessor
	:members:

database.py
~~~~~~~~~~~

.. automodule:: server.database

.. autoclass:: server.database.ServerStorage
	:members:

main_window.py
~~~~~~~~~~~~~~

.. automodule:: server.main_window


.. autoclass:: server.main_window.MainWindow
	:members:

add_user.py
~~~~~~~~~~~

.. automodule:: server.add_user

.. autoclass:: server.add_user.RegisterUser
	:members:

remove_user.py
~~~~~~~~~~~~~~

.. automodule:: server.remove_user

.. autoclass:: server.remove_user.DelUserDialog
	:members:

config_window.py
~~~~~~~~~~~~~~~~

.. automodule:: server.config_window

.. autoclass:: server.config_window.ConfigWindow
	:members:

stat_window.py
~~~~~~~~~~~~~~~~

.. automodule:: server.stat_window

.. autoclass:: server.stat_window.StatWindow
	:members: