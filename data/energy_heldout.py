# HELD-OUT set: run each backend ONCE. Never tune prompts, rules or thresholds on it.
# Each test is (arguments_tuple, expected_result). Outputs avoid tuples (JSON round trip).

TASKS = [
    {
        "id": "h01_roman_to_int",
        "entry": "roman_to_int",
        "prompt": '''Write a Python function roman_to_int(s) that converts a Roman numeral string (uppercase letters I, V, X, L, C, D, M, valid numerals only) to an integer. Use the standard subtractive rules such as IV = 4 and IX = 9. Return only the code.''',
        "tests": [
            (("III",), 3),
            (("IV",), 4),
            (("IX",), 9),
            (("LVIII",), 58),
            (("MCMXCIV",), 1994),
            (("XL",), 40),
            (("MMXXVI",), 2026),
        ],
    },
    {
        "id": "h02_flatten",
        "entry": "flatten",
        "prompt": '''Write a Python function flatten(nested) that takes a list that may contain other lists nested to any depth and returns a single flat list with all the non-list items in their original left-to-right order. Strings are items, not lists. Return only the code.''',
        "tests": [
            (([1, [2, [3, [4]]]],), [1, 2, 3, 4]),
            (([],), []),
            (([[], [[]]],), []),
            (([1, 2, 3],), [1, 2, 3]),
            (([[1, 2], [3, [4, 5]], 6],), [1, 2, 3, 4, 5, 6]),
            ((["a", ["b"]],), ["a", "b"]),
        ],
    },
    {
        "id": "h03_rotate_matrix",
        "entry": "rotate_matrix",
        "prompt": '''Write a Python function rotate_matrix(m) that takes a square matrix (a list of equal-length lists) and returns a NEW matrix rotated 90 degrees clockwise, without modifying the input. An empty matrix returns an empty list. Return only the code.''',
        "tests": [
            (([[1, 2], [3, 4]],), [[3, 1], [4, 2]]),
            (([[1]],), [[1]]),
            (([],), []),
            (([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [[7, 4, 1], [8, 5, 2], [9, 6, 3]]),
        ],
    },
    {
        "id": "h04_group_anagrams",
        "entry": "group_anagrams",
        "prompt": '''Write a Python function group_anagrams(words) that groups words that are anagrams of each other. Return a list of groups, where each group is a list of words sorted alphabetically, and the list of groups is sorted by the first word of each group. An empty input returns an empty list. Return only the code.''',
        "tests": [
            ((["eat", "tea", "tan", "ate", "nat", "bat"],), [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]),
            (([],), []),
            ((["a"],), [["a"]]),
            ((["ab", "ba", "abc"],), [["ab", "ba"], ["abc"]]),
        ],
    },
    {
        "id": "h05_longest_common_prefix",
        "entry": "longest_common_prefix",
        "prompt": '''Write a Python function longest_common_prefix(strs) that takes a list of strings and returns the longest prefix shared by all of them, or an empty string if there is none. An empty list returns an empty string. Return only the code.''',
        "tests": [
            ((["flower", "flow", "flight"],), "fl"),
            ((["dog", "racecar", "car"],), ""),
            (([],), ""),
            ((["a"],), "a"),
            ((["abc", "abc"],), "abc"),
            ((["", "abc"],), ""),
        ],
    },
    {
        "id": "h06_is_valid_ipv4",
        "entry": "is_valid_ipv4",
        "prompt": '''Write a Python function is_valid_ipv4(s) that returns True if s is a valid IPv4 address and False otherwise. A valid address has exactly four parts separated by dots. Each part contains only digits, is between 0 and 255, and has no leading zeros (except the single digit "0" itself). Spaces and signs are not allowed. Return only the code.''',
        "tests": [
            (("192.168.1.1",), True),
            (("256.1.1.1",), False),
            (("1.2.3",), False),
            (("01.2.3.4",), False),
            (("1.2.3.4.5",), False),
            (("0.0.0.0",), True),
            (("1.2.3.a",), False),
            (("",), False),
            (("255.255.255.255",), True),
            (("1..2.3",), False),
            ((" 1.2.3.4",), False),
            (("-1.2.3.4",), False),
        ],
    },
    {
        "id": "h07_median_bug",
        "entry": "median",
        "prompt": '''This Python function returns the wrong answer for some inputs.

```python
def median(nums):
    """Return the median of a non-empty list of numbers."""
    s = sorted(nums)
    mid = len(s) // 2
    return s[mid]
```

Fix the bug and return the complete corrected function. Return only the code.''',
        "tests": [
            (([1, 3, 2],), 2),
            (([1, 2, 3, 4],), 2.5),
            (([5],), 5),
            (([4, 1],), 2.5),
            (([7, 1, 3, 5],), 4.0),
        ],
    },
    {
        "id": "h08_chunk_bug",
        "entry": "chunk",
        "prompt": '''This Python function silently drops items.

```python
def chunk(items, size):
    """Split items into lists of length size. The last list may be shorter."""
    return [items[i:i + size] for i in range(0, len(items) - size, size)]
```

Fix the bug and return the complete corrected function. Return only the code.''',
        "tests": [
            (([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]]),
            (([1, 2, 3, 4], 2), [[1, 2], [3, 4]]),
            (([], 3), []),
            (([1, 2], 5), [[1, 2]]),
            (([1, 2, 3], 1), [[1], [2], [3]]),
        ],
    },
    {
        "id": "h09_slugify_extend",
        "entry": "slugify",
        "prompt": '''Here is an existing Python function.

```python
def slugify(title):
    """Turn a title into a URL slug."""
    return title.lower().replace(" ", "-")
```

Change it so that it: (1) lowercases the text, (2) deletes every character that is not a letter, a digit, a space or a hyphen, (3) turns each run of spaces and hyphens into a single hyphen, and (4) has no leading or trailing hyphen. Return the complete updated function. Return only the code.''',
        "tests": [
            (("Hello World",), "hello-world"),
            (("  Hello,   World!  ",), "hello-world"),
            (("Rock & Roll",), "rock-roll"),
            (("a--b",), "a-b"),
            (("",), ""),
            (("C++ Tips 2026",), "c-tips-2026"),
            (("---x---",), "x"),
        ],
    },
    {
        "id": "h10_is_sorted_bug",
        "entry": "is_sorted",
        "prompt": '''This Python function wrongly rejects some sorted lists.

```python
def is_sorted(nums, reverse=False):
    """True if nums is sorted ascending (or descending if reverse=True).
    Equal neighbours are allowed."""
    for a, b in zip(nums, nums[1:]):
        if reverse:
            if a < b:
                return False
        else:
            if a >= b:
                return False
    return True
```

Fix the bug and return the complete corrected function. Return only the code.''',
        "tests": [
            (([1, 2, 2, 3],), True),
            (([1, 3, 2],), False),
            (([],), True),
            (([3, 3],), True),
            (([3, 2, 2, 1], True), True),
            (([1, 2], True), False),
            (([5],), True),
        ],
    },
    {
        "id": "h11_fib_speed",
        "entry": "fib",
        "prompt": '''This Python function is correct but far too slow for large n.

```python
def fib(n):
    """Return the n-th Fibonacci number, with fib(0) = 0 and fib(1) = 1."""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

Rewrite it so that fib(90) returns instantly, and keep the same results. Return the complete function. Return only the code.''',
        "tests": [
            ((0,), 0),
            ((1,), 1),
            ((10,), 55),
            ((50,), 12586269025),
            ((90,), 2880067194370816120),
        ],
    },
    {
        "id": "h12_average_extend",
        "entry": "average",
        "prompt": '''Here is an existing Python function.

```python
def average(nums):
    """Return the mean of a list of numbers."""
    return sum(nums) / len(nums)
```

Change it so that None values in the list are ignored, an empty list (or a list that contains only None values) returns None, and the result is rounded to 2 decimal places. Return the complete updated function. Return only the code.''',
        "tests": [
            (([1, 2, 3],), 2.0),
            (([1, None, 3],), 2.0),
            (([],), None),
            (([None],), None),
            (([1, 2],), 1.5),
            (([1, 2, 2],), 1.67),
            (([0.1, 0.2],), 0.15),
        ],
    },
]