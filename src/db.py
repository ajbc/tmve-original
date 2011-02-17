import sqlite3

class db:
    def __init__(self, filename):
        self.con = sqlite3.connect(filename)
        self.cur = self.con.cursor()

    def __del__(self):
        self.con.commit()
        self.cur.close()
    
    def get_topics_info(self):
        self.cur.execute('SELECT * FROM topics')
        return self.cur.fetchall()

    def get_topic_info(self, topic_id):
        self.cur.execute('SELECT * FROM topics WHERE id=?', [topic_id])
        return self.cur.fetchall()

    def get_term_info(self):
        self.cur.execute('SELECT * FROM terms')
        return self.cur.fetchall()

    def get_term_title(self, term_id):
        self.cur.execute('SELECT title FROM terms WHERE id=?', [term_id])
        return self.cur.fetchall()

    def get_docs_info(self):
        self.cur.execute('SELECT * FROM docs')
        return self.cur.fetchall()

    def get_doc_info(self, doc_id):
        self.cur.execute('SELECT * FROM docs WHERE id=?', [doc_id])
        return self.cur.fetchall()

    def get_topic_terms(self, topic_id):
        self.cur.execute('SELECT * FROM topic_term WHERE topic=?', [topic_id])
        return self.cur.fetchall()

    def get_topic_docs(self, topic_id):
        self.cur.execute('SELECT * FROM doc_topic WHERE topic=?', [topic_id])
        return self.cur.fetchall()

    def get_term_docs(self, term_id):
        self.cur.execute('SELECT * FROM doc_term WHERE term=?', [term_id])
        return self.cur.fetchall()

    def get_topic_topics(self, topic_id):
        self.cur.execute('SELECT * FROM topic_topic WHERE topic_a=? OR topic_b=?', [topic_id, topic_id])
        return self.cur.fetchall()

    def get_doc_docs(self, doc_id):
        self.cur.execute('SELECT * FROM doc_doc WHERE doc_a=? OR doc_b=?', [doc_id, doc_id])
        return self.cur.fetchall()

    def get_doc_topics(self, doc_id):
        self.cur.execute('SELECT * FROM doc_topic WHERE doc=?', [doc_id])
        return self.cur.fetchall()

    def get_term_terms(self, term_id):
        self.cur.execute('SELECT * FROM term_term WHERE term_a=? OR term_b=?', [term_id, term_id])
        return self.cur.fetchall()

    def get_term_topics(self, term_id):
        self.cur.execute('SELECT * FROM topic_term WHERE term=?', [term_id])
        return self.cur.fetchall()
