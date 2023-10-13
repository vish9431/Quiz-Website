from questgen.extractor import Extractor
import re
from nltk import sent_tokenize
from questgen.options import OptionsGenerator


class Generator:

    def __init__(self, num_questions=10, num_options=4):
        self.options_generator = None
        self.questions = None
        self.num_questions = num_questions
        self.num_options = num_options
        self.extractor = Extractor(num_questions)

    def clean_data(self, data):
        data = data.replace('\n', ' ')
        sentences = sent_tokenize(data)
        cleaned_data = ''

        for sentence in sentences:
            clean_sentence = re.sub(r'([^\s\w]|_)+', '', sentence)
            clean_sentence = re.sub(' +', ' ', clean_sentence)
            cleaned_data += clean_sentence

            if cleaned_data[-1] == ' ':
                cleaned_data[-1] = '.'
            else:
                cleaned_data += '.'

            cleaned_data += ' '

        return cleaned_data

    def generate_questions(self, document):
        document = self.clean_data(document)
        self.questions = self.extractor.get_questions_dict(document)
        self.options_generator = OptionsGenerator(document)

        for i in range(self.num_questions):
            if i+1 not in self.questions:
                continue
            self.questions[i+1]['options'] = self.options_generator.all_options(
                self.questions[i+1]['answer'],
                self.num_options
            )

        return self.questions
