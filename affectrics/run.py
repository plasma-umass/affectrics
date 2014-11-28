"""
Code for running affectrics over a project.
"""
import argparse
import subprocess
import tempfile
import unittest
import sys

from os import path

from diligence import experiment as exp

class GitHubProject(exp.RepoResource):
    def __init__(self, remote_path):
        # need to check out to a local repo
        self.path = None 
        self.remote_path = remote_path
        target_dir = tempfile.mkdtemp()
        git_exit = subprocess.call(['git', 'clone', remote_path, target_dir],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        if git_exit != 0:
            raise ValueError("Couldn't check out repo {} to path {}"
                             .format(remote_path, target_dir))
        super().__init__(target_dir)
        # target_dir is now path thanks to the superclass

class TestGitHubProject(unittest.TestCase):
    
    def testInvalidRemotePath(self):
        with self.assertRaises(ValueError):
            GitHubProject('http://www.example.com')
            
    def testRepoChecksOut(self):
        ghp = GitHubProject('https://github.com/WhisperSystems/TextSecure.git')
        assert path.exists(path.join(ghp.path, '.git'))


class AffectricsExperiment(exp.Experiment):
    def __init__(self, repo):
        assert path.exists(repo)
        
        if not isinstance(repo, exp.RepoResource):
            repo = exp.RepoResource(repo)

        self.repo = repo

    def get_configs(self):
        return []
    
    def get_programs(self):
        pass

def main():
    repo_path = sys.argv[1]
    print("Running over " + repo_path)
    