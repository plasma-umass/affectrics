"""
Code for running affectrics over a project.
"""
import argparse
import itertools as itls
import subprocess
import tempfile
import unittest
import sys

from os import path

from diligence import experiment as exp
from diligence import tasks as task

class GitHubProject(exp.RepoResource):
    def __init__(self, path):
        if path.startswith('https://'):
            target_path = tempfile.mkdtemp()
            self.fetch(path, target_dir=target_path)
            path = target_path

        super().__init__(path)
        # target_dir is now path thanks to the superclass

    def fetch(self, remote_path, target_dir=None):
        """Clone a remote repo from remote_path into self.path, or
        target_dir if given.
        """
        if target_dir is None:
            target_dir = self.path
            
        assert remote_path.startswith('http')
        assert path.exists(target_dir)

        self.remote_path = remote_path
        git_exit = subprocess.call(['git', 'clone',
                                    remote_path, target_dir],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        if git_exit != 0:
            raise ValueError("Couldn't check out repo {} to path {}"
                             .format(remote_path, target_dir))

class TestGitHubProject(unittest.TestCase):
    
    def testInvalidRemotePath(self):
        with self.assertRaises(ValueError):
            GitHubProject('http://www.example.com')
            
    def testRepoChecksOut(self):
        ghp = GitHubProject('https://github.com/WhisperSystems/TextSecure.git')
        assert path.exists(path.join(ghp.path, '.git'))


class AffectricsExperiment(object):
    def __init__(self, repos, callbacks, taskrunner=None):
        assert all(callable(c) for c in callbacks)
        self.callbacks = callbacks
        self.repos = [GitHubProject(p) for p in repos]
        if taskrunner is None:
            taskrunner = task.ThreadTaskRunner
        self.taskrunner = taskrunner()

    def run(self):
        all_tasks = []
        for r in self.repos:
            for mapres in r.map(self.make_tasks):
               for t in mapres:
                   assert isinstance(t, task.Task), t
                   all_tasks.append(t)
            
        assert all(isinstance(t, task.Task) for t in all_tasks), all_tasks

        results = self.taskrunner.run_tasks(all_tasks)
        return self.postprocess(results)
        
    def make_tasks(self, repo, i, c):
        return [task.Task(lambda: callback(repo, i, c),
                          passon = {'repo': repo, 'count': i,
                                    'commit': c})
                for callback in self.callbacks]


    def postprocess(self, results):
        return results
    

def main():
    exp = AffectricsExperiment(
        ['https://github.com/WhisperSystems/TextSecure.git'],
        [lambda r,i,c: c.message]
    )
    return exp.run()