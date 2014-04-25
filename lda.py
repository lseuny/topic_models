# -*- coding: utf-8 -*-

import random


NUM_TOPIC     = 30
ALPHA         = 50.0 / NUM_TOPIC
BETA          = 0.01
MAX_DOC_CNT   = -1 # 
ITER_CNT      = 500 # maximum iteration count
SAVE_INTERVAL = 50 # for each SAVE_INTERVAL iteration, intermediate results are stored.
MIN_DOC_TOKEN = 30 # documents with less tokens are ignored
MIN_DF        = 10
MAX_DF_R      = 0.1
INPUT_DOC_PATH= 'input.txt'


# Get a sample based on probability distribution.
# prob: (Multinomial) Probability distribution
def get_one_sample(prob):
	assert abs(sum(prob) - 1.0) < 0.01
	r      = random.random() 
	acc    = [0.0] * len(prob)
	acc[0] = prob[0]
	for i in range(1, len(prob)):
		if r < acc[i-1]:
			return i-1
		acc[i] = acc[i-1] + prob[i]
	return len(prob) - 1


# Get word statistics and document count.
def get_data_stat(path):
	word_cf = {}
	word_df = {}
	f = open(path, 'rt')
	doc_cnt = 0
	for line in f:
		doc_cnt += 1
		if MAX_DOC_CNT > 0 and doc_cnt > MAX_DOC_CNT:
			break
		word_tf   = {}
		token_lst = line.strip().split(' ')
		for token in token_lst:
			if token not in word_tf:
				word_tf[token] = 0
			word_tf[token] += 1
		for word, tf in word_tf.items():
			if word not in word_df:
				word_df[word] = 0
			word_df[word] += 1
			if word not in word_cf:
				word_cf[word] = 0
			word_cf[word] += tf
	f.close()
	return word_cf, word_df, doc_cnt


def main():
	print 'ALPHA: %.2f' % ALPHA
	print 'BETA: %.2f'  % BETA

	word_cf, word_df, doc_cnt = get_data_stat(INPUT_DOC_PATH)
	max_df = int(doc_cnt * MAX_DF_R)

	corpus      = {} # docid -> term list
	lexicon     = {} # word -> termid
	token_cnt   = 0
	termid_word = {} # termid -> word

	f = open(INPUT_DOC_PATH, 'rt')
	for line in f:
		token_lst = line.strip().split(' ')
		if len(token_lst) < MIN_DOC_TOKEN:
			continue
		docid = len(corpus)
		if MAX_DOC_CNT > 0 and docid >= MAX_DOC_CNT:
			break
		corpus[docid] = []
		for token in token_lst:
			if token not in word_df:    continue
			if word_df[token] < MIN_DF: continue
			if word_df[token] > max_df: continue
			token_cnt += 1
			if token not in lexicon:
				lexicon[token] = len(lexicon)
			termid = lexicon[token]
			corpus[docid].append(termid)
			if termid not in termid_word:
				termid_word[termid] = token
	f.close()
	print 'Doc: %d'    % len(corpus)
	print 'Word: %d'   % len(lexicon)
	print 'Token: %d'  % token_cnt
	print 'MAX_DF: %d' % max_df
	print 'MIN_DF: %d' % MIN_DF

	doc_term_topic   = {}
	doc_topic        = [[0 for x in xrange(NUM_TOPIC)] for x in xrange(len(corpus))]
	term_topic       = [[0 for x in xrange(NUM_TOPIC)] for x in xrange(len(lexicon))]
	topic_occurrence = [0] * NUM_TOPIC

	for docid, term_lst in corpus.items():
		doc_term_topic[docid] = [0] * len(term_lst)
		for i in range(len(term_lst)):
			termid                     = term_lst[i]
			topic                      = int(random.random() * NUM_TOPIC) # Random assignment
			doc_term_topic[docid][i]   = topic
			doc_topic[docid][topic]   += 1
			term_topic[termid][topic] += 1
			topic_occurrence[topic]   += 1

	'''
	for t in range(NUM_TOPIC):
		print '%d\t%d' % (t, topic_occurrence[t])
	print 'total: %d' % reduce(lambda x, y: x + y, topic_occurrence)
	'''

	for iteration in range(ITER_CNT):
		print 'Iteration %d' % iteration
		for docid, term_lst in corpus.items():
			for i in range(len(term_lst)):
				termid                     = term_lst[i]
				topic                      = doc_term_topic[docid][i]
				doc_topic[docid][topic]   -= 1
				term_topic[termid][topic] -= 1
				topic_occurrence[topic]   -= 1
				topic_prob                 = [0.0] * NUM_TOPIC
				for t in range(NUM_TOPIC):
					a = (term_topic[termid][t] +  BETA) / (topic_occurrence[t] +  BETA*len(lexicon))
					b = (doc_topic[docid][t]   + ALPHA) / (len(term_lst)       + ALPHA*NUM_TOPIC)
					topic_prob[t] = a * b
				topic_prob                 = map(lambda x: x / sum(topic_prob), topic_prob)
				topic                      = get_one_sample(topic_prob)
				doc_term_topic[docid][i]   = topic
				doc_topic[docid][topic]   += 1
				term_topic[termid][topic] += 1
				topic_occurrence[topic]   += 1

		'''
		for t in range(NUM_TOPIC):
			print '%d\t%d' % (t, topic_occurrence[t])
		print 'total: %d' % reduce(lambda x, y: x + y, topic_occurrence)
		'''

		if SAVE_INTERVAL > 0 and (iteration + 1) % SAVE_INTERVAL == 0:
			f = open('topic_%d.txt' % (iteration + 1), 'wt')
			topic_label = [''] * NUM_TOPIC
			for t in range(NUM_TOPIC):
				b = {}
				for termid in lexicon.values():
					b[termid] = (term_topic[termid][t] + BETA) / (topic_occurrence[t] + BETA*len(lexicon))
				f.write('Topic: %d\n' % t)
				wlst = []
				for termid in sorted(b, key=b.get, reverse=True):
					if b[termid] < 0.002: break
					word = termid_word[termid]
					wlst.append(word)
					f.write('%s(%.1f%%, %d) ' % (word, b[termid] * 100, word_df[word]))
					if len(wlst) >= 10:
						break
				f.write('\n')
				topic_label[t] = '_'.join(wlst[:5])
				#f.write('%s\n\n' % topic_label[t])
			f.close()
			'''
			f = open('doc_term_%d.txt' % (iteration + 1), 'wt')
			for docid, term_lst in corpus.items():
				for i in range(len(term_lst)):
					termid = term_lst[i]
					topic  = doc_term_topic[docid][i]
					f.write('%d\t%s\t%s\n' % (docid, termid_word[termid], topic_label[topic]))
				f.write('\n')
			f.close()
			'''
	

if __name__ == '__main__':
	main()

