#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import traceback
import unicodedata
from pathlib import Path

import MeCab
from sumeval.metrics.rouge import RougeCalculator
from tqdm import tqdm

from eval_util import extract_words, extract_all_words, word2ids


GS_FILENAME = "PoliInfo3_QuestionAnswering_v20211120-Gold.json"


class EvaluationException(Exception):
    pass


def main():
    try:
        dicdir = subprocess.run(["mecab-config", "--dicdir"], check=True,
                                stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip()
        sysconfdir = subprocess.run(["mecab-config", "--sysconfdir"], check=True,
                                    stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip()
        unidic_path = f"{dicdir}/unidic" \
            if os.path.exists(f"{dicdir}/unidic") else None
    except IOError:
        sysconfdir = "/etc"
        unidic_path = None

    gs_data = (Path(__file__).parents[0] / GS_FILENAME)

    parser = argparse.ArgumentParser(
        description="""NTCIR-16 QA Lab PoliInfo-3 Question Answering タスクの ROUGE 自動評価スクリプトです．""")

    parser.add_argument('-f', '--input-file', required=True,
                        help='入力データを指定します')
    parser.add_argument('-g', '--gs-data', required=(not gs_data.exists()), default=gs_data,
                        help='GSデータを指定します')
    parser.add_argument('-d', '--unidic-path', required=(unidic_path is None), default=unidic_path,
                        help='MeCabで用いるUnidicのパスを指定します')

    args = parser.parse_args()

    mecab = MeCab.Tagger(f'-r {sysconfdir}/mecabrc -d {args.unidic_path}')
    rouge_calculator = RougeCalculator(stopwords=False, lang="en")

    # GS読み込み
    with open(args.gs_data, "r", encoding="utf-8-sig") as f:
        gss_raw = json.load(f)
        gss = {line["ID"]: line for line in gss_raw}
        assert gss_raw and len(gss_raw) == len(gss) and all("AnswerSummary" in line for line in gss_raw)
        del gss_raw

    # 評価対象読み込み
    with open(args.input_file, "r", encoding="utf-8-sig") as f:
        try:
            targets_raw = json.load(f)
        except Exception:
            raise EvaluationException("JSON ファイルのデコードに失敗しました。データを確認してください。")
    targets = {}
    for i, line in enumerate(targets_raw):
        if "ID" not in line:
            raise EvaluationException(f"JSON ファイルに ID のない項目があります（項目 {i + 1}）。データを確認してください。")
        if line["ID"] in targets:
            raise EvaluationException(f"JSON ファイルに ID の重複があります（ID: {line['ID']}）。データを確認してください。")
        targets[line["ID"]] = line
    del targets_raw

    # データの確認
    for k in gss.keys():
        if k not in targets:
            raise EvaluationException(f"入力データで回答されていない項目があります（ID: {k}）。データを確認してください。")
    for k, line in targets.items():
        if k not in gss:
            raise EvaluationException(f"入力データに不明な ID があります（ID: {k}）。データを確認してください。")
        if "AnswerSummary" not in line:
            raise EvaluationException(f"JSON ファイルに AnswerSummary のない項目があります（ID: {k}）。データを確認してください。")

    # 評価結果リスト
    evals = {}

    # 評価データ各々に対して
    for key, gs in tqdm(gss.items()):
        target = targets[key]

        eval_line = {}
        for extract_type, extract_func in (
            ('短単位（表層形）', lambda s: extract_all_words(mecab, s, True)),
            ('短単位（原形）', lambda s: extract_all_words(mecab, s, False)),
            ('内容語', lambda s: extract_words(mecab, s)),
        ):
            reference_text = extract_func(unicodedata.normalize("NFKC", gs["AnswerSummary"]))
            summary_text = extract_func(unicodedata.normalize("NFKC", target["AnswerSummary"]))
            ((summary,),), ((references,),) = word2ids(summary_text, reference_text)

            scores = {
                'ROUGE-1-R': rouge_calculator.rouge_1(summary, references, 0.0),
                'ROUGE-2-R': rouge_calculator.rouge_2(summary, references, 0.0),
                'ROUGE-3-R': rouge_calculator.rouge_n(summary, references, 3, 0.0),
                'ROUGE-4-R': rouge_calculator.rouge_n(summary, references, 4, 0.0),
                'ROUGE-L-R': rouge_calculator.rouge_l(summary, references, 0.0),
                'ROUGE-1-F': rouge_calculator.rouge_1(summary, references, 0.5),
                'ROUGE-2-F': rouge_calculator.rouge_2(summary, references, 0.5),
                'ROUGE-3-F': rouge_calculator.rouge_n(summary, references, 3, 0.5),
                'ROUGE-4-F': rouge_calculator.rouge_n(summary, references, 4, 0.5),
                'ROUGE-L-F': rouge_calculator.rouge_l(summary, references, 0.5),
            }

            if not eval_line:
                for rouge_type in scores.keys():
                    eval_line[rouge_type] = {}

            for rouge_type, score in scores.items():
                eval_line[rouge_type][extract_type] = score

        evals[key] = eval_line

    # 全体スコアの計算
    macro_count = 0
    macro_sum = {}
    for eval_line in evals.values():
        if not macro_sum:
            for rouge_type, scores in eval_line.items():
                macro_sum[rouge_type] = {}
                for extract_type, score in scores.items():
                    macro_sum[rouge_type][extract_type] = 0.0

        macro_count += 1
        for rouge_type, scores in eval_line.items():
            for extract_type, score in scores.items():
                macro_sum[rouge_type][extract_type] += eval_line[rouge_type][extract_type]

    macro_ave = {
        rouge_type: {extract_type: score / macro_count for extract_type, score in scores.items()}
        for rouge_type, scores in macro_sum.items()
    }

    # 出力
    return json.dumps({
        'status': 'success',
        'score': macro_ave['ROUGE-1-F']['内容語'],
        'macro_ave': macro_ave,
        'ins': evals
    }, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    try:
        print(main())
    except EvaluationException as e:
        print(json.dumps({'status': 'failed', 'message': e.args[0]}, ensure_ascii=False))
        traceback.print_exc()
    except Exception:
        print(json.dumps({'status': 'failed'}, ensure_ascii=False))
        traceback.print_exc()
