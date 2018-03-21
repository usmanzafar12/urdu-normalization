#########################################
### Dataset Creation Code starts here ###
#########################################


def add_sent_marker(corp):
    """To add sentence markers to nltk sentences corpora."""
    out = []
    for sent in corp:
        sent = ['<s>'] + sent + ['</s>']
        for word in sent:
            out.append(word)
    return out


def get_corpus():
    """To get nltk sentence corpora."""
    from nltk.corpus import brown
    from nltk.corpus import reuters

    corpus = add_sent_marker(brown.sents())
    corpus = corpus + add_sent_marker(reuters.sents())
#     print corpus[-50:]
#     corpus = add_sent_marker(corpus)
    return corpus


def add_domain_data(filename, corpus):
    """To add other data(from flatfile) to nltk corpora."""
    """This data has sentence markers already."""
    # with open("lm_corpus.txt", "r") as thefile:
    with open(filename, "r") as thefile:
        x = thefile.read().splitlines()
        corpus = corpus + x
    return corpus


def remove_punctuation(corpus):
    """To remove punctuation from corpus."""
    import re

    result = []

    for n in corpus:
        n = n.lower()
        n = n.encode('utf-8')
        x = re.sub('\.', '', n)
        x = re.sub('\?', '', x)
        x = re.sub('\#', '', x)
        x = re.sub('\!', '', x)
        x = re.sub("''", '', x)
        x = re.sub('""', '', x)
        if x != '':
            result.append(x)

    return result


def build_lm(corpus):
    """Build and save language model(pickle & redis DB). Return language model."""
    import nltk
    import redis
    language_model = nltk.ConditionalFreqDist(nltk.bigrams(corpus))

#     f = open('language_model.pkl', 'w')
#     pickle.dump(language_model, f)
#     f.close()

    r = redis.Redis(host='localhost', port=6379, db=0)
    temp = language_model.keys()
    for value in temp:
        values = dict(language_model[value].most_common())
        for dummy in values.iteritems():
            temp2 = {dummy[0]: int(dummy[1])}
            r.hmset(value, temp2)

    return language_model


def build_dmeta(corpus):
    """To build and dump double metaphone dictionary to Redis DB."""
    from metaphone import doublemetaphone
    import redis
    dmeta = {}
    for word in corpus:
        # print n
        # print word
        word = word.lower()
        if word:
            code = doublemetaphone(word)
            if code[0] not in dmeta:
                dmeta[code[0]] = [word]
            else:
                if word not in dmeta[code[0]]:
                    dmeta[code[0]].append(word)
#     print dmeta
#     values = dict(dmeta[value].most_common())
    # print values

    r = redis.Redis(host='localhost', port=6379, db=0)
    for dummy in dmeta.iteritems():
        # print dummy
        # print "testing", ",".join(dummy[1])
        temp2 = {dummy[0]: ",".join(dummy[1])}
#         temp2 = {dummy[0]: dummy[1]}
        r.hmset('dmeta', temp2)
    return


def dmeta_wordlist(word):
    """Load double metaphones dictionary from Redis."""
    from metaphone import doublemetaphone
    code = doublemetaphone(word)
    r = redis.Redis(host='localhost', port=6379, db=0)
    dmeta = r.hmget('dmeta', code)

    try:
        wordlist = dmeta[0].split(",")
    except AttributeError:
        wordlist = []

    return wordlist


def create_data(filename, corpus):
    """To create and save data by User Input. Enter 'quit' to stop."""
    """Takes target filename and corpus as input."""
    x = ""
    while x != "quit":
        x = raw_input("Enter Sentence:\n")
        if x != "quit":
            x = '<s> ' + x
            x = x + ' </s>'
            y = x.split()
            corpus = corpus + y

#    with open("lm_corpus.txt", "w") as thefile:
    with open(filename, "w") as thefile:
        for n in corpus[-93:]:
            thefile.write("%s\n" % n)
    thefile.close()

    return corpus


import redis
r = redis.Redis(host='localhost', port=6379, db=0)
corpus = get_corpus()
corpus = add_domain_data('lm_corpus.txt', corpus)
corpus = remove_punctuation(corpus)
build_lm(corpus)
build_dmeta(corpus)

# Test case for Double Metaphones
code = 'LST'        # enter Double Metaphone code here
dmeta = r.hmget('dmeta', code)

try:
    wordlist = dmeta[0].split(",")
except AttributeError:
    wordlist = []
print wordlist

# Test case for Language Model word suggestions
word = 'have' # Enter English word here to find probable candidates
scores = r.hgetall(word)
sorted_names = sorted(scores.items(), key=lambda x: int(x[1]), reverse=True)
res_list = []

for word in sorted_names:
    res_list.append(word[0])
print res_list