from api import get_events_followed_profiles
import pandas as pd
import numpy as np

get_events_followed_profiles()


# Generate a dummy DataFrame with random data
data = {
    'id': range(1, 6),
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': np.random.randint(20, 40, size=5),
    'score': np.random.uniform(60.0, 100.0, size=5).round(2),
    'passed': [True, True, False, True, False]
}

df = pd.DataFrame(data)
df.to_csv('test.csv', index=False)