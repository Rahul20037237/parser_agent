
import pandas as pd
data = {"Name": ["Alice", "Bob"], "Age": [25, 30], "City": ["NY", "LD"]}
df = pd.DataFrame(data)
df.to_csv("generated.csv", index=False)
