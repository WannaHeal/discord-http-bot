import enum


class DiscordInteractionType(enum.IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class DiscordInteractionCallbackType(enum.IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
