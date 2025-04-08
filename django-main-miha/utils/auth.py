
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
import requests #Miha
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend
from main.settings.settings import REMOTE_USER_HEADER, NO_UPDATE_LAST_LOGIN, WHOAMI_URL
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
import re
from json import loads
import kerberos #Miha
from thirdparty.threadlocals.threadlocals import get_current_request

# проверка, в каком окружении запущен проект
_local_development = True
try:
    from main.settings.django_private import DATABASES
    _local_development = False
except:
    from main.settings.local_dev import DATABASES
    _local_development = True


"""
    Список username закешированых пользователей
"""
CACHED_USERS = []

"""
    Отключение обновления последнего логина
"""
if NO_UPDATE_LAST_LOGIN:
    user_logged_in.disconnect(
        update_last_login, dispatch_uid='update_last_login')


"""
    Мидлвар для отключения CSRF
"""


class DisableCSRFMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response


class CustomRemoteUserMiddleware(RemoteUserMiddleware):
    '''    изменяет имя заголовка, который используется для аутентификации
    по умолчанию REMOTE_USER, в локали (runserver) LOGNAME, на веб сервере HTTP_X_REMOTE_USER
    смотрит в переменную в settings, изменится в зависимости от локальной/деплойной конфигурации
    '''
    header = REMOTE_USER_HEADER
    force_logout_if_no_header = True

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")
        try:
            username = request.META[self.header]
        except KeyError:
            # If specified header doesn't exist then remove any existing
            # authenticated remote-user, or return (leaving request.user set to
            # AnonymousUser by the AuthenticationMiddleware).
            if self.force_logout_if_no_header and request.user.is_authenticated:
                self._remove_invalid_user(request)
            return

        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if request.user.get_username() == self.clean_username(username, request):
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)
        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, remote_user=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)
            CACHED_USERS.append(username)
            save_user_info_to_request_session(request)


class CustomRemoteUserBackend(RemoteUserBackend):
    '''
    Управляет возможностью автоматического создания пользователя при отсутствии учётных данных в БД,
    путём переопределения переменной create_unknown_user, в засимости от переметра CREATE_UNKNOWN_USER
    в settings. При отсутствии данного параметра, сохраняет действие Django по умолчанию (True).
    Также приводит к единому виду учетные записи.
    '''
    try:
        from main.settings.settings import CREATE_UNKNOWN_USER
        create_unknown_user = CREATE_UNKNOWN_USER
    except:
        pass

    def clean_username(self, username):
        _username, domain = username.split('@')
        cleaned_username = _username + '@' + domain.upper()
        return cleaned_username

    def authenticate(self, request, remote_user):
        username, domain = remote_user.split('@')
        remote_user = username
        if domain:
            remote_user += '@' + domain.upper()

        save_user_info_to_request_session(request)
        return super().authenticate(request, remote_user=remote_user)


def get_client_username(request):
    # Веб сервер, настроен определенным образом, авторизует пользователя
    # и добавляет в каждый запрос определенный заголовок, содержащий имя пользователя
    username = request.META.get(REMOTE_USER_HEADER, '')
    return username


def get_client_negotiate_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    negotiate_token = ''
    if auth_header:
        # может быть несколько заголовков с авторизацией
        kind, details = auth_header.split(' ')
        if kind.lower() == 'negotiate':
            negotiate_token = details.strip()
    return negotiate_token


def generate_local_negotiate():
    __, krb_context = kerberos.authGSSClientInit('HTTP@ecp-webdev1.main.ecp')
    kerberos.authGSSClientStep(krb_context, "")
    negotiate_details = kerberos.authGSSClientResponse(krb_context)
    return negotiate_details


def get_client_negotiate_value(response):
    """Extracts the gssapi authentication token from the appropriate header"""
    # взято из библиотеки kerberos
    if hasattr(get_client_negotiate_value, 'regex'):
        regex = get_client_negotiate_value.regex
    else:
        # There's no need to re-compile this EVERY time it is called. Compile
        # it once and you won't have the performance hit of the compilation.
        regex = re.compile('(?:.*,)*\s*Negotiate\s*([^,]*),?', re.I)
        get_client_negotiate_value.regex = regex

    authreq = response.headers.get('www-authenticate', None)

    if authreq:
        match_obj = regex.search(authreq)
        if match_obj:
            return match_obj.group(1)

    return None


def get_credentials_from_user_info(request):
    '''
    Из объекта request получит данные сессии текущего пользователя.
    И если в них есть данные user_info, найдет в них SQL логин и пароль текущего пользователя
    '''
    user_info = request.session.get('user_info')
    user = ''
    password = ''
    if user_info:
        data = user_info.get('data')
        user = data.get('sql_login')
        password = data.get('token')
    return user, password


def get_user_info_from_request_session(request):
    user_info = {}
    if request.session:
        user_info = request.session.get('user_info')
    return user_info


def save_user_info_to_request_session(request):
    if not is_request_has_session_user_info(request):
        user_info = get_whoami()
        request.session['user_info'] = user_info


def is_request_has_session_user_info(request):
    if request.session:
        session_user_info = request.session.get('user_info')
        if session_user_info:
            data = session_user_info.get('data')
            user = data.get('sql_login')
            password = data.get('token')
            if user and password:
                return True
    return False


def get_whoami():
    '''
    Запросит АПИ Портала для того, чтобы через керберос аутентификацию получить информацию о текущем пользователе.
    Если проект запущен в локальном режиме, то сгенерирует аутентификацию пользователя, который запустил проект.
    Если проект запущен на веб сервере, то перенесет аутентификацию исходного обрабатываемого запроса.
    '''
    url = WHOAMI_URL
    answer = {}

    # формируем авторизацию
    if _local_development:
        negotiate_details = generate_local_negotiate()
    else:
        request = get_current_request()
        negotiate_details = get_client_negotiate_token(request)
    if negotiate_details:
        headers = {"Authorization": "Negotiate "+negotiate_details}
        # получаем информацию
        
        try:
            resp = requests.get(url, headers=headers)
            answer = loads(resp.text)
        except Exception as e:
            print(str(e))
    return answer


def request_get_with_negotiate(request, **kwargs):
    '''
    Делает новый запрос GET на переданный url с использованием аутентификации исходного запроса
    '''
    message = ''
    response = None
    target_url = kwargs.get('url')
    if target_url:
        try:
            negotiate_details = get_client_negotiate_token(request)
            if negotiate_details == '':
                negotiate_details = generate_local_negotiate()
            headers = {"Authorization": "Negotiate "+negotiate_details}

            response = requests.get(target_url, headers=headers)
            message += str(response.status_code)

        except requests.RequestException as e:
            message += str(e)

    return response, message
