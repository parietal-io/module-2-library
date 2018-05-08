from __future__ import print_function, absolute_import

import os
import shutil

import click
import jinja2

# This file's directory
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class Options(dict):
    def __init__(self):
        super(Options,self).__init__()
        self['pkgname'] = None
        self['pkgimp'] = None
        self['pymod'] = ''
        self['author'] = ''


pass_options = click.make_pass_decorator(Options, ensure=True)

# @click.group()
@click.command()
@click.argument('pymod')
@click.option('--pkgname', default=None, type=str, help="Name of package to install")
@click.option('--pkgimp', default=None, type=str, help="Namespace of package to import")
@click.option('--version', default='0.1', type=str, help="Version of the package")
@click.option('--requires', default=None, type=str, help="Comma-separated list of dependencies")
@click.option('--author', default=None, type=str, help="Name of package author")
@click.option('--description', default=None, type=str, help="Short package description")
@click.option('--dest', default=None, type=str, help="Top directory where package should be created")
@click.option('--entrypoint', default=None, type=str, help="Function in module to use as entrypoint")
@click.option('--datadir', default=None, type=str, help="Data directory (recursively copied)")
# @pass_options
def cli(pymod, pkgname, pkgimp, version, requires, author, description, dest, entrypoint, datadir):
    """
    Module-to-Library: setup a minimal Python package around a module
    """
    options = Options()
    options['pkgname'] = pkgname
    options['pkgimp'] = pkgimp
    options['version'] = version
    options['requires'] = requires
    options['author'] = author
    options['description'] = description
    options['dest'] = dest
    options['entrypoint'] = entrypoint
    options['datadir'] = datadir

    init(options, pymod)


class Package(object):
    """
    Handles package metadata; then used by (jinja) templates

    Attributes:
     - pymod
     - pkgname
     - pkgimp
     - version
     - requires
     - description
     - author
     - dest
     - entrypoint
     - datadir
    """

    def __init__(self, options):
        assert options['pymod']
        assert options['version']
        self.pymod = options['pymod']
        self.version = options['version']

        self.pkgimp = self.set_pkgimp(options['pkgimp'])
        self.pkgname = self.set_pkgname(options['pkgname'])
        assert self.pkgname and self.pkgimp

        self.entrypoint = options['entrypoint']

        self.author = self.set_author(options['author'])
        self.description = self.set_description(options['description'])
        assert not(self.author is None or self.description is None)

        self.path = self.set_path(options['dest'])

        self.requires = self.set_requires(options['requires'])

        self.datadir = self.set_datadir(options['datadir'])

    def set_pkgname(self, pkgname):
        if pkgname is None or pkgname.strip() == '':
            #TODO: normalize better pakcage-name (whitespaces, periods, etc.)
            pkgname = self.pymod.rstrip('\.py')
        return pkgname

    def set_pkgimp(self, pkgimp):
        if pkgimp is None or pkgimp.strip() == '':
            #TODO: normalize better package import/namespace
            pkgimp = self.pymod.rstrip('\.py')
        return pkgimp

    def set_author(self, author):
        return author or "Anonymous author"

    def set_description(self, description):
        return description or "The {} package.".format(self.pkgname)

    def set_path(self, dest):
        if dest:
            dest = os.path.join(os.path.abspath(dest), self.pkgname)
        else:
            dest = os.path.abspath(self.pkgname)
        return dest

    def set_requires(self, requires):
        # reqs = []
        # for req in requires:
        #     reqs.extend(req.split(','))
        return requires.split(',') if requires else []

    def set_datadir(self, datadir):
        if datadir:
            assert os.path.exists(datadir), "Data directory '{}' not found".format(datadir)
            return os.path.abspath(datadir)


# @cli.command()
# @click.argument('pymod')
# @pass_options
def init(options, pymod):
    """
    Initialize package schema from '.py' module
    """
    assert os.path.exists(pymod), "Module '{}' not found.".format(pymod)

    options['pymod'] = pymod
    pkg = Package(options)
    do_package(pkg)
    do_readme(pkg)
    do_setuptools(pkg)
    do_tests(pkg)
    do_conda(pkg)
    # _license(pkg)
    do_git(pkg)
    do_versioneer(pkg)
    do_commit_version(pkg)


def do_package(pkg):
    """
    Copy module to package
    """
    path_pkg = pkg.path
    if os.path.exists(path_pkg) and os.path.isdir(path_pkg):
        shutil.rmtree(path_pkg)
    os.mkdir(path_pkg)

    path_src = os.path.join(path_pkg, pkg.pkgimp)
    if not os.path.exists(path_src):
        os.mkdir(path_src)
    shutil.copy(pkg.pymod, path_src)

    _src = os.path.join('src', '__init__.py')
    templates.render(_src, pkg, subdir=pkg.pkgimp)

    # Copy (optional) data directory to pkg-directory
    if pkg.datadir:
        _do_datadir(pkg.datadir, path_pkg, pkg)

def _do_datadir(path_data, path_pkg, pkg):
    assert os.path.exists(path_data) and os.path.isdir(path_data)
    from distutils.dir_util import copy_tree
    _dest = os.path.basename(path_data)
    _dest = os.path.join(path_pkg, _dest)
    copy_tree(path_data, _dest)

def do_readme(pkg):
    """
    Render README file
    """
    templates.render('README.md', pkg)


def do_setuptools(pkg):
    """
    Render setup.{py,cfg} files
    """
    for fname in ['setup.cfg','setup.py']:
        templates.render(fname, pkg)


def do_tests(pkg):
    """
    Copy tests structure
    """
    _src = os.path.join('tests','test_core.py')
    templates.render(_src, pkg, subdir='tests')



def do_conda(pkg):
    """
    Render conda-recipe
    """
    _src = os.path.join('conda_recipe', 'meta.yaml')
    templates.render(_src, pkg, subdir='conda_recipe')


def _license():
    pass


def do_git(pkg):
    """
    Create git repository, add all files
    """
    git_init_all = 'git init && git add * && git commit -am "Init package"'

    _path = pkg.path
    assert os.path.exists(_path) and os.path.isdir(_path)
    _pwd = os.getcwd()
    try:
        os.chdir(_path)
        os.system(git_init_all)
    finally:
        os.chdir(_pwd)


def do_versioneer(pkg):
    """
    Setup versioneer to package
    """
    _path = pkg.path
    assert os.path.exists(_path) and os.path.isdir(_path)

    _pwd = os.getcwd()
    try:
        os.chdir(_path)
        os.system('versioneer install')
    finally:
        os.chdir(_pwd)


def do_commit_version(pkg):
    """
    Finish packaging with commit/version-tag
    """
    git_commit_all = 'git commit -am "Module packaged"'
    git_tag_version = 'git tag -am "Version {0}" {0}'.format(pkg.version)

    _path = pkg.path
    assert os.path.exists(_path) and os.path.isdir(_path)
    _pwd = os.getcwd()
    try:
        os.chdir(_path)
        os.system(git_commit_all)
        os.system(git_tag_version)
    finally:
        os.chdir(_pwd)


class templates:
    path = os.path.join(THIS_DIR, 'templates')

    @classmethod
    def get(cls, name):
        from jinja2 import Environment, FileSystemLoader
        _env = Environment(loader=FileSystemLoader(cls.path),
                           keep_trailing_newline=True)
        return _env.get_template(name)

    @staticmethod
    def render(pathname, pkg, subdir=None):
        def assure_dir(path):
            if not (os.path.exists(path) or os.path.isdir(path)):
                os.mkdir(path)

        temp = templates.get(pathname)
        cont = temp.render(pkg=pkg)

        write_to = pkg.path
        assure_dir(write_to)
        if subdir:
            write_to = os.path.join(write_to, subdir)
            assure_dir(write_to)

        basename = os.path.basename(pathname)
        write_to = os.path.join(write_to, basename)

        with open(write_to, 'w') as fp:
            fp.write(cont)


if __name__ == "__main__":
    cli()
