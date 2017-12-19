from ScopusWp.config import PATH

import json
import pathlib


class IDManagerInterface:

    def new(self):
        raise NotImplementedError()

    def delete(self, publication_id):
        raise NotImplementedError

    @property
    def all(self):
        raise NotImplementedError()

    @property
    def used(self):
        raise NotImplementedError()

    @property
    def unused(self):
        raise NotImplementedError()


class IDManagerSingleton(IDManagerInterface):

    _instance = None

    def __init__(self):
        self.path_string = '{}/ids.json'
        self.path = pathlib.Path(self.path_string)

        content_dict = self.load()
        self.used_ids = content_dict['used']
        self.unused_ids = content_dict['unused']
        self.pointer = content_dict['pointer']

    def save(self):
        with self.path.open(mode='w') as file:
            content_dict = {
                'used': self.used_ids,
                'unused': self.unused_ids,
                'pointer': self.pointer
            }
            json.dump(content_dict, file)

    def new(self):
        self.pointer += 1
        return self.pointer

    def delete(self, publication_id):
        if publication_id in self.used_ids:
            self.used_ids.remove(publication_id)
            self.unused_ids.append(publication_id)

    def load(self):
        with self.path.open(mode='r') as file:
            content_dict = json.load(file)
        return content_dict

    @staticmethod
    def get_instance():
        if IDManagerSingleton._instance is None:
            # Creating a new instance
            id_manager = IDManagerSingleton()
            IDManagerSingleton._instance = id_manager
            return id_manager
        else:
            return IDManagerSingleton._instance

    @property
    def all(self):
        return self.used_ids

    @property
    def used(self):
        return self.used_ids

    @property
    def unused(self):
        return self.unused_ids



class ReferenceModel:

    def __init__(self):
        pass