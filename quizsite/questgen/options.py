import gensim
import gensim.downloader as api
from gensim.models import Word2Vec
from nltk.tokenize import sent_tokenize, word_tokenize
import random
import numpy as np


class OptionsGenerator:

    def __init__(self, document):
        self.all_sim = None
        self.model = api.load('glove-wiki-gigaword-100')
        self.all_words = []
        for sentence in sent_tokenize(document):
            self.all_words.extend(word_tokenize(sentence))

        self.all_words = list(set(self.all_words))

    def all_options(self, answer, num_options):
        options_dict = dict()
        try:
            similar_words = self.model.similar_by_word(answer, topn=15)[::-1]

            for i in range(num_options):
                options_dict[i] = similar_words[i][0]

        except BaseException:
            self.all_sim = []
            for word in self.all_words:
                if word not in answer:
                    try:
                        self.all_sim.append((self.model.similarity(answer, word), word))
                    except BaseException:
                        self.all_sim.append((0.0, word))

                else:
                    self.all_sim.append((-1, word))

            self.all_sim.sort(reverse=True)

            for i in range(num_options):
                options_dict[i] = self.all_sim[i][1]

        replacement = random.randint(1, num_options-1)
        options_dict[replacement] = answer
        return options_dict
