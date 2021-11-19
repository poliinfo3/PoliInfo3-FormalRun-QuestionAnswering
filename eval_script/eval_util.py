#!/usr/bin/env python3

import sys
import re
import math
from collections import defaultdict
from typing import Tuple, Optional, TypeVar, List


T = TypeVar('T')

functional_verbs = {"為る", "居る", "成る", "有る"}
content_words = ["助詞", "助動詞", "感動詞", "空白", "補助記号", "記号-一般"]
adverbial_nouns = {"所", "為", "くらい"}
formal_nouns = {"の", "事", "物", "積り", "訳"}
numeral_notation1_regex = re.compile(
    r'([^兆億万]+兆)?([^兆億万]+億)?([^兆億万]+万)?([^兆億万]*)')
numeral_notation2_regex = re.compile(
    r'([^千百十]*千)?([^千百十]*百)?([^千百十]*十)?([^千百十]*)')


def nonEmpty(s: str) -> bool:
    return s is not None and s != ''


def isEmpty(s: str) -> bool:
    return not nonEmpty(s)


def or_else(n: Optional[T], e: T) -> T:
    return n if n is not None else e


def is_content_word(pos: str) -> bool:
    for el in content_words:
        if pos.startswith(el):
            return False
    return True


def is_noun(pos: str, original: str) -> bool:
    return (pos.startswith('名詞') or pos == "記号-文字" or pos.startswith(
        "接尾辞-名詞的") or pos == "接頭辞") and (original not in adverbial_nouns) and (original not in formal_nouns)


def is_numeral(pos: str) -> bool:
    return pos == '名詞-数詞'


def word2ids(summary: List[str], reference: List[str]) -> Tuple[List[List[str]], List[List[List[str]]]]:
    id_dict = defaultdict(lambda: len(id_dict))
    rsummary = [[' '.join([str(id_dict[w]) for w in summary])]]
    rreference = [[[' '.join([str(id_dict[w]) for w in reference])]]]
    return rsummary, rreference


def replace_all_kanji_to_arabic(numerals: str) -> str:
    tmp = numerals.replace("一", "1").replace("二", "2").replace("三", "3").replace("四", "4").replace("五", "5").replace(
        "六", "6").replace("七", "7").replace("八", "8").replace("九", "9").replace("〇", "0")
    tmp = re.sub(r'[^0123456789]', '', tmp)
    tmp = re.sub(r'^0+', '', tmp)
    return tmp


def parse_kanji_numerals(kanji_numerals: str) -> Optional[int]:
    def p3(numerals: str, has_default: bool) -> Optional[int]:
        if nonEmpty(numerals):
            if has_default:
                return 1
            else:
                return None
        try:
            return int(replace_all_kanji_to_arabic(numerals))
        except Exception as err:
            print(err, file=sys.stderr)
            return None

    def p4(numerals: str) -> Optional[int]:
        numeral_array = list(reversed(replace_all_kanji_to_arabic(numerals)))
        num = 0
        for i, x in enumerate(numeral_array):
            try:
                num += int(int(x) * math.pow(10, i))
            except Exception:
                pass
        return num

    def p2(numerals: str) -> Optional[int]:
        if isEmpty(numerals):
            return None
        mobj = numeral_notation2_regex.match(numerals)
        if mobj is not None:
            if nonEmpty(mobj.group(1)) and nonEmpty(mobj.group(2)) and nonEmpty(mobj.group(3)):
                base2 = 10
                print(numerals, file=sys.stderr)
                output2 = or_else(p3(mobj.group(1)[:-1], True), 0) * base2 * base2 * base2 + or_else(
                    p3(mobj.group(2)[:-1], True), 0) * base2 * base2 + or_else(p3(mobj.group(3)[:-1], True),
                                                                               0) * base2 + or_else(
                    p3(mobj.group(4), False), 0)
                return output2
            else:
                return p4(numerals)
        else:
            return None

    tmp = kanji_numerals.replace('ゼロ-zero', '〇').replace('零', '〇')
    matchObj = numeral_notation1_regex.match(tmp)
    if matchObj is not None:
        base = 10000
        default_string = 'a'
        output = or_else(p2(or_else(matchObj.group(1), default_string)[:-1]), 0) * base * base * base + or_else(
            p2(or_else(matchObj.group(2), default_string)[:-1]), 0) * base * base + or_else(
            p2(or_else(matchObj.group(3), default_string)[:-1]), 0) * base + or_else(p2(matchObj.group(4)), 0)
        return output
    else:
        return None


# '内容語'
def extract_words(mecab, s: str) -> List[str]:
    parsed = mecab.parse(s)
    ret = []
    compound_nouns = []
    numerals = []

    def append(term):
        if term not in functional_verbs:
            ret.append(term)

    def extract_compound_noun():
        if len(compound_nouns) > 0:
            append(''.join(compound_nouns))
            compound_nouns.clear()

    def extractNumeral():
        if len(numerals) > 0:
            x = parse_kanji_numerals(''.join(numerals))
            if x is not None:
                compound_nouns.append(str(x))
            numerals.clear()

    def compound_noun(tokens: List[str]):
        if len(tokens) < 5:
            return

        pos = tokens[4]

        def buffer_noun():
            compound_nouns.append(tokens[3].strip())

        def buffer_numeral():
            numerals.append(tokens[3].strip())

        def extract_content_word():
            if is_content_word(pos):
                append(tokens[3].strip())

        if is_noun(pos, tokens[0]):
            if is_numeral(pos):
                buffer_numeral()
            else:
                extractNumeral()
                buffer_noun()
        else:
            extractNumeral()
            extract_compound_noun()
            extract_content_word()

    for line in filter(lambda x: x != 'EOS', parsed.splitlines()):
        tmp = line.split('\t')
        if len(tmp) > 1:
            compound_noun(tmp)
        else:
            append(tmp[0])

    extractNumeral()
    extract_compound_noun()

    return ret


# '短単位（原形）' (not is_original), '短単位（表層形）' (is_original)
def extract_all_words(mecab, s: str, is_original: bool) -> List[str]:
    parsed = mecab.parse(s)
    idx = 0 if is_original else 3
    ret = []

    def append(term):
        ret.append(term)

    for line in filter(lambda x: x != 'EOS', parsed.splitlines()):
        tmp = line.split('\t')
        if len(tmp) > 2:
            append(tmp[idx])
        else:
            append(tmp[0])
    return ret
