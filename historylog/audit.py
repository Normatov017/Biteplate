import threading


_state = threading.local()


def set_current_user(user):

    _state.user = user


def get_current_user():

    return getattr(
        _state,
        'user',
        None
    )
