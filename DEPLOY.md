## Deploy on Heroku

Heroku offers a free server option for 550h a month. But it has the disadvantage
of using ephemeral containers who do not support *media* uploaded by the users.

A version of MicrofauneAnnotator where the audio files are stored in the database 
exists in the branch heroku.

To deploy it the following steps must be followed:

* Some prerequisites:
  * Clone the repository MicrofauneAnnotator
  * Create a free Heroku account
  * Install the heroku cli: `sudo snap install heroku --classic`
  * heroku login
* Config the build steps of heroku:
```
heroku buildpacks:set heroku/python
heroku buildpacks:add --index 1 heroku-community/apt
```
* Push the branch *heroku* to master on heroku server: `git push heroku heroku:master`
* Create the database: `heroku run python manage.py migrate`
* Create a superuser: `heroku run python manage.py createsuperuser`
