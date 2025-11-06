import os
from typing import Any
import requests
from openai import OpenAI
import json
from dotenv import load_dotenv
from time import time

CORRECTNESS_TEMPLATE = """
    Question: {question}
    Ground truth: {answer_true}

    Your task is to evaluate the correctness of the given answer as either 'correct' or 'incorrect'.
    The correct answer should be numerically or logically close to the provided ground truth.
    Please respond with your rating only, without any further explanation.

    ---{answer_pred}---
"""


def validate_answer(
    client: OpenAI, model: str | None, question: str, answer_true: str, answer_pred: str
) -> tuple[Any, int | float]:
    """
    score = validate_answer(
            client,
            os.getenv('MODEL'),
            '2+2 = ?',
            '4', '4'
        )
    """

    messages = [
        {
            "role": "user",
            "content": CORRECTNESS_TEMPLATE.format(
                question=question, answer_true=answer_true, answer_pred=answer_pred
            ),
        },
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=32,
        # temperature=0.7,
    )

    response_str_original = response.choices[0].message.content
    response_str = response_str_original.strip().lower()

    if "incorrect" in response_str:
        correctness: int | float = 0
    elif "correct" in response_str:
        correctness = 1
    else:
        correctness = 0.3

    return response_str_original, correctness


if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(
        api_key=os.getenv("KEY"),
        # base_url=os.getenv("URL"),
    )

    with open("train.json", "r") as fd:
        train = json.load(fd)

    lst_scores = []

    start_time = time()
    for item in train[:5]:
        response = requests.get(
            f"http://localhost:8008/get_answer?question={item['question']}"
        )
        score = validate_answer(
            client,
            os.getenv("MODEL"),
            item["question"],
            item["answer"],
            response.json().get("answer"),
        )
        lst_scores.append(score)
    time_validate = time() - start_time

    print(f"Get scores: {lst_scores} in {time_validate:.4f}")
    acc = sum([score[1] for score in lst_scores]) / len(lst_scores)
    print(f"LLM-accuracy: {acc:.4f} ")
