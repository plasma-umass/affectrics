import re
import subprocess

from io import StringIO

def complexity_callback(repores, repo, i, c):
    complexities = []
    for name, blob in repores.files_of_commit(repo, c):
        if not name.endswith('.java'): continue
        complexities.append(complexity(blob.data))
    N = len(complexities)
    return {'avg_complexity': (sum(complexities) / N
                               if N > 0 else 0)}

def complexity(file_blob):
    JAVANCSS_PATH = "/home/tedks/Source/javancss/bin/javancss"
    ncss = subprocess.Popen([JAVANCSS_PATH, '-function'],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (output, error) = ncss.communicate(input=file_blob)
    retval = ncss.wait()

    if retval != 0 or output is None:
        return 0

    mobj = re.search('Average Function CCN:\s*(\d)', output.decode())
    if mobj is not None:
        return int(mobj.group(1))
    else:
        return 0