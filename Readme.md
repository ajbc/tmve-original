# TMVE 0.1: topic model visualization engine
Depending on your objective, you may want to check out my [more recent code for dynamic visualization](https://github.com/ajbc/tmv), as this code creates static pages and is not actively maintained.

### Demo
###### a browser of 100K Wikipedia articles
[This Wikipedia browser](http://www.princeton.edu/~achaney/tmve/wiki100k/browse/topic-presence.html)
was produced by using the results of running [David Blei's LDA-C](http://www.cs.princeton.edu/~blei/lda-c/) on 100,000 Wikipedia articles to find 50 topics.


### Tutorial
###### to produce a browser similar to the demo above</h4>
First, download build [LDA-C](http://www.cs.princeton.edu/~blei/lda-c/) and run it on a dataset.  For the above demo, the command looked something like:
```bash
./lda est 1/50 50 settings.txt wiki/100K/word_count.dat seeded wiki-100k-lda
```
Next, the LDA data will need to be processed and put into a database; for this purpose, use the database generator provided in the `lib` folder.  Again, for the demo, the command to run the generator would be as follows.
```bash
python generate_db.py 100k_wiki_db wiki/100K/word_count.dat wiki-100k-lda/final.beta wiki-100k-lda/final.gamma wiki/100K/vocab.dat wiki/100K/dmap.dat
```
The word_count, vocab, and dmap files have the same format as LDA-c; check out it's [documentation](http://www.cs.princeton.edu/~blei/lda-c/readme.txt) and [example data](http://www.cs.princeton.edu/~blei/lda-c/ap.tgz).
+ `vocab.dat` is like `vocab.txt`, where the word's index matches its line number
+ `word_count.dat` contains the word counts for each document (see lda-c doc for format details); example `ap.dat`.
+ `dmap.dat` contains the full document content, and so would be kind of like
`ap.txt`, but with one line per document.  The idea is that people would
modify the write_docs function in generate_db.py to match their
document structure.

This DB generation can take a while for large datasets.  As a short-cut, a demo 1k database is included in the `demo` folder, entitled `1k_demo_db`.

Finally, TMVE needs to be run with a project file, which specifies what database and template to use.  Templates control how the data is displayed; in this case, a basic browser is produced.  The included project file `wiki_project_demo.tmv` is set up to run with the demo database.

The command to run TMVE with the demo project is fairly simple:
```bash
python src/tmve.py demo/wiki_project.tmv
```

Or, for more information as the script runs, the verbose mode is helpful:
```bash
python src/tmve.py -v demo/wiki_project.tmv
```

For the demo project, you will need to be connected to the Internet while TMVE generates the document pages as it must pull content from Wikipedia.  When this is done, you should have a local browser (in the demo directory) like the demo above, but a little smaller.


### Making Changes
###### adapting to other datasets and other topic model types

Creating a new template will allow you to view your data in an alternative fashion.  To do so, take a look at the BasicBrowser template included in the TMVE source download.

To use another dataset, you will need to change the way documents are displayed.  This is currently hard-coded into the `BasicBrowser.py` file, in the function `get_doc_display`.

To try different topic models, only the database generator needs to be changed.  Depending on how the output differs from LDA-C, the work to do this may be minimal.

---
Copyright Allison J. B. Chaney, Princeton University 2010-2015
