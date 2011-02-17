import utils
from utils import printv
from relations import *
import time

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

TERM_CUTOFF = 30

#todo make topic viewer inherited so as to require some of these functions
def validate():
    return True

def get_doc_display(doc):
        url = "http://en.wikipedia.org/wiki/" + doc.get_safe_title()
        url2 = "http://en.wikipedia.org/wiki/" + doc.title.replace(" ", "_").replace("&amp;", '&')
        
        f = ''
        try:
            f = opener.open(url)
        except urllib2.HTTPError:
            try:
                f = opener.open(url2)
            except:
                return "This page could not be found."
        site = f.read()
        
        # get past the unwanted content at the start of the html file
        end_cur = site.find('</h1>')

        start_cur = site[end_cur:].find('<table class="vertical-navbox nowraplinks"')
        while (start_cur != -1):
            while (start_cur != -1):
                new_end_cur = end_cur + start_cur + site[end_cur + start_cur:].find('</table>')
                start_cur = site[end_cur + start_cur + len('<table') : new_end_cur].find('<table')
                end_cur = new_end_cur
            start_cur = site[end_cur:].find('<table class="vertical-navbox nowraplinks"')

        # cherrypick desired content, up to a certain length
        new_start_cur = site[end_cur:].find('<p')
        new_end_cur = site[end_cur:].find('</p>')

        pair_key = 0
        pairs = [('<p', '</p>'), ('<span class="mw-headline"', '</span>'), ('<div id="toctitle">', '</div>'), ('<ul>','</ul>')]

        content = ''
        while (new_start_cur != -1 and new_end_cur != -1 and len(content) < 5000):
            content_addition = str(site[end_cur+new_start_cur:end_cur+new_end_cur+len(pairs[pair_key][1])])
            if pair_key == 1:
                content += '\n<h3>' + content_addition + '</h3>'
            else:
                content += '\n' + content_addition

            end_cur = end_cur + new_end_cur + len(pairs[pair_key][1])
            
            new_start_cur = -1
            new_end_cur = -1
            for pair in pairs:
                start_cur = site[end_cur:].find(pair[0])
                if start_cur != -1 and (new_start_cur == -1 or start_cur < new_start_cur):
                    new_start_cur = start_cur
                    new_end_cur = site[end_cur:].find(pair[1])
                    temp_start_cur = new_start_cur
                    count = 0
                    while count <10 and site[end_cur + temp_start_cur + len(pair[0]) : end_cur + new_end_cur].find(pair[0]) != -1:
                        temp_start_cur = temp_start_cur + site[end_cur + temp_start_cur + len(pair[0]):].find(pair[0]) + len(pair[0])
                        new_end_cur = new_end_cur + site[end_cur + new_end_cur + len(pair[1]):].find(pair[1])  + len(pair[1])
                        count += 1
                    pair_key = pairs.index(pair)
        
        # make sure links connect to wikipedia.org properly
        content = content.replace('href="/wiki', 'href="http://www.wikipedia.org/wiki')
        content = content.replace('href="#', 'href="' + url + '#')
        
        return content + '\n<p><a href="' + url + '">Full article&nbsp;&#x25B8;</a></p>'

def get_html_insert(key, relational_db, identifier):
    return_string = ""
    if key == "nav-bar": #TODO: see if this code can be modularized more
        return_string = get_html_navbar()
    elif key == "topic-table":
        return_string = get_xml_topic_table(relational_db)
    elif key == "topic-graph":
        return_string = get_xml_topic_graph(relational_db)
    elif key == "topic-presence-graph":
        return_string = get_xml_topic_presence_graph(relational_db)
    elif key == "term-graph":
        return_string = get_xml_term_graph(relational_db)
    elif key == "term-list":
        return_string = get_xml_term_list_table(relational_db)
    elif key == "term-hidden-list":
        return_string = get_xml_term_hidden_list_table(relational_db)
    elif key == "doc-graph":
        return_string = get_xml_doc_graph(relational_db)
    elif key == "topic-terms-column":
        return_string = get_xml_topic_terms_column(identifier)
    elif key == "topic-docs-column":
        return_string = get_xml_topic_docs_column(relational_db, identifier)
    elif key == "topic-topics-column":
        return_string = get_xml_topic_topics_column(relational_db, identifier)
    elif key == "doc-content":
        return_string = get_xml_doc_content(relational_db, identifier)
    elif key == "doc-topics-column":
        return_string = get_xml_doc_topics_column(relational_db, identifier)
    elif key == "doc-docs-column":
        return_string = get_xml_doc_docs_column(relational_db, identifier)
    elif key == "topic-pie-array":
        return_string = get_js_doc_topic_pie_array(relational_db, identifier)
    elif key == "term-pie-array":
        return_string = get_js_topic_term_pie_array(relational_db, identifier)
    elif key == "term-related-terms-column":
        return_string = get_xml_term_terms_column(relational_db, identifier)
    elif key == "term-related-docs-column":
        return_string = get_xml_term_docs_column(relational_db, identifier)
    elif key == "term-related-topics-column":
        return_string = get_xml_term_topics_column(relational_db, identifier)
    else:
        print "need to add " + key + " to get_html_insert in template"

    
    return return_string

topics_per_row = 3 #make this variable?

def split_topics(topics):
    topic_sets = []
    for i in range(0, len(topics) - 1, topics_per_row):
        if (len(topics) < i + topics_per_row):
            appendage = topics[i:]
            for j in range(topics_per_row - len(appendage)):
                appendage.append('')
            topic_sets.append(appendage)
        else:
            topic_sets.append(topics[i:i + topics_per_row])
    return topic_sets

def get_xml_topic_table(relations):#TODO: figure out better way to handle relations/db
    topics = relations.get_topics()

    topic_table = "<table>\n"
    
    topic_sets = split_topics(topics)
    for topic_set in topic_sets:
        topic_table += '<tr class="titles">\n'
        for top in topic_set:
            if top == '':
                    topic_table += '<td class="blank"></td>\n'
            else:
                topic_table += '<td onclick="window.location.href=\'../topics/' + top.get_safe_title() + '.html\'">' + top.title + '</td>\n'
        topic_table += '</tr>\n'
        
        num_terms = 5 #TODO:set this elsewhere, perhaps a template file pref?
        for i in range(num_terms):
            topic_table += '<tr>'
            for top in topic_set:
                if top == '' or top.get_term(i) == None:
                    topic_table += '<td class="blank"></td>\n'
                else:
                    topic_table += '<td onclick="window.location.href=\'../terms/' + top.get_term(i).title + '.html\'">' + top.get_term(i).title + '</td>\n'
            topic_table += '</tr>'

        topic_table += '<tr class="spacer">'
        for top in topic_set:
            topic_table += '<td></td>'
        topic_table += '<tr>\n'
    
    topic_table += "</table>\n"
    return topic_table

def get_xml_topic_graph(relations):
    topics = relations.get_topics() 
    
    topics_table = ""
    terms_table = ""
    
    for topic in topics:
        topics_table += '<table width="250px"><tr><td class="dark-hover" onclick="window.location.href=\'../topics/' + topic.get_safe_title() + '.html\'">' + topic.title + '</td></tr></table>\n'
        terms_table += '<table width="100%" class="high-contrast-table"><tr>\n'
        terms = relations.get_topic_terms(topic)
        term_keys = terms.keys()
        term_keys.sort(lambda x, y: -cmp(terms[x], terms[y]))
        
        total_percent = 0
        remaining_terms = ''
        
        for term in term_keys:
            per = topic.get_relative_percent(term)
            if (per != 0):
                terms_table += '<td class="clickable" width="' + str(per*100) + '%" title="' + term.title + '" onclick="window.location.href=\'../terms/' + term.get_safe_title() + '.html\'"></td>\n'
                total_percent += per
            else:
                if remaining_terms == '':
                    remaining_terms = term.title
                elif len(remaining_terms) < 150: #make 150 a const
                    remaining_terms += ', ' + term.title
                else:
                    break

        if len(remaining_terms) >= 150:
            remaining_terms += '...'

        if (100 - total_percent) > 0:
            terms_table += '<td width="' + str((1 - total_percent)*100) + '%" title="' + remaining_terms + '">&nbsp;</td>\n'
        
        terms_table += '</tr></table>\n'

    topic_graph = '<table width="100.0%">\n<tr><td>\n\n' + topics_table + '\n</td><td class="bars">\n' + terms_table + '\n</td></tr>\n</table>'
    return topic_graph

def get_xml_topic_presence_graph(relations):
    topics = relations.get_topics() 
    
    topic_table = '<table width="100%">\n'
    
    max_overall_score = relations.get_overall_score(topics[0])
    for topic in topics:
        overall_topic_score = relations.get_overall_score(topic)
        width = overall_topic_score / max_overall_score * 100.0
        topic_table += '<tr><td><table width="' + str(width)  + '%" ><tr><td class="high-contrast" title="' + str(int(overall_topic_score)) + '"onclick="window.location.href=\'../topics/' + topic.get_safe_title() + '.html\'">' + topic.title + '</td></tr></table></td></tr>\n'
    
    topic_table += '</table>'
    return topic_table

def get_xml_term_graph(relations):
    terms = relations.get_terms()
    
    terms_table = ""
    topics_table = ""
    
    for term in terms:
        terms_table += '<table width="100.0%"><tr><td class="dark-hover"><a href="../terms/' + term.get_safe_title() + '.html">' + term.title + '</a></td></tr></table>\n'
        topics_table += '<table class="high-contrast-table" width="100.0%"><tr>\n'
        topics = relations.get_related_topics(term)
        topic_keys = topics.keys()
        topic_keys.sort(lambda x, y: cmp(topics[x], topics[y]))
        
        total_percent = 0
        remaining_topics = ''
        
        for topic in topic_keys:
            per = relations.get_relative_percent(topic, term)
            if (per != 0):
                topics_table += '<td class="clickable" width="' + str(per * 100) + '%" title="' + topic.title + '" onclick="window.location.href=\'../topics/' + topic.get_safe_title() + '.html\'"></td>\n'
                total_percent += per
            else:
                if remaining_topics == '':
                    remaining_topics = topic.title
                elif len(remaining_topics) < 150:
                    remaining_topics += ', ' + topic.title

        if len(remaining_topics) >= 150:
            remaining_topics += '...'

        if remaining_topics != '' and (100 - total_percent) > 0:
            topics_table += '<td width="' + str((1 - total_percent) * 100) + '%" title="' + remaining_topics + '">&nbsp;</td>\n'
        
        topics_table += '</tr></table>\n'

    term_graph = '<table width="100.0%">\n<tr><td width="20.0%">\n\n' + terms_table + '\n</td><td class="bars">\n' + topics_table + '\n</td></tr>\n</table>'
    return term_graph

def get_xml_term_list_table(relations):
    terms = relations.get_terms()
    
    terms_table = '<div ><table onmouseover="show_count_bar()" onmouseout="hide_count_bar()">\n'
    for i in range(0, len(terms), 8):
        terms_table += '<tr>\n'
        for j in range(8):
            if (i + j) < len(terms):
                term_count = relations.get_term_count(terms[i+j])
                terms_table += '<td title="' + str(int(term_count)) + '" onclick="window.location.href=\'../terms/' + terms[i+j].get_safe_title() + '.html\'" onmouseover="count_adjust(' + str(100.0*(term_count - relations.term_score_range[0]) /(relations.term_score_range[1] - relations.term_score_range[0])+1) + ')">' + terms[i+j].title + '</td>\n'
            else:
                terms_table += '<td class="blank"></td>'
        terms_table += '</tr>\n'
    terms_table += '</table></div>\n'

    return terms_table

def get_xml_term_hidden_list_table(relations):
    terms_hidden_table = '<div onmouseover="show_count_bar()" onmouseout="hide_count_bar()"><table class="hidden"><tr><td class="count"></td><td class="total"></td>\n</tr></table></div>\n'

    return terms_hidden_table

def get_xml_topic_terms_column(topic):
    topic_column = ""
    
    term_no = 0
    for term in topic.get_terms(TERM_CUTOFF):
        topic_column += '<tr class="list"><td onclick="window.location.href=\'../terms/' + term.get_safe_title() + '.html\'">' + term.title + '</td></tr>\n'
        term_no += 1

    return topic_column

def get_xml_doc_graph(relations):
    docs = relations.get_docs()
    
    docs_table = ""
    topics_table = ""
    
    for doc in docs:
        docs_table += '<table width="100.0%"><tr><td class="dark-hover"><a href="../docs/' + doc.get_safe_title() + '.html">' + doc.title + '</a></td></tr></table>\n'
        topics_table += '<table class="high-contrast-table" width="100.0%"><tr>\n'
        topics = relations.get_related_topics(doc)
        topic_keys = topics.keys()
        topic_keys.sort(lambda x, y: -cmp(topics[x], topics[y]))
        
        total_percent = 0
        remaining_topics = ''
        
        total_score_sum = 0
        for key in topic_keys:
            total_score_sum += topics[key]
        
        for topic in topic_keys:
            per = topics[topic] / total_score_sum
            if (per != 0):
                topics_table += '<td class="clickable" width="' + str(per * 100) + '%" title="' + topic.title + '" onclick="window.location.href=\'../topics/' + topic.get_safe_title() + '.html\'"></td>\n'
                total_percent += per
            else:
                if remaining_topics == '':
                    remaining_topics = topic.title
                elif len(remaining_topics) < 150:
                    remaining_topics += ', ' + topic.title

        if len(remaining_topics) >= 150:
            remaining_topics += '...'

        if remaining_topics != '' and (100 - total_percent) > 0:
            topics_table += '<td width="' + str((1 - total_percent) * 100) + '%" title="' + remaining_topics + '">&nbsp;</td>\n'
        
        topics_table += '</tr></table>\n'

    doc_graph = '<table width="100.0%">\n<tr><td width="50%">\n\n' + docs_table + '\n</td><td class="bars">\n' + topics_table + '\n</td></tr>\n</table>'
    return doc_graph
    
def get_xml_topic_docs_column(relation, topic):
    doc_column = ""
    
    docs = relation.get_related_docs(topic)
    doc_keys = docs.keys()
    doc_keys.sort(lambda x, y: -cmp(docs[x], docs[y]))
    for doc in doc_keys[0:100]:
        doc_column += '<tr class="list"><td onclick="window.location.href=\'../docs/' + doc.get_safe_title() + '.html\'">' + doc.title + '</td></tr>\n'

    return doc_column

def get_xml_doc_topics_column(relation, doc): #TODO: some of these functions can be collapsed/generalized
    topic_column = ""
    
    topics = relations.get_related_topics(relation, doc)
    topic_keys = topics.keys()
    topic_keys.sort(lambda x, y: -cmp(topics[x], topics[y])) 
    topic_num = 0
    for top in topic_keys:
        topic_column += '<tr class="list"><td id="' + top.get_safe_title() + '" onmouseover="highlight(' + str(topic_num) + ')" onmouseout="unhighlight()" onclick="window.location.href=\'../topics/' + top.get_safe_title() + '.html\'">' + top.title + '</td></tr>\n'
        topic_num += 1

    return topic_column

def get_xml_doc_content(relation, doc):
    content = doc.get_display()
    content = content.replace("\n\n", "</p>\n\n<p>")
    return content

def get_xml_doc_docs_column(relation, parent_doc):
    doc_column = ""
    
    time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
    
    docs = relation.get_related_docs(parent_doc)
    doc_keys = docs.keys()
    doc_keys.sort(lambda x, y: cmp(docs[x], docs[y]))
    for doc in doc_keys[:30]:
        doc_column += '<tr class="list"><td onclick="window.location.href=\'../docs/' + doc.get_safe_title() + '.html\'">' + doc.title + '</td></tr>\n'

    return doc_column

def get_xml_topic_topics_column(relations, topic):
    topic_column = ""
    
    topics = relations.get_related_topics(topic)
    topic_keys = topics.keys()
    topic_keys.sort(lambda x, y: cmp(topics[x], topics[y])) 
    for top in topic_keys:
        topic_column += '<tr class="list"><td onclick="window.location.href=\'../topics/' + top.get_safe_title() + '.html\'">' + top.title + '</td></tr>\n'

    return topic_column

def get_js_doc_topic_pie_array(relations, doc):
    array_string = "["
    
    topics = relations.get_related_topics(doc)
    topic_keys = topics.keys()
    topic_keys.sort(lambda x, y: -cmp(topics[x], topics[y]))
    key_count = 0
    for key in topic_keys:
        array_string += "[" + str(topics[key]) + ", " + "\"../topics/" + key.get_safe_title() + ".html\", \"" + key.get_safe_title() + "\"]"
        key_count += 1
        if key_count != len(topic_keys):
            array_string += ", "
    
    array_string += "]"
    
    return array_string

def get_js_topic_term_pie_array(relations, topic):
    array_string = "["
    
    terms = topic.get_terms(TERM_CUTOFF)
    term_count = 0
    term_score_total = 0
    for term in terms:
        rel_percent = topic.terms[term]
        array_string += "[" + str(rel_percent) + ", " + "\"../topics/" + term.get_safe_title() + ".html\", \"" + term.get_safe_title() + "\"]"
        term_count += 1
        term_score_total += rel_percent
        if term_count != len(terms):
            array_string += ", "
    if term_score_total < topic.term_score_total:
        array_string += ', [' + str(topic.term_score_total-term_score_total) + ', \"\", \"\"]'
    
    array_string += "]"
    
    return array_string

def get_html_navbar():
    navbar = '<div id="navigation">\n<hr noshade>\n<table><tr>\n    <td class="navtext">Browse&nbsp;&#x25B8;</td> \n    <td class="linked"><a>Topics</a>\n      <ul> \n        <li><a href="../browse/topic-list.html">List of Terms</a></li> \n        <li><a href="../browse/topic-graph.html">Term Distributions</a></li> \n        <li><a href="../browse/topic-presence.html">Relative Presence</a></li>\n      </ul> \n    </td> \n    <td class="linked"><a>Documents</a>\n      <ul>\n        <li><a href="../browse/doc-graph.html">Topic Distributions</a></li>\n      </ul> \n    </td>\n    <td class="linked"><a>Terms</a>\n      <ul> \n        <li><a href="../browse/term-list.html">List by Frequency</a></li> \n        <li><a href="../browse/term-graph.html">Topic Distributions</a></li> \n       </ul> \n    </td>\n    <td class="linked"><a>About</a>\n      <ul>\n        <li><a href="http://www.cs.princeton.edu/~blei/lda-c/">LDA</a></li>\n      </ul> \n    </td>\n    \n    </td>\n    <td></td>\n    <td class="searchbar"> Search&nbsp;&#x25B8;</td>\n    <td class="searchbar"><input type="text" name="search" size="20" onkeypress="handleKeyPress(event)"><span onclick="doSearch()"></span>\n    </td>\n</tr></table>\n</div>'# \n        <li><a href="../browse/term-list.html">Alphabetical List</a></li>
#       <li><a href="../browse/term-doc-graph.html">Graph of Document Distribution</a></li>\n
    return navbar

def get_xml_term_terms_column(relations, term):
    terms_column = ""
    
    terms = relations.get_related_terms(term)
    term_keys = terms.keys()
    term_keys.sort(lambda x, y: cmp(terms[x], terms[y])) 
    for t in term_keys[:20]:
        terms_column += '<tr class="list"><td onclick="window.location.href=\'../terms/' + t.get_safe_title() + '.html\'">' + t.title + '</a></td></tr>\n'
    
    return terms_column

def get_xml_term_docs_column(relations, term):
    doc_column = ""
    
    docs = relations.get_related_docs(term)
    doc_keys = docs.keys()
    
    doc_keys.sort(lambda x, y: -cmp(docs[x], docs[y]))
    for doc in doc_keys[:20]:
        doc_column += '<tr class="list"><td onclick="window.location.href=\'../docs/' + doc.get_safe_title() + '.html\'">' + doc.title + '</td></tr>\n'

    return doc_column

def get_xml_term_topics_column(relations, term):
    topic_column = ""
    
    topics = relations.get_related_topics(term)
    topic_keys = topics.keys()
    topic_keys.sort(lambda x, y: -cmp(topics[x], topics[y])) 
    for top in topic_keys[:20]:
        topic_column += '<tr class="list"><td onclick="window.location.href=\'../topics/' + top.get_safe_title() + '.html\'">' + top.title + '</td></tr>\n'

    return topic_column

