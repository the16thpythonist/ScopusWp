from ScopusWp.scopus.data import ScopusPublication, ScopusAuthor, ScopusAuthorProfile, ScopusAffiliation
from ScopusWp.scopus.data import ScopusAuthorObservation

from ScopusWp.scopus.scopus import ScopusAffiliationController
from ScopusWp.scopus.scopus import ScopusAuthorController
from ScopusWp.scopus.scopus import ScopusPublicationController

import pytest


############################
# THE DATA STRUCTURE TESTS #
############################

# THE FIXTURES FOR SAMPLE DATA STRUCTURES

@pytest.fixture
def scopus_author_profile_sample():
    scopus_author_profile = ScopusAuthorProfile(
        1,
        'Max',
        'Mustermann',
        13,
        7,
        2,
        [345, 346]
    )
    return scopus_author_profile


@pytest.fixture
def scopus_author_sample():
    scopus_author = ScopusAuthor(
        'Max',
        'Mustermann',
        1,
        [12]
    )
    return scopus_author


@pytest.fixture
def scopus_publication_sample():
    scopus_publication = ScopusPublication(
        31415,
        '2e1234567',
        '2k-str.9876',
        'Sample publication title',
        'Sample publication description',
        '12-12-17',
        ScopusAuthor("max", "mustermann", 1, 12),
        [
            ScopusAuthor('Max', 'Mustermann', 1, [12]),
            ScopusAuthor('Sabine', 'Müller', 2, [34, 35]),
            ScopusAuthor('Karl', 'Weber', 3, [56])
        ],
        [345, 897, 675],
        ['keyword', 'apple', 'banana'],
        'nature',
        '12'
    )
    return scopus_publication


@pytest.fixture
def scopus_author_observation_sample():
    scopus_author_observation = ScopusAuthorObservation(
        [2],
        'Sabine',
        'Müller',
        [34, 23],
        [35, 12, 45]
    )
    return scopus_author_observation


def test_scopus_author_profile_id_interface(scopus_author_profile_sample):
    scopus_author_profile = scopus_author_profile_sample  # type: ScopusAuthorProfile
    assert scopus_author_profile.get_id() == 1
    assert int(scopus_author_profile) == 1


def test_scopus_author_id_interface(scopus_author_sample):
    # Tests if the interface for getting the id from an object implemented correctly
    scopus_author = scopus_author_sample  # type: ScopusAuthor
    assert scopus_author.get_id() == 1
    assert int(scopus_author) == 1


def test_scopus_author_contains_affiliations(scopus_author_sample):
    scopus_author = scopus_author_sample  # type: ScopusAuthor
    assert scopus_author.contains_affiliation(12)


def test_scopus_publication_id_interface(scopus_publication_sample):
    scopus_publication = scopus_publication_sample  # type: ScopusPublication
    assert scopus_publication.get_id() == 31415
    assert int(scopus_publication) == 31415


def test_scopus_publication_affiliations(scopus_publication_sample):
    # Tests if the list of all the affiliations will be assembled correctly for a publication object
    scopus_publication = scopus_publication_sample  # type: ScopusPublication
    assert sorted(scopus_publication.affiliations) == sorted([12, 34, 35, 56])
    # Tests if the contains affiliation works correctly
    assert scopus_publication.contains_affiliation(34)


def test_scopus_publication_contains_author(scopus_publication_sample, scopus_author_sample,
                                            scopus_author_profile_sample):
    # Tests if the contains author method works with a ScopusAuthor object
    scopus_publication = scopus_publication_sample  # type: ScopusPublication
    scopus_author = scopus_author_sample  # type: ScopusAuthor
    assert scopus_publication.contains_author(scopus_author)
    # Tests if the contains author method works with a ScopusAuthorProfile object
    scopus_author_profile = scopus_author_profile_sample
    assert scopus_publication.contains_author(scopus_author_profile)


def test_scopus_publication_contains_keyword(scopus_publication_sample):
    # Tests if the contains keyword method of the scopus publication object works correctly
    scopus_publication = scopus_publication_sample  # type: ScopusPublication
    assert scopus_publication.contains_keyword('apple')


def test_scopus_author_observation_whitelist_contains(scopus_author_observation_sample):
    scopus_author_observation = scopus_author_observation_sample  # type: ScopusAuthorObservation
    assert scopus_author_observation.whitelist_contains(23)
    assert scopus_author_observation.whitelist_contains_any([78, 99, 65, 23])


def test_scopus_author_observation_whitelist_check_publication(scopus_author_observation_sample,
                                                               scopus_publication_sample):
    scopus_author_observation = scopus_author_observation_sample  # type: ScopusAuthorObservation
    scopus_publication = scopus_publication_sample
    assert scopus_author_observation.whitelist_check_publication(scopus_publication)


def test_scopus_author_observation_blacklist_contains(scopus_author_observation_sample):
    scopus_author_observation = scopus_author_observation_sample  # type: ScopusAuthorObservation
    assert scopus_author_observation.blacklist_contains(12)
    assert scopus_author_observation.blacklist_contains_any([33, 66, 78, 99, 92, 12])


def test_scopus_author_observation_blacklist_check_publication(scopus_author_observation_sample,
                                                               scopus_publication_sample):
    scopus_author_observation = scopus_author_observation_sample  # type: ScopusAuthorObservation
    scopus_publication = scopus_publication_sample
    assert scopus_author_observation.blacklist_check_publication(scopus_publication)


################################
# THE SCOPUS CONTROLLERS TESTS #
################################


def test_affiliation_request():
    affiliation_controller = ScopusAffiliationController()
    scopus_affiliation = affiliation_controller.get_affiliation(60102538)
    assert isinstance(scopus_affiliation, ScopusAffiliation)
    assert scopus_affiliation.country == 'Germany'
    assert scopus_affiliation.city == 'Karlsruhe'
    assert scopus_affiliation.institute == "Karlsruhe Institute of Technology"


def test_author_request():
    author_controller = ScopusAuthorController()
    scopus_author_profile = author_controller.get_author(56950893700)
    assert isinstance(scopus_author_profile, ScopusAuthorProfile)
    assert scopus_author_profile.first_name == 'Andrei'
    assert scopus_author_profile.last_name == 'Shkarin'


def test_publication_request():
    publication_controller = ScopusPublicationController()
    scopus_publication = publication_controller.get_publication(84899652059)
    assert isinstance(scopus_publication, ScopusPublication)
    assert int(scopus_publication) == 84899652059
