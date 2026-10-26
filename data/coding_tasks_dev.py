# Dev set: tasks we may use to tune prompts and routing rules.
# Each test is (arguments_tuple, expected_result).

TASKS = [
    {
        "id": "t01_is_palindrome",
        "entry": "is_palindrome",
        "prompt": (
            "Write a Python function is_palindrome(s) that returns True if the string s "
            "reads the same forwards and backwards, ignoring case and ignoring every "
            "character that is not a letter or a digit. Return only the code."
        ),
        "tests": [
            (("racecar",), True),
            (("A man, a plan, a canal: Panama",), True),
            (("hello",), False),
            (("",), True),
            (("12345",), False),
            (("12321",), True),
            (("ab12ba",), False),
            (("No 'x' in Nixon",), True),
        ],
    },
    {
        "id": "t02_fizzbuzz",
        "entry": "fizzbuzz",
        "prompt": (
            "Write a Python function fizzbuzz(n) that returns a list of strings for the "
            "numbers 1 to n. For multiples of 3 use 'Fizz', for multiples of 5 use "
            "'Buzz', for multiples of both use 'FizzBuzz', otherwise the number as a "
            "string. fizzbuzz(0) returns an empty list. Return only the code."
        ),
        "tests": [
            ((0,), []),
            ((1,), ["1"]),
            ((5,), ["1", "2", "Fizz", "4", "Buzz"]),
            ((15,), ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
                     "11", "Fizz", "13", "14", "FizzBuzz"]),
        ],
    },
    {
        "id": "t03_second_largest",
        "entry": "second_largest",
        "prompt": (
            "Write a Python function second_largest(nums) that takes a list of numbers "
            "and returns the second largest DISTINCT value. If there are fewer than two "
            "distinct values, return None. Return only the code."
        ),
        "tests": [
            (([1, 2, 3],), 2),
            (([3, 3, 2],), 2),
            (([5],), None),
            (([],), None),
            (([2, 2, 2],), None),
            (([-1, -5, -3],), -3),
            (([10, 9, 10, 8],), 9),
        ],
    },
    {
        "id": "t04_count_words",
        "entry": "count_words",
        "prompt": (
            "Write a Python function count_words(text) that returns a dict mapping each "
            "word to how many times it appears. A word is a maximal run of the ASCII "
            "letters a-z or A-Z; everything else separates words. Words are compared "
            "case-insensitively and the keys are lowercase. Return only the code."
        ),
        "tests": [
            (("a b a",), {"a": 2, "b": 1}),
            (("Hello, hello!",), {"hello": 2}),
            (("",), {}),
            (("It's",), {"it": 1, "s": 1}),
            (("one two  three\nthree",), {"one": 1, "two": 1, "three": 2}),
            (("123 !!!",), {}),
        ],
    },
    {
        "id": "t05_merge_intervals",
        "entry": "merge_intervals",
        "prompt": (
            "Write a Python function merge_intervals(intervals) that takes a list of "
            "[start, end] lists and merges all overlapping intervals. Intervals that "
            "touch (for example [1,4] and [4,5]) count as overlapping. Return a list of "
            "[start, end] lists sorted by start. Return only the code."
        ),
        "tests": [
            (([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]),
            (([[1, 4], [4, 5]],), [[1, 5]]),
            (([],), []),
            (([[5, 6], [1, 2]],), [[1, 2], [5, 6]]),
            (([[1, 10], [2, 3]],), [[1, 10]]),
        ],
    },
    {
        "id": "t06_valid_parentheses",
        "entry": "is_valid_parentheses",
        "prompt": (
            "Write a Python function is_valid_parentheses(s) for a string containing "
            "only the characters ()[]{}. Return True if every bracket is closed by the "
            "same type in the correct order, otherwise False. The empty string is "
            "valid. Return only the code."
        ),
        "tests": [
            (("()",), True),
            (("()[]{}",), True),
            (("(]",), False),
            (("([)]",), False),
            (("{[]}",), True),
            (("",), True),
            (("(",), False),
            ((")(",), False),
        ],
    },
]