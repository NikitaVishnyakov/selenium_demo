expected = {
    "plugin_a": "1.2",
    "plugin_b": "2.0"
}

actual = {
    "plugin_a": "1.0"
}

for i in expected:
    if i not in actual:
        print(f"{i} not in {actual}")
    elif actual[i] != expected[i]:
        print(f"{i} not equals {expected[i]} in {actual}")


