import re
from typing import Literal

from num2words import num2words

_AMHARIC_DIGITS = {
    "0": "ዜሮ",
    "1": "አንድ",
    "2": "ሁለት",
    "3": "ሶስት",
    "4": "አራት",
    "5": "አምስት",
    "6": "ስድስት",
    "7": "ሰባት",
    "8": "ስምንት",
    "9": "ዘጠኝ",
}


def _normalize_english_numbers(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0).replace(",", "")
        try:
            if "." in token:
                return num2words(float(token), lang="en")
            return num2words(int(token), lang="en")
        except Exception:
            return match.group(0)

    return re.sub(r"\d[\d,]*(?:\.\d+)?", repl, text)


def _normalize_amharic_numbers(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0).replace(",", "")
        return " ".join(_AMHARIC_DIGITS.get(ch, ch) for ch in token)

    return re.sub(r"\d[\d,]*(?:\.\d+)?", repl, text)


def normalize_text_for_tts(text: str, lang: Literal["en", "am"]) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""

    text = text.replace("%", " percent " if lang == "en" else " ፐርሰንት ")
    text = text.replace("&", " and " if lang == "en" else " እና ")
    text = text.replace("/", " slash " if lang == "en" else " ")

    if lang == "am":
        return _normalize_amharic_numbers(text)
    return _normalize_english_numbers(text)
