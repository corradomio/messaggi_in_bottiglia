import re as rexp
import path as p
import functools as ft


def text_from_file(filepath, nl=True, lower=True, encoding='utf-8'):
    """
    
    :param str filepath: file to read 
    :param str encoding: encoding to use in the file reading. Default 'utf-8'
    :param bool nl: if to remove the new line 
    :param bool lower: if to convert all text in lowercase 
    :return str: the content of the file as a single string
    """
    content = []
    """:type: list[str]"""
    with open(filepath, mode="r", encoding=encoding) as f:
        content = list(f)
        f.close()
    if nl:
        content = [c.replace('\n', ' ') for c in content]
        content = [c.replace('\r', ' ') for c in content]
        content = [c.replace('\t', ' ') for c in content]
    if lower:
        content = [c.lower() for c in content]
    return " ".join(content)


def words_from_text(text, re='[^a-zàáèéìíòóùú]', word2id=None):
    """
    Convert a text ina list of words
    
    :param str text: 
    :param str re: re to use to split the line in words
    :param corpora.Dictionary word2id: dictionary to use to convert words in ids
    :return list: list of words or list of tuples (id, count) 
    """
    words = rexp.split(re, text.lower())
    if word2id:
        words = word2id.doc2bow(words)
    return words


def words_from_file(filepath,
                    encoding='utf-8',
                    re='[^a-zàáèéìíòóùú]',
                    corpus=False,
                    word2id=None):
    """
    
    :param str filepath: file to read
    :param str encoding: encoding to use in the file reading. Default 'utf-8'
    :param str re: re to use to split the line in words
    :param bool corpus: if return each line as a document
    :param corpora.Dictionary word2id: dictionary to use to convert words in ids
    :return list: list of words or list of tuples (id, count) 
    """
    print("... load %s" % filepath)
    with open(filepath, mode="r", encoding=encoding) as f:
        content = list(f)
        f.close()
    content = [rexp.split(re, c.lower()) for c in content]
    content = [[w for w in c if len(w)>0] for c in content]
    content = [c for c in content if len(c) > 0]
    if word2id:
        content = [word2id.doc2bow(c) for c in content]
    if corpus:
        return content
    collected = []
    r = [collected.extend(c) for c in content]
    return collected


def words_from_directory(directory,
                         pattern="*.txt",
                         encoding='utf-8',
                         re='[^a-zàáèéìíòóùú]',
                         word2id=None):
    """
    Read the content of a directory (or multiple directories) and create
    the related corpora: a list of lists of words, where a list of words is a 
    document
    
    :param str|list[str] directory: directory/ies to scan 
    :param str pattern: pattern to use to selecte the files in the directory 
    :param str encoding: encoding of the files. Default 'utf-8' 
    :param str re: re used to split a text line 
    :param corpora.Dictionary word2id: dictionary to use to convert words in in ids
    :return list[list]: list of list of words/id 
    """
    if type(directory) in [str]:
        dirs = [directory]
    else:
        dirs = directory

    allwords = []
    for adir in dirs:
        print("scan %s ..." % adir)
        d = p.Path(adir)
        words = [
            words_from_file(fp, encoding=encoding, re=re, word2id=word2id)
            for fp in d.files(pattern=pattern)
        ]
        allwords.extend(words)
    return allwords


def wordset_from_file(filepath, encoding='utf-8'):
    """
    Read a file of words and create a set.
    
    :param str filepath: path of the file to read
    :param str encoding: encoding to use. Default 'utf-8' 
    :return: 
    """
    with open(filepath, mode="r", encoding=encoding) as f:
        content = list(f)
        f.close()
    content = [c.split() for c in content]
    content = ft.reduce(lambda a, b: (a.extends(b) if a else b), content, [])
    return set(content)


def count_corpus_words(corpus, words=False):
    if not words:
        return sum(len(c) for c in corpus)
    else:
        return sum((sum(t[1] for t in c)) for c in corpus)