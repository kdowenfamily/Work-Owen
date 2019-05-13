#!/usr/bin/python

class User(object):
    """Represents a single <user> element"""

    def __init__(self):
        self.id = None
        self.display_name = None

class Post(object):
    """Represents a single <post> element"""

    def __init__(self):
        self.id = None
        self.post_type_id = None
        self.owner_user_id = None
        self.accepted_answer_id = None

class MapData(object):
    """Represents an object for counting based on name"""

    def __init__(self):
        self.display_name = None
        self.count = 0

class ServerFault(object):
    def __init__(self):
        self.users = {}
        self.posts = {}

    @staticmethod
    def parse_field_from_line(line, key):
        # We're looking for a thing that looks like:
        # [key]="[value]"
        # as part of a larger String.
        # We are given [key], and want to return [value].

        key_pattern = '%s="' % key
        idx = line.find(key_pattern)

        if idx == -1:
            return ""

        # find the start and end of the value
        start = idx + len(key_pattern)
        end = start
        while line[end] != '"':
            end = end + 1

        return line[start:end]

    def read_users(self, filename):
        inputf = open(filename, 'r')

        for line in inputf:
            user = User()
            user.id = self.parse_field_from_line(line, 'Id')
            user.display_name = self.parse_field_from_line(line, 'DisplayName')
            self.users[user.id] = user

    def read_posts(self, filename):
        inputf = open(filename, 'r')

        for line in inputf:
            post = Post()
            post.id = self.parse_field_from_line(line, 'Id')
            post.post_type_id = self.parse_field_from_line(line, 'PostTypeId')
            post.owner_user_id = self.parse_field_from_line(line, 'OwnerUserId')
            post.accepted_answer_id = self.parse_field_from_line(line, 'AcceptedAnswerId')
            self.posts[post.id] = post

    def find_user(self, id):
        if id in self.users:
            return self.users[id]
        return User()

    def run(self):
        self.read_users('users-short.xml')
        self.read_posts('posts-short.xml')

        # counting username to answer count
        answers = {}

        for post in self.posts.itervalues():
            user = self.find_user(post.owner_user_id)
            if user.id not in answers:
                answers[user.id] = MapData()
                answers[user.id].display_name = user.display_name
            if post.post_type_id == "2":
                answers[user.id].count = answers[user.id].count + 1

        print "Top 10 users with the most answers:"
        for i in xrange(10):
            max_key = None
            max_data = None

            for (key, data) in answers.iteritems():
                if max_data is None or data.count > max_data.count:
                    max_data = data
                    max_key = key

            del answers[max_key]

            print "%d\t%s" % (max_data.count, max_data.display_name)

        print

        # counting username to accepted answers
        accepted_answers = {}

        for answer_post in self.posts.itervalues():
            # Is this post an accepted answer?
            if answer_post.post_type_id == "2":
                for post in self.posts.itervalues():
                    if post.post_type_id == "1" and post.accepted_answer_id == answer_post.id:
                        user = self.find_user(answer_post.owner_user_id)
                        if user.id not in accepted_answers:
                            accepted_answers[user.id] = MapData()
                            accepted_answers[user.id].display_name = user.display_name
                        accepted_answers[user.id].count = accepted_answers[user.id].count + 1

        print "Top 10 users with the most accepted answers:"
        for i in xrange(10):
            max_key = None
            max_data = None

            for (key, data) in accepted_answers.iteritems():
                if max_data is None or data.count > max_data.count:
                    max_data = data
                    max_key = key

            del accepted_answers[max_key]

            print "%d\t%s" % (max_data.count, max_data.display_name)

        print

if __name__ == "__main__":
    sf = ServerFault()
    sf.run()
