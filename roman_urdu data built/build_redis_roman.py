#########################################
### Dataset Creation Code starts here ###
#########################################


def read_data(filename):
    """To read data from flat file."""
    file = open(filename, "r")
    data = file.read().splitlines()
    file.close()
    return data


def load_entities():
    """To load list of predefined entities."""
    entities = read_data("data/entities.txt")
#     r = redis.Redis(host='localhost', port=6379, db=1)
    r = load_redis(1)
    for n in entities:
        r.lpush('all_entities', n)
    return


def add_sent_marker(corp):
    """To add sentence markers to nltk corpora."""
    out = []
    for sent in corp:
        sent = sent.lower()
        sent = '<s> ' + sent + ' </s>'
        sent = sent.split()
        for word in sent:
            out.append(word)
    return out


def get_roman_corpus():
    """To get nltk corpora."""
    corpus = []
    corpus = add_domain_data('roman_corpus.txt', corpus)
    corpus = add_sent_marker(corpus)
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


def load_redis(db):
    """Load redis database. argument 'db' is integer number."""
    import redis
    r = redis.Redis(host='localhost', port=6379, db=db)
    return r


def build_roman_lm(corpus):
    """Build and save language model(pickle & redis DB). Return language model."""
    import nltk
#     import redis
    language_model = nltk.ConditionalFreqDist(nltk.bigrams(corpus))

#     r = redis.Redis(host='localhost', port=6379, db=1)
    r = load_redis(1)
    temp = language_model.keys()
    for value in temp:
        values = dict(language_model[value].most_common())
        for dummy in values.iteritems():
            temp2 = {dummy[0]: int(dummy[1])}
            r.hmset(value, temp2)

    return language_model


def build_roman_dmeta(corpus):
    """To build and dump double metaphone dictionary to Redis DB."""
    from metaphone import doublemetaphone
#     import redis
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

#     r = redis.Redis(host='localhost', port=6379, db=1)
    r = load_redis(1)
    for dummy in dmeta.iteritems():
        # print dummy
        # print "testing", ",".join(dummy[1])
        temp2 = {dummy[0]: ",".join(dummy[1])}
#         temp2 = {dummy[0]: dummy[1]}
        r.hmset('dmeta', temp2)
    return


def roman_dmeta_wordlist(word):
    """Load double metaphones dictionary from Redis."""
    from metaphone import doublemetaphone
    code = doublemetaphone(word)
    r = load_redis(1)
#     r = redis.Redis(host='localhost', port=6379, db=1)
    dmeta = r.hmget('dmeta', code)

    try:
        wordlist = dmeta[0].split(",")
    except AttributeError:
        wordlist = []

    return wordlist


def get_roman_dict(filename):
    """To Create roman word dictionary with [informal,formal] key value pairs."""
    import pandas as pd
    data = pd.read_csv(filename)
    roman_dict = {}
    word_check = []
    for n, m in enumerate(data['X1']):
        if m in word_check:
            roman_dict[m].append(data['X2'][n])
        else:
            roman_dict[m] = [data['X2'][n]]
    return roman_dict


def get_roman_list(filename):
    """To create list of informal word list."""
    import pandas as pd
    data = pd.read_csv(filename)
    roman_dict = []
    for n, m in enumerate(data['X1']):
        if m not in roman_dict:
            roman_dict.append(m)
    return roman_dict


def build_roman_resource():
    """To dump roman word list and roman word dictionary into Redis db."""
    # import redis
    roman_dict = get_roman_dict('data/SMSStandardizerVersionFinal1.csv')
    roman_list = get_roman_list('data/SMSStandardizerVersionFinal1.csv')

    # r = redis.Redis(host='localhost', port=6379, db=1)
    r = load_redis(1)

    for dummy in roman_dict:
        temp = {dummy: ",".join(roman_dict[dummy])}
        r.hmset('roman_dict', temp)

    for word in roman_list:
        r.lpush('roman_list', word)

    return


def create_data(filename, corpus):
    """To create and save data by User Input."""
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


if __name__ == "__main__":
    from metaphone import doublemetaphone

    corpus = get_roman_corpus()
    corpus = add_domain_data('lm_corpus.txt', corpus)
    corpus = remove_punctuation(corpus)
    build_roman_lm(corpus)
    build_roman_dmeta(corpus)
    build_roman_resource()
    load_entities()

    # Test case for Double Metaphones
    r = load_redis(1)
    word = raw_input("enter word: \n")
    code = doublemetaphone(word)
    dmeta = r.hmget('dmeta', code)

    try:
        wordlist = dmeta[0].split(",")
    except AttributeError:
        wordlist = []
    print "\nDouble Metaphone word list: "
    print wordlist

    # Test case for Language Model word suggestions
    scores = r.hgetall(word)
    sorted_names = sorted(scores.items(), key=lambda x: int(x[1]), reverse=True)
    res_list = []

    for word in sorted_names:
        res_list.append(word[0])
    print "\nLanguage Model Result is:"
    print res_list
