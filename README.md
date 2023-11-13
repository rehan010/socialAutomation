
# Smart Presence

Smart Presence is a powerful web application that simplifies social media management. It's designed to help individuals, businesses, and organizations streamline their social media marketing efforts with ease.

## Features

1. #### Multi-Platform Scheduling: 
Schedule posts and content across various social media platforms, including Facebook, Twitter, Instagram, LinkedIn, and more.

2.  #### Analytics: 
Track the performance of your posts and campaigns through detailed analytics.

3. #### Team Collaboration: 
Collaborate with team members and clients, assign roles and permissions, and streamline your social media workflow.

4. #### Automation: 
Automate routine social media tasks, such as posting, reposting, and engaging with your audience.



### Built With

* [![Django][Django]][Django-url]
* [![Tailwindcss][Tailwindcss]][Tailwindcss-url]
* [![JQuery][JQuery.com]][JQuery-url]
* [![HTML][HTML]][HTML-url]
* [![Postgres][Postgres]][Postgres-url]
* [![redis][redis]][redis-url]




[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Django]: https://img.shields.io/badge/django-35495E?style=for-the-badge&logo=django&logoColor=4FC08D
[Django-url]: https://www.djangoproject.com/
[Tailwindcss]:https://img.shields.io/badge/tailwindcss-0F172A?style=for-the-badge&logo=tailwindcss
[Tailwindcss-url]:https://tailwindcss.com/
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[Postgres]: https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white
[HTML]:https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white
[Postgres-url]:https://www.postgresql.org/
[HTML-url]:https://developer.mozilla.org/en-US/docs/Glossary/HTML5
[redis]:https://img.shields.io/badge/redis-%23DD0031.svg?&style=for-the-badge&logo=redis&logoColor=white
[redis-url]:https://redis.io/
## Getting Started

### Prerequisite
* Python 3.8
* Redis
* Django 4.2
* Celery
* Postgres Sql 14.9

#### for Redis on Windows [click here](https://redis.io/docs/install/install-redis/install-redis-on-windows/).

### Installation
1. Make Virtual Enviorment
    ```sh
   pip install virtualenv
   ```
    ```sh
    python<version> -m venv env
   ```
   For `Mac`:
   ```sh
    source env/bin/activate

   ```
   For `Windows`:
   ```sh
    env/Scripts/activate.bat //In CMD
    env/Scripts/Activate.ps1 //In Powershel
   ```


2. Clone the repo
   ```sh
   git clone https://github.com/SmartPresence0313/SmartPresence.git
   ```
3. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
4. Configure your Postgres with credentials

    1. Login In into postgres sql shell.
    2. Create a Database
       ```commandline
            createdb -U username -h hostname -p port <dbname>;
       ```
       or 
       ```commandline
         create database <dbname>;
       ```
      
   3. Create a user and grant permission to that user
      ```commandline
         create user <user_name> with encrypted password 'mypass';
       ```
      ```commandline
         grant all privileges on database <dbname> to <user_name>;
      ```
   4. Open the `settings.py` file in your Automatation project and replace the following database settings with your database settings to connect to your PostgreSQL database:
      ```commandline
      'NAME': 'smart_pre', // Database name 
      'USER': 'smart_pre', // UserName
      'PASSWORD': 'smart123!', //Password
      'HOST': 'localhost', //Host
      'PORT': '5432' // Port
      ```
5. Change directory to `socialAutomation` and Migrate the database
    ```sh
    python manage.py makemigrations
    ```
     ```sh
    python manage.py migrate
    ```
6. Run the development server on localhost:8000
    ```sh
    python manage.py runsslserver
    ```
7. Run `Celery` for background task

     For `Mac`:
     ```sh
        celery -A Automatation worker --beat
     ```
     
     For `Windows`: 

     install `eventlet`:
     ```sh
       pip install eventlet
     ```
     ```sh
       celery -A Automatation worker -l info -P eventlet
     ```
      ```sh
       celery -A Automatation beat -l info 
     ```

## Intial setup

1. Create a superuser/root user from terminal.

```python
  python manage.py createsuperuser
```
2. To Add Social Application Credientials in the database go to `http:localhost:8000/admin` and login through the created credientials of superuser.

3. Go to `Social Application` section from admin panel.

4. Click add Application from right corner

5. Select a correct provider 

6. Enter the name of applications as follow:
   ```commandline
      Instagram --> Instagram
      Linkedin ---> linkedin_oauth2
      Facebook ---> Facebook
      Google -----> Google
   ```
7. Enter correct App id in client id and App secret in secret key.

8. Click Save to save changes.




## License

[MIT](https://choosealicense.com/licenses/mit/)

