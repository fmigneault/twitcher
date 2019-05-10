import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

about = {}
with open(os.path.join(here, 'twitcher', '__meta__.py'), 'r') as f:
    exec(f.read(), about)

reqs = [line.strip() for line in open('requirements.txt')]
extra_reqs = [line.strip() for line in open('requirements_dev.txt')]

setup(name='pyramid_twitcher',
      version=about['__version__'],
      description=about['__description__'],
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "Development Status :: 4 - Beta",
      ],
      author=about['__author__'],
      author_email=about['__email__'],
      url=about['__repository__'],
      license='Apache License 2.0',
      keywords='pyramid twitcher birdhouse wps security proxy ows ogc',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='twitcher',
      python_requires='>=3.7',
      install_requires=reqs,
      extra_requires={
          "dev": extra_reqs,    # pip install -e '.[dev]'
      },
      entry_points="""\
      [paste.app_factory]
      main = twitcher:main
      [console_scripts]
      twitcherctl=twitcher.twitcherctl:main
      """,
      )
