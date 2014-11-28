import textblob
import unittest

def sentiment(string):
    assert isinstance(string, basestring)
    blob = textblob.Textblob(string)
    return (blob.sentiment.subjectivity, blob.sentiment.polarity)

def extract_comments(fstring):
    comments = []

    line_comment_tok = '//'
    start_comment_tok = '/*'
    end_comment_tok = '*/'
    
    in_line_comment = False
    in_mline_comment = False
    
    prev_c = ''
    comment = ""
    for c in fstring:
        if prev_c + c == line_comment_tok and not in_mline_comment:
            in_line_comment = True
        elif prev_c + c == start_comment_tok and not in_mline_comment:
            in_mline_comment = True
        elif in_line_comment and c == '\n':
            comments.append(comment)
            comment = ''
            in_line_comment = False
        elif in_mline_comment and prev_c + c == end_comment_tok:
            comments.append(comment.rstrip('*'))
            comment = ''
            in_mline_comment = False
        elif in_line_comment or in_mline_comment:
            comment += c
        prev_c = c
    if in_line_comment:
        comments.append(comment)
    return comments

class TestExtractComments(unittest.TestCase):
    
    def test_no_comments(self):
        self.assertEqual([], extract_comments(""))
        self.assertEqual([], extract_comments("hello world"))
    
    def test_line_comments(self):
        self.assertEqual(['hello world'], extract_comments('//hello world'))
        self.assertEqual(['hello/ /world'], extract_comments('//hello/ /world'))
        self.assertEqual(['hello world'], extract_comments('\n\n//hello world\n'))
        self.assertEqual(['hello', 'world'],
                         extract_comments('//hello\n beautiful\n //world\n'))
        
    
    def test_multiline_comments(self):
        self.assertEqual(['hello\nworld'], extract_comments('/*hello\nworld*/'))
        self.assertEqual(['hello//world'], extract_comments('/*hello//world*/'))

    def test_java_source_file(self):
        path = '/home/tedks/Projects/subsonic/trunk/' + \
               'subsonic-main/src/main/java/org/json/HTTP.java'
        with open(path) as jf:
            comments = extract_comments(jf.read())
        self.assertEqual(8, len(comments))
        self.assertIn("* Carriage return/line feed. ", comments)

