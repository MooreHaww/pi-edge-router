# Dev set 2: realistic edit tasks (fix a bug, extend existing code).
# Each prompt contains existing code. Each test is (arguments_tuple, expected_result).
# Outputs avoid tuples because expected values go through JSON.

TASKS = [
    {
        "id": "t07_cart_total_bug",
        "entry": "cart_total",
        "prompt": (
            "This Python function has a bug: it ignores the quantity of each item.\n\n"
            "```python\n"
            "def cart_total(items, discount_pct=0):\n"
            "    \"\"\"items is a list of (name, unit_price, qty).\n"
            "    Return the total after the percentage discount, rounded to 2 decimals.\"\"\"\n"
            "    total = 0\n"
            "    for name, price, qty in items:\n"
            "        total += price\n"
            "    return round(total * (1 - discount_pct / 100), 2)\n"
            "```\n\n"
            "Fix the bug and return the complete corrected function. Return only the code."
        ),
        "tests": [
            (([("a", 2.5, 2)],), 5.0),
            (([("a", 10, 1), ("b", 5, 3)], 10), 22.5),
            (([],), 0),
            (([("x", 19.99, 3)],), 59.97),
            (([("x", 100, 1)], 100), 0.0),
        ],
    },
    {
        "id": "t08_paginate_bug",
        "entry": "paginate",
        "prompt": (
            "This Python function is supposed to return one page of a list, but the "
            "pages are off by one.\n\n"
            "```python\n"
            "def paginate(items, page, per_page):\n"
            "    \"\"\"Return the items on the given page. Pages start at 1.\n"
            "    Return an empty list if the page is past the end.\"\"\"\n"
            "    start = page * per_page\n"
            "    end = start + per_page\n"
            "    return items[start:end]\n"
            "```\n\n"
            "Fix the bug and return the complete corrected function. Return only the code."
        ),
        "tests": [
            (([1, 2, 3, 4, 5], 1, 2), [1, 2]),
            (([1, 2, 3, 4, 5], 3, 2), [5]),
            (([1, 2, 3, 4, 5], 4, 2), []),
            (([], 1, 10), []),
            (([1, 2, 3], 1, 10), [1, 2, 3]),
            (([1, 2, 3, 4], 2, 2), [3, 4]),
        ],
    },
    {
        "id": "t09_parse_duration_extend",
        "entry": "parse_duration",
        "prompt": (
            "Here is an existing Python function.\n\n"
            "```python\n"
            "def parse_duration(text):\n"
            "    \"\"\"Convert strings like '1h30m' to total minutes (an int).\n"
            "    Supports the units h and m.\"\"\"\n"
            "    total = 0\n"
            "    number = \"\"\n"
            "    for ch in text:\n"
            "        if ch.isdigit():\n"
            "            number += ch\n"
            "        elif ch == \"h\":\n"
            "            total += int(number) * 60\n"
            "            number = \"\"\n"
            "        elif ch == \"m\":\n"
            "            total += int(number)\n"
            "            number = \"\"\n"
            "        else:\n"
            "            raise ValueError(\"bad unit: \" + ch)\n"
            "    return total\n"
            "```\n\n"
            "Change it so that it returns the total number of SECONDS (an int) and also "
            "supports the units d (days) and s (seconds), in addition to h and m. "
            "An empty string returns 0. Return the complete updated function. "
            "Return only the code."
        ),
        "tests": [
            (("1h30m",), 5400),
            (("2d",), 172800),
            (("45s",), 45),
            (("1d2h3m4s",), 93784),
            (("",), 0),
            (("90m",), 5400),
        ],
    },
    {
        "id": "t10_wrap_text_bug",
        "entry": "wrap_text",
        "prompt": (
            "This Python word-wrap function sometimes breaks a line too early.\n\n"
            "```python\n"
            "def wrap_text(text, width):\n"
            "    \"\"\"Greedy word wrap. Return a list of lines, each at most `width`\n"
            "    characters long. A single word longer than width stays on its own line.\"\"\"\n"
            "    lines = []\n"
            "    current = \"\"\n"
            "    for word in text.split():\n"
            "        if len(current) + len(word) + 1 < width:\n"
            "            current = current + \" \" + word if current else word\n"
            "        else:\n"
            "            if current:\n"
            "                lines.append(current)\n"
            "            current = word\n"
            "    if current:\n"
            "        lines.append(current)\n"
            "    return lines\n"
            "```\n\n"
            "Fix the bug and return the complete corrected function. Return only the code."
        ),
        "tests": [
            (("the quick brown fox", 9), ["the quick", "brown fox"]),
            (("hello world", 11), ["hello world"]),
            (("a b c", 3), ["a b", "c"]),
            (("", 5), []),
            (("superlongword short", 5), ["superlongword", "short"]),
            (("aa bb cc", 5), ["aa bb", "cc"]),
        ],
    },
    {
        "id": "t11_top_words_extend",
        "entry": "top_words",
        "prompt": (
            "Here is an existing Python function.\n\n"
            "```python\n"
            "def top_words(text, n):\n"
            "    \"\"\"Return the n most common words in text.\"\"\"\n"
            "    counts = {}\n"
            "    for word in text.lower().split():\n"
            "        word = word.strip(\".,!?;:\")\n"
            "        counts[word] = counts.get(word, 0) + 1\n"
            "    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)\n"
            "    return [w for w, c in ranked[:n]]\n"
            "```\n\n"
            "Change it so that: (1) words with the same count are ordered alphabetically, "
            "(2) empty strings left after stripping punctuation are ignored, and "
            "(3) it takes an optional third parameter stop_words=None, a collection of "
            "lowercase words to exclude from the result. Return the complete updated "
            "function. Return only the code."
        ),
        "tests": [
            (("b a b a c", 2), ["a", "b"]),
            (("the cat the dog", 2), ["the", "cat"]),
            (("the cat the dog", 2, ["the"]), ["cat", "dog"]),
            (("!!! a", 1), ["a"]),
            (("", 3), []),
            (("x y z", 5), ["x", "y", "z"]),
            (("Hello, hello!", 1), ["hello"]),
        ],
    },
    {
        "id": "t12_apply_transactions_bug",
        "entry": "apply_transactions",
        "prompt": (
            "This Python function does not follow its docstring: overdrafts are not "
            "rejected and the rejected count is always 0.\n\n"
            "```python\n"
            "def apply_transactions(balance, transactions):\n"
            "    \"\"\"Apply (kind, amount) pairs in order. kind is 'deposit' or 'withdraw'.\n"
            "    A withdrawal larger than the current balance is rejected (the balance\n"
            "    stays unchanged). Return a list [final_balance, rejected_count].\"\"\"\n"
            "    for kind, amount in transactions:\n"
            "        if kind == \"deposit\":\n"
            "            balance += amount\n"
            "        elif kind == \"withdraw\":\n"
            "            balance -= amount\n"
            "    return [balance, 0]\n"
            "```\n\n"
            "Fix it so it follows the docstring and return the complete corrected "
            "function. Return only the code."
        ),
        "tests": [
            ((100, [("deposit", 50), ("withdraw", 30)]), [120, 0]),
            ((50, [("withdraw", 80)]), [50, 1]),
            ((0, []), [0, 0]),
            ((10, [("withdraw", 10), ("withdraw", 1)]), [0, 1]),
            ((100, [("withdraw", 60), ("withdraw", 60), ("deposit", 20), ("withdraw", 60)]), [0, 1]),
        ],
    },
]