import gensim.downloader as gd
import nltk
from lsutils import *
from bornrule import BornClassifier
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline


class W2V:

	model_name = None
	model = None

	@staticmethod
	def init():
		W2V.model_name = "word2vec-google-news-300"
		W2V.model = gd.load(W2V.model_name)

	@staticmethod
	def get_most_relevant_words(target_word, document):
		
		threshold = 0.27

		#nltk.download('averaged_perceptron_tagger')

		dw = nltk.word_tokenize(document.lower())
		dw_tagged = nltk.pos_tag(dw)

		accepted_tags = ["CD", "FW", "JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS", "PDT", "RB", "RBR", "RBS", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]

		document_words = [ t[0] for t in dw_tagged if t[1] in accepted_tags ]

		#target_vector = model[target_word]
		#document_vectors = [model[word] for word in document_words if word in model]
		
		similar_words = set()

		for word in document_words:

			try:
				target_vector = W2V.model[word]
			except:
				continue

			if W2V.model.similarity(target_word, word) >= threshold:
				similar_words.add(word)

		return similar_words

	

class Born:

	X_tfidf = None
	y = None
	clf = None
	
	labels = None
	words = None

	@staticmethod
	def init(X, y):
		vectorizer = TfidfVectorizer()
		Born.X_tfidf = vectorizer.fit_transform(X)
		Born.y = y
		Born.clf = BornClassifier()
		Born.clf.fit(Born.X_tfidf, y)
		Born.labels = list(set(y))
		Born.words = vectorizer.get_feature_names_out()

	@staticmethod
	def get_kw_from_sample(sample_idx, sample, target_genre):
		
		expl = Born.clf.explain(Born.X_tfidf[sample_idx])
		vals = expl.toarray()

		#Filtering only for words allowed (like in w2v)
		nltk.download('averaged_perceptron_tagger')
		dw = nltk.word_tokenize(sample.lower())
		dw_tagged = nltk.pos_tag(dw)
		accepted_tags = ["CD", "FW", "JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS", "PDT", "RB", "RBR", "RBS", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
		doc_allowed_words = [ t[0] for t in dw_tagged if t[1] in accepted_tags ]
		
		sample_words = set()
		
		n_words = len(vals)

		for i in range(0, n_words):
			
			#Holding the word only if it gives the best score for the target genre
			wg = list(vals[i])
			idx = wg.index(max(wg))

			#Taking only the words in which the max probability score is for the target genre and the score is greater than the threshold
			if Born.labels[idx] == target_genre and Born.words[i] in doc_allowed_words and vals[i][idx] > 0:
				sample_words.add(Born.words[i])

		return list(sample_words)

class TC:

	X_tfidf = None
	y = None
	clf = None
	
	labels = None
	words = None

	threshold = 0.25

	@staticmethod
	def init(X, y):
		vectorizer = TfidfVectorizer()
		TC.X_tfidf = vectorizer.fit_transform(X)
		TC.y = y
		TC.clf = LinearSVC(dual="auto")
		TC.clf.fit(TC.X_tfidf, y)
		TC.labels = list(set(y))
		TC.words = vectorizer.get_feature_names_out()

	@staticmethod
	def get_kw_from_sample(sample, target_genre):
		
		classes = list(TC.clf.classes_)
		wfg = TC.clf.coef_[classes.index(target_genre)]
		vals = dict(zip(TC.words, wfg))

		#Filtering only for words allowed (like in w2v)
		dw = nltk.word_tokenize(sample.lower())
		dw_tagged = nltk.pos_tag(dw)
		accepted_tags = ["CD", "FW", "JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS", "PDT", "RB", "RBR", "RBS", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
		doc_allowed_words = [ t[0] for t in dw_tagged if t[1] in accepted_tags ]
		
		sample_words = set()

		#Looping through the allowed words of the document, searching the most relevant keywords for the song
		for word in doc_allowed_words:

			if word in vals and vals[word] > TC.threshold:
				sample_words.add(word)

		return list(sample_words)

class Comparer:

	@staticmethod
	def get_genre_keywords(docs, genres):

		#Number of the top representative keywords to hold for the docs
		num_kw = 30

		vectorizer = TfidfVectorizer()

		tfidf_matrix = vectorizer.fit_transform(docs)
		feature_names = vectorizer.get_feature_names_out()

		data = tfidf_matrix.toarray()

		keywords = dict()

		i = 0
		for genre_tfidf in data:
			merges = list(zip(feature_names, genre_tfidf))
			kwds = [ x[0] for x in (list(sorted(merges, key=lambda item: item[1], reverse=True))[0:num_kw])]
			keywords[genres[i]] = kwds
			i += 1

		return keywords
	
class ZS:

	classifier = None
	sents = None

	loaded = False

	@staticmethod
	def init():
		if not ZS.loaded:
			ZS.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
			ZS.sents = ["positive", "negative"]
			ZS.loaded = True

	@staticmethod
	def get_sentiment(text):

		#Retrieving the sentiment: text could be both a song or a string composed of the keywords
		result = ZS.classifier(text, candidate_labels=ZS.sents)

		return result["labels"][0]

	