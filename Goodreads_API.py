import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "8AxkJ7H3Zk1zWPKuO73r4A", "isbns": "9781632168146"})
print(res.json())
