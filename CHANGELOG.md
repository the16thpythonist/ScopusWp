# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.0.0] - 2018-01-08

### Added

- Initial release
- A method for updating new posts onto the website based on the observed authors

## [0.1.0] - 2018-01-24

### Added

- A method for updating the citation comments on the scopus posts on the wordpress site
- Added a database table for comment references
- Added a mandatory close() method to the top controller

### Changed

- Changed the naming of the post reference class
- Made the post reference class use the config file for table name
- Fixed the ids json not saving and thus creating duplicate keys

## [0.2.0] - 2018-01-24

### Added

- A datetime column in the post reference table for when the comments of that post were updated
- The functionality to specify the amount of days until the comments update has to be repeated in the config
- An option for the update of comments to specify roughly how many to be done in one session

## [0.2.1] - 05.02.2018

### Added 

- The ScopusAuthorPublicationFetcher which is a object, that handles getting the publications of an author

### Fixed

- The issue, that author profiles had only up to 25 publications saved to them 
because the scopus search only returned 25 items per request

## [0.2.2]

### Fixed

- The problem with the categories in the scopus author observation file 
not actually making it to the post on the website

## [0.3.0]

**Installer Update**
Changed the installation process in a way, that the project can be installed via pip into the 
site packages folder normally, without the need to modify python path or create local folder structure 
for the dependencies. The recommended installation process is using pipenv and then importing the main 
functions classes into a new module in the pipenv project folder

## Added

- A 'VERSION' variable in the config module
- A 'PROJECT_PATH' variable in the config module. In the shipping version of the project this variable is 
empty, but once running the installation script from the install module, the user is prompted to select 
a project folder for ScopusWp and the variable will then hold the this path.
- Controller to install.py, which prompts the user to input the project path, where the 
non code files are supposed to be stored
- SetupController: A method to setup the database tables

## Changed

- install.py: All controllers are now based on creating the files in a folder that is given 
to them in construction instead of using the config.PATH right of the bat
