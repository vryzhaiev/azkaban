#!/usr/bin/env python
# encoding: utf-8

"""Test Azkaban pig extension."""

from azkaban.ext.pig import *
from azkaban.project import Project
from azkaban.util import AzkabanError, Config, temppath
from nose.tools import eq_, ok_, raises, nottest
from os.path import dirname, relpath
from zipfile import ZipFile


class TestPigJob(object):

  def test_init(self):
    with temppath() as path:
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      # forcing type to override potential configuration option
      job = PigJob(path, {'a': 2}, {'a': 3, 'b': 4}, {'type': 'pig'})
      with temppath() as tpath:
        job.build(tpath)
        with open(tpath) as reader:
          eq_(
            reader.read(),
            'a=3\nb=4\npig.script=%s\ntype=pig\n' % (path.lstrip('/'), )
          )

  def test_override_type(self):
    with temppath() as path:
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      job = PigJob(path, {'type': 'bar'})
      with temppath() as tpath:
        job.build(tpath)
        with open(tpath) as reader:
          eq_(
            reader.read(),
            'pig.script=%s\ntype=bar\n' % (path.lstrip('/'), )
          )

  def test_on_add(self):
    project = Project('pj')
    with temppath() as path:
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      project.add_job('foo', PigJob(path))
      eq_(project._files, {path: path})

  def test_format_jvm_args(self):
    with temppath() as path:
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      job = PigJob(path, {'jvm.args': {'a': 2, 'b': 2}}, {'jvm.args.a': 3})
      with temppath() as tpath:
        job.build(tpath)
        with open(tpath) as reader:
          eq_(
            reader.read(),
            'jvm.args=-Da=3 -Db=2\npig.script=%s\ntype=%s\n' % (
              path.lstrip('/'), Config().get_option('azkabanpig', 'type', 'pig')
            )
          )

  def test_on_add_absolute(self):
    project = Project('pj')
    with temppath() as path:
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      # forcing type to override potential configuration option
      project.add_job('foo', PigJob(path, {'type': 'pig'}))
      eq_(project._files, {path: path})
      with temppath() as zpath:
        project.build(zpath)
        reader = ZipFile(zpath)
        try:
          apath = path.lstrip('/')
          files = reader.namelist()
          ok_('foo.job' in files)
          ok_(apath in files)
          eq_(reader.read('foo.job'), 'pig.script=%s\ntype=pig\n' % (apath, ))
        finally:
          reader.close()

  @raises(AzkabanError)
  def test_on_add_relative_without_root(self):
    with temppath() as path:
      root = dirname(path)
      project = Project('pj')
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      rpath = relpath(path, root)
      project.add_job('foo', PigJob(rpath, {'type': 'pig'}))

  def test_on_add_relative_with_root(self):
    with temppath() as path:
      root = dirname(path)
      project = Project('pj', root=root)
      with open(path, 'w') as writer:
        writer.write('-- pig script')
      # forcing type to override potential configuration option
      rpath = relpath(path, root)
      project.add_job('foo', PigJob(rpath, {'type': 'pig'}))
      eq_(project._files, {path: rpath})
      with temppath() as zpath:
        project.build(zpath)
        reader = ZipFile(zpath)
        try:
          files = reader.namelist()
          ok_('foo.job' in files)
          ok_(rpath in files)
          eq_(reader.read('foo.job'), 'pig.script=%s\ntype=pig\n' % (rpath, ))
        finally:
          reader.close()
