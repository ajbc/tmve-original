from db import db
import math
import urllib2
import sys

template = None

def import_template(template_name):
    global template
    sys.path.append("templates/" + template_name)
    template = __import__(template_name)

class Document:
    def __init__(self, doc_id, title):
        self.id = doc_id
        self.title = str(title)

    def get_safe_title(self):
        safe_title = self.title.replace(" ", "_").replace("\'", "_").replace("/", "-")
        return safe_title

    def get_display(self):
        return template.get_doc_display(self)

class Topic:
    def __init__(self, rel, topic_id, title):
        self.rel = rel
        self.topic_id = topic_id
        self.title = str(title)
        self.terms = {}
        self.ranked_terms = []
        self.term_score_total = 0

    def get_term(self, rank):
        if self.terms == {}:
            self.terms = self.rel.get_topic_terms(self)
            self.ranked_terms = sorted(self.terms, key=self.terms.get, reverse=True)
        
        if rank >= len(self.ranked_terms):
            return None
        
        return self.ranked_terms[rank]

    def get_terms(self, cutoff):
        if self.terms == {}:
            self.terms = self.rel.get_topic_terms(self)
            self.ranked_terms = sorted(self.terms, key=self.terms.get, reverse=True)
        
        return self.ranked_terms[:cutoff]#TODO: cutoff should be based on merit, not just position

    def get_safe_title(self):
        safe_title = self.title.replace(" ", "_").replace("\'", "")
        return safe_title

    def get_relative_percent(self, term):
        self.get_terms(10)
        rank = self.ranked_terms.index(term)
        if self.term_score_total == 0:
            for t in self.ranked_terms:
                self.term_score_total += math.exp(self.terms[t])

        percent = (math.exp(self.terms[term]) / self.term_score_total)

        if percent < .005:
            return 0
        else:
            return percent
        

class Term:
    all_terms = {}

    def __init__(self, term_id, title):
        self.id = term_id
        self.title = str(title)
        Term.all_terms[term_id] = self

    def get_safe_title(self):
        return self.title
        

class relations:
    def __init__(self, mydb):
        self.mydb = mydb
        self.topics = [] # do we need these?
        self.docs = []
        self.terms = []
        self.term_score_range = (0, 0)

    def get_term(self, term_id):
        if Term.all_terms.has_key(term_id):
            return Term.all_terms[term_id]
        else:
            if self.mydb.get_term_title(term_id+1) == []:
                return None
            return Term(term_id, self.mydb.get_term_title(term_id+1)[0][0])

    def get_topics(self):
        if self.topics == []:
            topics_info = self.mydb.get_topics_info()
            for topic_info in topics_info:
                topic_id = topic_info[0] - 1
                title = topic_info[1]
                self.topics.append(Topic(self, topic_id, title))

        self.topics.sort(lambda x, y: -cmp(self.get_overall_score(x), self.get_overall_score(y)))

        return self.topics

    def get_terms(self):
        if self.terms == []:
            terms_info = self.mydb.get_term_info()
            for term_info in terms_info:
                term_id = term_info[0] - 1
                self.terms.append(self.get_term(term_id))
            self.terms.sort(lambda x, y: -cmp(self.get_term_count(x), self.get_term_count(y)))
            self.term_score_range = (self.get_term_count(self.terms[-1]), self.get_term_count(self.terms[0]))
        return self.terms

    def get_topic(self, topic_id):
        topic_info = self.mydb.get_topic_info(topic_id + 1)
        if topic_info == []:
            return None
        title = topic_info[0][1]
        return Topic(self, topic_id, title)

    def get_docs(self):
        if self.docs == []:
            docs_info = self.mydb.get_docs_info()
            for doc_info in docs_info:
                doc_id = doc_info[0] - 1
                title = doc_info[1]
                self.docs.append(Document(doc_id, title))

        return self.docs

    def get_doc(self, doc_id):
        doc_info = self.mydb.get_doc_info(doc_id + 1)
        title = doc_info[0][1]
        return Document(self, doc_id, title)
    
    def get_topic_terms(self, topic):
        topic_terms_info = self.mydb.get_topic_terms(topic.topic_id)
        topic_terms = {}
        for info in topic_terms_info:
            term_id = info[2]
            score = info[3]
            term =self.get_term(term_id)
            if term != None:
                topic_terms[term] = score
        return topic_terms

    def get_related_docs(self, token):
        token_doc_info = []
        if isinstance(token, Topic):
            token_doc_info = self.mydb.get_topic_docs(token.topic_id)
        elif isinstance(token, Document):
            token_doc_info = self.mydb.get_doc_docs(token.id) #TODO: id vs doc_id: make docs, topics, etc more consistent
        elif isinstance(token, Term):
            token_doc_info = self.mydb.get_term_docs(token.id)
        
        token_docs = {}
        for info in token_doc_info:
            doc_id = info[1]
            if isinstance(token, Document) and info[1] == token.id:
                doc_id = info[2]
            score = info[3]
            if score != 0: #TODO: is there better way to do this?
                doc_info = self.mydb.get_doc_info(doc_id+1)
                if doc_info != []:
                    title = doc_info[0][1]
                    token_docs[Document(doc_id, title)] = score
                #if len(token_docs.keys()) > 30:
                    #break
        
        return token_docs
            
    
    def get_related_topics(self, token):
        token_topic_info = []
        if isinstance(token, Topic):
            token_topic_info = self.mydb.get_topic_topics(token.topic_id)
        elif isinstance(token, Document):
            token_topic_info = self.mydb.get_doc_topics(token.id)
        elif isinstance(token, Term):
            token_topic_info = self.mydb.get_term_topics(token.id)
        
        topics = {}
        for info in token_topic_info:
            score = info[3]
            if score != 0 and not (isinstance(token, Document) and score < 1): #check for reverse pairs in topic-topic search
                if (isinstance(token, Topic) and info[2] == token.topic_id) or isinstance(token, Term):
                    t = self.get_topic(info[1])
                    if t != None:
                        topics[t] = score #TODO: topic init needs work
                else:
                    t = self.get_topic(info[2])
                    if t != None:
                        topics[t] = score

        
        return topics

    def get_related_terms(self, term):
        terms_info = self.mydb.get_term_terms(term.id)
        
        terms = {}

        for info in terms_info:
            term_a = info[1]
            term_b = info[2]
            score = info[3]
            if score != 0:
                if info[2] == term.id:
                    terms[self.get_term(info[1])] = score
                else:
                    terms[self.get_term(info[2])] = score 
        
        return terms

    def get_relative_percent(self, topic, term):
        topics = self.get_related_topics(term)
        score = 0
        topica = ''#topics should eb universal instead
        for t in topics.keys():
            score += topics[t];
            if t.topic_id == topic.topic_id:
                topica = t
        return topics[topica] / score
    
    def get_term_count(self, term):
        total = 0;
        for doc_info in self.mydb.get_term_docs(term.id):
            total += doc_info[3]
        return total

    def get_overall_score(self, topic):
        total = 0;
        for doc_info in self.mydb.get_topic_docs(topic.topic_id):
            total += doc_info[3]
        return total
