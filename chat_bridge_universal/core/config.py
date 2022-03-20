import json
import os
from typing import TypeVar, Type

from mcdreforged.utils.serializer import Serializable


class CBUConfigBase(Serializable):
    aes_key: str = 'ThisIsSecret'


class ClientMeta(Serializable):
    name: str
    password: str


T = TypeVar('T', bound=CBUConfigBase)


def load_config(config_path: str, config_class: Type[T]) -> T:
    config = config_class.get_default()
    if not os.path.isfile(config_path):
        print('Configure file not found!'.format(config_path))
        with open(config_path, 'w', encoding='utf8') as file:
            json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
        print('Default example configure generated'.format(config_path))
        return load_config(config_path, config_class)
    else:
        with open(config_path, encoding='utf8') as file:
            config.update_from(json.load(file))
        with open(config_path, 'w', encoding='utf8') as file:
            json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
        return config
