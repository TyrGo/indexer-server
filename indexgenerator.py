from os import replace
import re
import pdfplumber


def make_index(ms, words):
    '''Writes an index for a book from a list of entries'''

    entries = get_entries(words)
    entries_list = list_entries(entries)
    found_words = find_words(ms, entries_list)
    print(f"found_words: {found_words}")
    ranged_words = rangify_list(found_words)
    index = write_index(entries, ranged_words)
    write_file(index)


def get_entries(words):
    '''Gets a list of entry lines from a txt file'''

    byte_entries = words.read().splitlines()
    lines = [entry.decode('utf-8') for entry in byte_entries]
    # better: get more e.g. ' ' with regex
    not_empties = [line for line in lines if line != '']
    entries = sorted(not_empties, key=str.casefold)
    print(f"lines to index: {entries}")
    return entries


def list_entries(entries):
    '''Produces a list of entries from a list of entry lines'''

    entries_list = []

    for line in entries:
        words = re.split(', |, |: |\+', line)
        for word in words:
            if word not in entries_list:
                entries_list.append(word)

    entries_list = [remove_ligatures(word) for word in entries_list]
    return entries_list


def remove_ligatures(word): 
    '''Removes ligatures, etc, from a string'''
    
    return (word
            .replace('9', 'ti')
            .replace(';', 'tio')
            .replace('^', 'tt')
            .replace('ﬀ', 'ff')
            .replace('ﬁ', 'fi')
            .replace('ﬃ', 'ffi')
            .replace('-', ' ')
            )  # many more ligatures; maybe best to do via dictionary of them


def find_words(ms, entries_list):
    '''Produces a dictionary of entries and corresponding manuscript pages'''

    found_words = {}

    with pdfplumber.open(ms) as pdf:
        all_pages = len(pdf.pages)

        for num in range(all_pages):
            print(f'processing page {num}')
            pg_num = pdf.pages[num]
            content = pg_num.extract_text(x_tolerance=1)
            pg_words = lower_case(content)

            for word in entries_list:
                entry_words = lower_case(word)
                if is_present(entry_words, pg_words):
                    print(f'~~~~~found: {word}')

                    if word not in found_words:
                        found_words[word] = []
                    found_words[word].append(pg_num.page_number)

    return found_words


def lower_case(content):
    '''Lowers the case of strings in a list'''

    words = re.findall(r'[\w]+', content)
    words_lowered = [word.lower().lstrip() for word in words]
    return words_lowered


def is_present(entry_words, pg_words):
    '''
    Discovers whether a list of words appear exactly and in order in another list

    >>> is_present(['a', 'b', 'c'], ['extra', 'a','b','c', 'extra'])
    True
    >>> is_present(['a','b', 'c'], ['a', 'extra', 'b', 'c'])
    False
    '''

    first, rest = entry_words[0], entry_words[1:]
    pos = 0
    try:
        while True:
            pos = pg_words.index(first, pos) + 1
            if not rest or pg_words[pos:pos+len(rest)] == rest:
                return True
    except ValueError:
        return False


def rangify_list(found_words):
    '''Rangifies values in a dictionary'''

    for word in found_words:
        found_words[word] = rangify(found_words[word])

    return found_words


def rangify(arr):
    '''
    Produces (page) ranges from list of numerals
    
    >>> rangify([1,2,3,18,26,27,28,94])
    '1-3, 18, 26-8, 94'
    '''

    if arr == []:
        return ''

    final_list = []
    ranger = []
    i = 0

    while i < len(arr):
        if ranger != [] and arr[i] != arr[i - 1] + 1:
            if len(ranger) > 1:
                range = f'{ranger[0]}-{ranger[-1]}'
                final_list.append(shorten_range(range))
            else:
                final_list.append(ranger[0])
            ranger = []
        ranger.append(str(arr[i]))
        i += 1

    if len(ranger) == 1:
        final_list.append(str(arr[-1]))
    else:
        range = f'{ranger[0]}-{ranger[-1]}'
        final_list.append(shorten_range(range))

    return ', '.join(final_list)


def shorten_range(range):
    '''
    Makes a range of pages neater
   
    >>> shorten_range('126-128')
    '126-8'
    '''

    [lefty, righty] = range.split('-')

    if len(lefty) < len(righty):
        return range

    i = 0

    while i < len(righty) and lefty[i] == righty[i]:
        i += 1

    return f"{lefty}-{righty[i:]}"


def write_index(entries, found_words):
    '''Produces an an index of entries and their page numbers'''

    index = 'Index'
    letter = ''

    for line in entries:
        new_line = ''
        words = re.split(', |, |: |\+', line)
        subs = words[1:]
        subs = sorted(subs, key=str.casefold)
        words = [words[0]] + subs

        for word in words:
            check_word = remove_ligatures(word)
            if check_word in found_words:
                word = f'{word} {found_words[check_word]}'
            new_line += f'{word}; '
            print(f"creating index for {word}")

        new_line = new_line[:-2]
        if new_line[0].lower() != letter:
            index = f"{index}\n"
            letter = new_line[0].lower()
        index = f"{index}\n" + new_line

    return index


def write_file(index):
    '''Writes an index to a file'''

    index_file = open("index.txt", "a")
    index_file.write(index)
    index_file.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
