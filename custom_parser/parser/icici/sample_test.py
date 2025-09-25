import pandas as pd

data = {
    "Name": ["Alice", "Bob", "Charlie", "David"],
    "Age": [25, 30, 35, 40],
    "City": ["New York", "London", "Paris", "Berlin"]
}

df = pd.DataFrame(data)
df.to_csv("sample.csv", index=False)
