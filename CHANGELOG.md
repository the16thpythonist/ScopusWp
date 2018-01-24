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

