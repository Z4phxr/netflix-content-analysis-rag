import pandas as pd

df = pd.read_csv('/app/data/netflix_with_embeddings.csv', usecols=['title'])
print('csv_rows=', len(df))
print('distinct_titles_in_csv=', df['title'].nunique())
