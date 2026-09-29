import math


def fake_embedding(text: str) -> list[float]:
    vector = [0.0] * 8

    for char in text:
        vector[ord(char) % 8] += 1

    length = math.sqrt(sum(x * x for x in vector))
    if length == 0:
        return vector

    return [x / length for x in vector]