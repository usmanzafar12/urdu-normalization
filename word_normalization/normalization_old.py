"""To take text as input. Return text with corrected spelling."""
# coding: utf-8


def eng_word_candidates(word, language_model):
    """Take input word, return list of most likely words using Language Model."""
    res_list = [x[0] for x in language_model[word].most_common()]
    return res_list


def load_lm(filename):
    """Load pickle file of trained language model. Returns trained LM."""
    import pickle

    f = open(filename, 'r')
    bigram_freq = pickle.load(f)
    f.close()
    return bigram_freq


def eng_word_correction(text):
    """Detect and correct error words with enchant library and trained LM."""
    import enchant
    d = enchant.Dict("en_US")   # create dictionary for US English
    language_model = load_lm('bigrams.pkl')
    text = text.split()
    for n, m in enumerate(text):
        if not d.check(m):
            wordlist = eng_word_candidates(text[n - 1], language_model)
            suggested_words = d.suggest(m)
            match = set(suggested_words) & set(wordlist)

            try:
                text[n] = list(match)[0]
            except IndexError:
                text[n] = suggested_words[0]
    return text


text = "I hve lost my crdt crd"
print(text)
text = eng_word_correction(text)
print(text)
