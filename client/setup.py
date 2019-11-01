from setuptools import setup, find_packages
import sys

sys.path[0] = sys.path[0] + '\HeroChatClient'

setup(name='HeroChatClient',
      description='Client package for HeroChat.',
      version='0.9.2',
      author='Rex1k',
      author_email='kiber-rex@mail.ru',
      package_dir={'': 'HeroChatClient'},
      packages=find_packages(where=sys.path[0]),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome'])
