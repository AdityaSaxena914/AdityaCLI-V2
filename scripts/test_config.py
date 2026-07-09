from adityacli.logging import get_logger

logger1 = get_logger("provider")
logger2 = get_logger("tool")

print(logger1.handlers[1] is logger2.handlers[1])