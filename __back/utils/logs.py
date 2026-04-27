import logging

def order_for_friend_log():
    # Создаем logger
    logger = logging.getLogger('OrderForFriend')
    logger.setLevel(logging.INFO)

    # Handler для INFO
    file_handler_actions = logging.FileHandler('order_for_friend.log', mode='a', encoding='utf-8')
    file_handler_actions.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - ACTIONS: %(message)s'))
    file_handler_actions.setLevel(logging.INFO)
    logger.addHandler(file_handler_actions)
    return logger


friend_logger = order_for_friend_log()


def help_log():
    # Создаем logger
    logger = logging.getLogger('HelpLog')
    logger.setLevel(logging.INFO)

    # Handler для INFO
    file_handler_actions = logging.FileHandler('help.log', mode='a', encoding='utf-8')
    file_handler_actions.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - ACTIONS: %(message)s'))
    file_handler_actions.setLevel(logging.INFO)
    logger.addHandler(file_handler_actions)
    return logger


help_logger = help_log()
