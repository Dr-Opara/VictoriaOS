from enum import Enum


class Intent(str, Enum):
    GENERAL = "general"
    EMAIL = "email"
    CALENDAR = "calendar"
    WEATHER = "weather"
    TRAVEL = "travel"
    BMW = "bmw"
    HOME = "home"
    PHONE = "phone"
    UNKNOWN = "unknown"