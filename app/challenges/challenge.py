from __future__ import annotations
from dataclasses import dataclass
from typing import List, Protocol, Dict, Any

class Challenge(Protocol):
    id: str
    title: str
    difficulty: int
    def evaluate(self, answer: Any) -> Dict[str, Any]: ...

@dataclass
class QuizChallenge:
    id: str
    title: str
    difficulty: int
    questions: List[Dict[str, Any]]  # each: {q, options, correct_index, weight?}

    def __init__(self, id: str, title: str, difficulty: int, questions: List[Dict[str, Any]]):
        self.id = id
        self.title = title
        self.difficulty = difficulty
        self.questions = questions

    def evaluate(self, answers: List[int]) -> Dict[str, Any]:
        correct = 0
        total = len(self.questions) if self.questions else 0

        # Weighted accuracy support
        has_weights = any('weight' in q for q in self.questions)
        if not has_weights:
            for i, q in enumerate(self.questions):
                if i < len(answers) and answers[i] == q.get("correct_index"):
                    correct += 1
            accuracy = (correct / total) if total else 0.0
            return {"correct": correct, "total": total, "accuracy": accuracy}
        else:
            sum_w = 0.0
            sum_correct_w = 0.0
            for i, q in enumerate(self.questions):
                w = float(q.get("weight", 1.0))
                sum_w += w
                if i < len(answers) and answers[i] == q.get("correct_index"):
                    sum_correct_w += w
            accuracy = (sum_correct_w / sum_w) if sum_w > 0 else 0.0
            return {"correct": int(sum_correct_w), "total": int(sum_w), "accuracy": accuracy}

