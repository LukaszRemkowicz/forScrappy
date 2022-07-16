# ForScrappy
4Scrappy is a script responsible for data scrapping. Application login to specialist forum, jump on topics, and parsing link to music download.
Application wrote in Django just for ORM and admin site purpose.

## How to configure the app
1. It's a python based application, so you have to install python on your pc: [download python](https://www.python.org/downloads/)
    ``` 
    Note: 3.8 <= python < 3.9 version is required. 
   ```
2. Download the app or just clone it from repository
3. Create and enable virtual environment using command: `env\Scripts\activate.bat` [virtualenv PyPi](https://pypi.org/project/virtualenv/)
4. Install requirements.txt: `pip install -r requirements.txt`
5. Install database on your pc and choose it as a backend in settings.py (DATABASES variable). Default is sqlite, but Postgres is preferable.
6. Install Tesseract-OCR program: [github](https://github.com/tesseract-ocr/tesseract). Needed for reading the text from img file.
7. Create _env.py file to store the secrets locally. Required variables in new file:
    ```
    SECRET_KEY - django secret key
    REMOVE_FROM_NAME (iterable) - list with strings, which ara removed from song name (clearing the name).
    SYSTEM_USER_EMAIL - where to send notification
    PYTESSERACT - string path to tesseract.exe
    LOGIN_URL - login to forum url
    USERNAME - forum username
    PASSWORD - forum password
   ```
8. Generate secret key in django shell and pase it to .env file. Run the commands:

        cd ForScrappy
        manage.py shell
        from django.core.management.utils import get_random_secret_key
        get_random_secret_key()
        exit()

9. Create database tables:

        manage.py makemigrations
        manage.py migrate
10. Run script with command below to see available parameters:
   ```
   python .\index.py --help
   ```