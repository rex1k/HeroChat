from setuptools import setup, find_packages
import sys

sys.path[0] = sys.path[0] + '\HeroChatServer'

setup(name='HeroChatServer',
      description='Server package for HeroChat.',
      version='0.9.2',
      author='Rex1k',
      author_email='kiber-rex@mail.ru',
      package_dir={'': 'HeroChatServer'},
      packages=find_packages(where=sys.path[0]),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome'])
