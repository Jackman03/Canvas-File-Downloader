# Canvas submission downloader
### python script that downloads all of your canvas submissions and lectures
Note that if you have no submissions for a class it will not create a directory for it

## Setup
Use the config.ini file to put in your token and domain
- `TOKEN` is your canvas api token.
- `DOMAIN` is your schools .edu domain.

## Generate the token here
Settings -> Account -> New Access Token

## Run
```shell
python -m pip install -r requirements.txt
```

```shell
python CanvasFileDownloader.py
```

## Output
The file structue creates a directory for each semester then each class directory.

## TODO
Ad the option to download from modules aswell.
Link the semester names to the ids.
Create a generic downloader function
