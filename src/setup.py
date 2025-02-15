import setuptools
from distutils.util import convert_path
from fnmatch import fnmatchcase
import os

bulb_version = "0.0.75"

with open("README.md", "r") as fh:
    long_description = fh.read()
    



# Provided as an attribute, so you can append to these instead
# of replicating them:
standard_exclude = ('*.py', '*.pyc', '*$py.class', '*~', '*.bak')
standard_exclude_directories = ('CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info', "node_modules")
    
# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
# Note: you may want to copy this into your setup.py file verbatim, as
# you can't import this from another package, when you don't know if
# that package is installed yet.
def find_package_data(where='.', package='',
                      exclude=standard_exclude,
                      exclude_directories=standard_exclude_directories,
                      only_in_packages=True,
                      show_ignored=False):
    """
    Return a dictionary suitable for use in ``package_data``
    in a distutils ``setup.py`` file.
    The dictionary looks like::
        {'package': [files]}
    Where ``files`` is a list of all the files in that package that
    don't match anything in ``exclude``.
    If ``only_in_packages`` is true, then top-level directories that
    are not packages won't be included (but directories under packages
    will).
    Directories matching any pattern in ``exclude_directories`` will
    be ignored; by default directories with leading ``.``, ``CVS``,
    and ``_darcs`` will be ignored.
    If ``show_ignored`` is true, then all the files that aren't
    included in package data are shown on stderr (for debugging
    purposes).
    Note patterns use wildcards, or can be exact paths (including
    leading ``./``), and all searching is case-insensitive.
    """

    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern) or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print("Directory %s ignored by pattern %s" %
                                  (fn, pattern), file=sys.stderr)
                        break
                if bad_name:
                    continue
                if (os.path.isfile(os.path.join(fn, '__init__.py')) and not prefix):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append((fn, prefix + name + '/', package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern) or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print("File %s ignored by pattern %s" %
                                  (fn, pattern), file=sys.stderr)
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix + name)
    return out


setuptools.setup(
    name="bulb-core",
    version=bulb_version,
    author="Lilian Cruanes",
    author_email="cruaneslilian@gmail.com",
    description="Neo4j integration for Django, and much more tools for deployment of consequent websites...",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LilianCruanes/bulb",
    packages=setuptools.find_packages(),
    package_data=find_package_data(),
    install_requires=['neo4j', "Pillow-SIMD", "requests", "paramiko", "pysftp", "bcrypt", "scour", "django-compressor"],
    # bcrypt: for password hashing,
    # requests: for CDNs purge requests,
    # pysftp: for sftp content saving,
    # django-compressor & django-libsass: for sass/scss support during bundle operations,
    # Pillow-SIMD: for images compression and optimization.
    # paramiko: for SSH handling
    extras_require={"django-libsass": ["django-libsass"]},
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Natural Language :: English",
        "Topic :: Database",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "Topic :: Internet :: WWW/HTTP :: WSGI"
    ],
)
