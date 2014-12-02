"""
Code for running affectrics over a project.
"""
import argparse
import subprocess
import tempfile
import unittest

from functools import partial
from os import path

from diligence import experiment as exp
from diligence import tasks 

from . import affect
from . import metrics

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
        """Callbacks should return rows in a CSV, so a name and a
        value of the same type.

        """
        assert all(callable(c) for c in callbacks)
        self.callbacks = callbacks
        self.repos = [GitHubProject(p) for p in repos]
        if taskrunner is None:
            taskrunner = tasks.ThreadTaskRunner
        self.taskrunner = taskrunner()

    def run(self):
        all_tasks = []
        for r in self.repos:
            for t in r.map(self.make_tasks):
                if t is None: continue
                assert isinstance(t, tasks.Task), t
                all_tasks.append(t)
            
        assert all(isinstance(t, tasks.Task) for t in all_tasks), all_tasks

        results = self.taskrunner.run_tasks(all_tasks)
        return self.postprocess(results)
        
    def make_tasks(self, reporesource, repo, i, c):
        if len(c.parents) > 1: return None

        return tasks.Task(partial(self.run_callbacks,
                                  reporesource, repo, i, c),
                          passon = {'reporesource': reporesource,
                                    'repo': repo, 'count': i,
                                    'commit': c})

    def postprocess(self, results):
        return results

    def run_callbacks(self, repres, repo, i, c):
        """Run the callbacks and return a mixed dictionary of
        results.

        """
        results = {}
        for cb in self.callbacks:
            results.update(cb(repres, repo, i, c))
        return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", "r", type=str, 
                        help=("Repositories to analyze. "
                              "Can be a local path or a remote GIT url."))
    args = parser.parse_args()
    exp = AffectricsExperiment(
        [args.repo],
        [affect.affect_callback,
         metrics.complexity_callback],
        # taskrunner = tasks.TaskRunner
    )
    return exp.run()