#!/usr/bin/env python3

import argparse
import collections
import dataclasses
import json
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SummaryLine():
    ID: str = field()
    Meeting: str = field(repr=False)
    Date: str = field()
    Headlines: List[str] = field()
    SubTopic: str = field()
    QuestionSpeaker: str = field()
    QuestionSummary: str = field()
    AnswerSpeaker: List[str] = field()
    # AnswerLength: List[int] = field()
    AnswerSummary: List[str] = field()


@dataclass(frozen=True)
class UtteranceLine():
    Volume: str = field(repr=False)
    Number: str = field(repr=False)
    Date: str = field()
    Title: str = field(repr=False)
    SpeakerPosition: str = field(repr=False)
    SpeakerName: str = field(repr=False)
    QuestionSpeaker: str = field()
    Speaker: str = field()
    Utterance: str = field()


def main():
    parser = argparse.ArgumentParser(
        description="""QA Lab-PoliInfo-3 Question Answering タスクのスクリプトサンプル。発言の末尾40文字を取り出す。"""
    )
    parser.add_argument("-p", "--proceedings", default="PoliInfo3_Utterances_v20211120.json", help="会議録を指定します")
    parser.add_argument("-s", "--summary", default="PoliInfo3_QuestionAnswering_v20211120-Test.json", help="出題ファイルを指定します")
    args = parser.parse_args()

    # 出題ファイルの読み込み
    with open(args.summary, "r", encoding="utf-8") as fp:
        summary_data = [SummaryLine(**line) for line in json.load(fp)]

    # 会議録の読み込み
    with open(args.proceedings, "r", encoding="utf-8") as fp:
        proceeding_data = [UtteranceLine(**line) for line in json.load(fp)]

    proceeding_dict = collections.defaultdict(list)
    for proceeding_line in proceeding_data:
        proceeding_dict[proceeding_line.Date, proceeding_line.QuestionSpeaker, proceeding_line.Speaker].append(proceeding_line)

    out_summary = []
    for summary_line in summary_data:
        proceeding_lines = proceeding_dict[summary_line.Date, summary_line.QuestionSpeaker, summary_line.AnswerSpeaker]
        last_40chars = "".join(proceeding_line.Utterance for proceeding_line in proceeding_lines)[-40:]
        out_summary.append(dataclasses.replace(summary_line, AnswerSummary=last_40chars))

    # 標準出力に結果を出力
    lines = [json.dumps(dataclasses.asdict(ex), ensure_ascii=False) for ex in out_summary]
    print("[\n" + ",\n".join(lines) + "\n]")


if __name__ == "__main__":
    main()
