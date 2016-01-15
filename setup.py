from distutils.core import setup
setup(
  name = 'shippy',
  packages = ['shippy'], # this must be the same as the name above
  version = '0.1',
  description = 'A python interface to the Ship issue tracker',
  author = 'James Howard',
  author_email = 'james@realartists.com',
  url = 'https://github.com/realartists/shippy',
  download_url = 'https://github.com/realartists/shippy/tarball/0.1',
  keywords = [], # arbitrary keywords
  classifiers = [],
  install_requires=['requests']
)
