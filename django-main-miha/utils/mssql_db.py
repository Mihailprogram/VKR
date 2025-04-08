import pyodbc
import os


def connect_mssql(server_name: str, user: str, password: str):
    """
    Создает подключение к серверу MSSQL
    Args:
        server_name (string): Имя сервера подключения
        user (string): учетная запись пользователя для подключения
        password (string): Пароль учетной записи пользователя
    """
    try:
        cnxn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}',
                              server=server_name,
                              user=user,
                              password=password,
                              autocommit='true')
        return cnxn
    except pyodbc.Error as ex:
        sql_state = ex.args[0]
        if sql_state == '28000':
            print(f"Не удалось авторизоваться на сервере {server_name}")
        if sql_state == 'HYT00':
            print(f"Не удалось подключиться к серверу {server_name}")
        return None


def execute_procedure(server_name, user='', password='', proc_name="", params={}, sql=""):
    """
    Вызывает выполнение процедуры на mssql сервере либо из sql параметра, либо из переданных proc_name и params
    Args:
        server_name (string): Имя сервера подключения
        proc_name (string): Имя процедуры в формате [database].[schema].[proc_name]
        params (**kwargs): параметры процедуры
        sql (string): Чистый SQL запрос, который требуется выполнить, а не проуедура с параметрами
    """
    # если не были преданы параметры пользователя, пробуем использовать по-умолчанию
    # то есть те, что получены при проведении аутентификации
    if user == '':
        user = user
        password = password
    # Подключаемся к серверу
    con = connect_mssql(server_name, user, password)
    cursor = con.cursor()
    if sql and sql != "":
        try:
            cursor.execute(sql)
            return dictfetchall(cursor)
        except pyodbc.Error as ex:
            sql_state = ex.args[1]
            print(
                f"{sql_state}\nПроизошла ошибка выполнения sql запроса \n SQL: {sql}")
            return None

    if proc_name and proc_name != "" and params:
        try:
            # Внимание, преобразовывайте в параметрах None в 'Null'
            param_values = ','.join(params.values())
            proc_sql = f"EXEC {proc_name} {param_values}"
            cursor.execute(proc_sql)
            return dictfetchall(cursor)
        except pyodbc.Error as ex:
            sql_state = ex.args[1]
            print(
                f"{sql_state}\nПроизошла ошибка выполнения процедуры {proc_name} c параметрами {params}")
            return None


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
