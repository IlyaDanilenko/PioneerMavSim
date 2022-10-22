from json import load

class Language:
    words = load(open('settings/language.json', 'r', encoding='utf-8'))

    @classmethod
    def get_word(cls, word : str, language = "rus"):
        try:
            if language == "rus":
                return cls.words[word]
            else:
                return cls.words.keys()[list(cls.words.values()).index(word)]
        except KeyError:
            return word