import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


class Extractor:

    def __init__(self, num_questions):
        self.filtered_sentences = None
        self.unfiltered_sentences = None
        self.candidate_keywords = None
        self.word_score = dict()
        self.sentence_max_score = dict()
        self.candidate_scores = []

        self.num_questions = num_questions
        self.stop_words = set(stopwords.words('english'))
        self.ner_tagger = spacy.load('en_core_web_md')
        self.vectorizer = TfidfVectorizer()
        self.questions_dict = dict()

    def get_questions_dict(self, document):
        self.candidate_keywords = self.candidate_entities(document)

        self.set_tfidf_scores(document)

        self.rank_keywords()

        self.form_questions()

        return self.questions_dict

    def candidate_entities(self, document):
        entities = self.ner_tagger(document)
        entity_list = [entity.text for entity in entities.ents]

        return list(set(entity_list))

    def set_tfidf_scores(self, document):
        self.unfiltered_sentences = sent_tokenize(document)
        self.filtered_sentences = [self.filter_sentence(sentence) for sentence in self.unfiltered_sentences]

        vector = self.vectorizer.fit_transform(self.filtered_sentences)
        features = self.vectorizer.get_feature_names_out()
        matrix = vector.todense().tolist()

        for i in range(len(features)):
            word = features[i]
            self.sentence_max_score[word] = ""
            total = 0
            cur_max = 0

            for j in range(len(self.unfiltered_sentences)):
                total += matrix[j][i]
                if matrix[j][i] > cur_max:
                    cur_max = matrix[j][i]
                    self.sentence_max_score[word] = self.unfiltered_sentences[j]

            self.word_score[word] = total / len(self.unfiltered_sentences)

    def rank_keywords(self):
        for candidate in self.candidate_keywords:
            self.candidate_scores.append([
                self.keyword_score(candidate),
                candidate,
                self.sentence_for_keyword(candidate)
            ])

        self.candidate_scores.sort(reverse=True)

    def form_questions(self):
        used = list()
        i = 0
        j = 1
        candidate_count = len(self.candidate_scores)

        while j <= self.num_questions and i < candidate_count:
            candidate_score = self.candidate_scores[i]

            if candidate_score[2] not in used:
                used.append(candidate_score[2])

                self.questions_dict[j] = {
                    'question': candidate_score[2].replace(candidate_score[1],
                                                           '_'*len(candidate_score[1])),
                    'answer': candidate_score[1]
                }
                j += 1
            i += 1

    def filter_sentence(self, sentence):
        words = word_tokenize(sentence)
        return ' '.join(w for w in words if w not in self.stop_words)

    def keyword_score(self, keyword):
        score = 0
        for word in word_tokenize(keyword):
            if word in self.word_score:
                score += self.word_score[word]
        return score

    def sentence_for_keyword(self, keyword):
        words = word_tokenize(keyword)
        for word in words:
            if word not in self.sentence_max_score:
                continue

            sentence = self.sentence_max_score[word]

            check = True
            for w in words:
                if w not in sentence:
                    check = False

            if check:
                return sentence

        return ''
