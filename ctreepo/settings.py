MASKING_STRING = "******"
NO_VALUE = "<<no-value>>"
TAG_ON_UNDO = "post"
TEMPLATE_SEPARATOR = "UNDO>>"


# тэг для маркировки команд, которые должны быть применены перед основной секций
PRE_TAG = "pre"
# тэг для маркировки команд, которые должны быть применены после основной секции.
# тэг назначается автоматически на глобальные undo-команды
POST_TAG = "post"
# interface eth1
#  shutdown -> предварительные команды (PRE_TAG)
#  speed 100 -> основная секция
#  undo shutdown -> завершающие команды (POST_TAG)
# #
