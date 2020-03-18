### Local deploy
Run redis container with:
```
docker-compose up -d
```

Sorry - needed to run all with docker-compose / but have some troubles
```
virtualenv venv
 . venv/bin/activate
pip install -r requirements.txt
```

After that run scrapper what collect info:
```
python3 scraper.py
```
It will write total count of all collected sections

And run server
```
python3 server.py
```