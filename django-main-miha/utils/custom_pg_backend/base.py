from thirdparty.threadlocals.threadlocals import get_current_request
from utils.auth import get_credentials_from_user_info
from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper


class DatabaseWrapper(PostgresDatabaseWrapper):
    '''
    Измененный обработчик для подключения к БД с помощью сохраненной личной учетной записи пользователя
    '''

    def get_new_connection(self, conn_params):
        # в настройках подключения есть флаг, что это подключение должно производиться
        # из-под личной учетной записи пользователя
        if self.settings_dict.get('VOLATILE') == True:
            # получаем запрос, который в данный момент обрабатывается
            request = get_current_request()
            if request:
                # получаем пользовательские данные из сессии этого обрабатываемого запроса
                user, password = get_credentials_from_user_info(request)
                if user and password:
                    # подменяем учетные данные в подключении
                    conn_params['user'] = user
                    conn_params['password'] = password
        return super().get_new_connection(conn_params)
