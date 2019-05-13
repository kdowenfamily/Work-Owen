#!/usr/bin/python
import re, logging

logging.basicConfig(filename="srvrFault.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

USERS = "users.xml"
POSTS = "posts.xml"

class XmlObj(object):
    """
    Represents any object that comes from an XML record.
    """

    # pattern for finding one attribute and value in a <row> element
    attr = re.compile(r'\s*(\S+)\s*=\s*"([^"]+)"')

    def _is_valid(self, line):
        if (
            re.search(r'^\s*<row\s+\S', line) and
            re.search(r'\/>\s*$', line)
           ):
            return True
        else:
            logging.warning("Bad formatting:  '%s'", line.strip())
            return False

    def parseline(self, line):
        my_dict = {}

        if not self._is_valid(line):
            return my_dict

        line = re.sub(r'^\s*<row\s*', r'', line)
        line = re.sub(r'\s*\/>\s*$', r'', line)
        for (key, val) in re.findall(XmlObj.attr, line):
            my_dict[key] = val

        return my_dict

class User(XmlObj):
    """Represents a single <user> element"""

    def __init__(self, line=""):
        self.id = None
        self.display_name = None

        self._parse(line)
        self.answer_ids = []
        self.good_answers = 0

    def _parse(self, line):
        user_dict = self.parseline(line)

        self.id = user_dict.get("Id")
        self.display_name = user_dict.get("DisplayName")

    def __str__(self):
        return "{0}\t{1}".format(str(len(self.answer_ids)), self.display_name)

    def good_answer_str(self):
        return "{0}\t{1}".format(str(self.good_answers), self.display_name)

class Post(XmlObj):
    """Represents a single <post> element"""

    def __init__(self, line=""):
        self.id = None
        self.post_type_id = None
        self.owner_user_id = None
        self.accepted_answer_id = None
        self._parse(line)

    def _parse(self, line):
        post_dict = self.parseline(line)

        self.id = post_dict.get("Id")
        self.post_type_id = post_dict.get("PostTypeId")
        self.owner_user_id = post_dict.get("OwnerUserId")
        self.accepted_answer_id = post_dict.get("AcceptedAnswerId")

        if not self.post_type_id:
            return

        # if this is an answer, give the user credit now
        if (int(self.post_type_id) == 2) and (self.owner_user_id in ServerFault.users):
            user = ServerFault.users[self.owner_user_id]
            if user:
                user.answer_ids.append(self.id)

        # if this is a question with an accepted answer, bump up the count for that answer
        if (int(self.post_type_id) == 1) and (self.accepted_answer_id):
            if self.accepted_answer_id in ServerFault.good_answers:
                ServerFault.good_answers[self.accepted_answer_id] += 1
            else:
                ServerFault.good_answers[self.accepted_answer_id] = 1

class ServerFault(object):
    users = {}
    good_answers = {}

    def read_users(self, filename):
        logging.info("Parsing '%s'", filename)
        with open(filename, 'r') as inputf:
            for line in inputf:
                user = User(line)
                if user.id:
                    ServerFault.users[user.id] = user
        logging.info("Done parsing '%s'. %s users total.", filename,
                     str(len(ServerFault.users.values())))

    def read_posts(self, filename):
        logging.info("Parsing '%s'", filename)
        ct = 0
        with open(filename, 'r') as inputf:
            for line in inputf:
                ct += 1
                if (ct % 5000000 == 0): # around 10 min
                    logging.info("On post %s.", ct)
                Post(line) # no point in keeping this; just create
        logging.info("Done parsing '%s'. %s posts total.", filename, str(ct))

    def calc_user_awesomeness(self):
        logging.info("Calculating good answers for all users.")
        for user in ServerFault.users.values():
            for post_id in user.answer_ids:
                user.good_answers += ServerFault.good_answers.get(post_id, 0)
        logging.info("Done calculating.")

    def run(self):
        self.read_users(USERS)
        self.read_posts(POSTS)
        self.calc_user_awesomeness()
        users = ServerFault.users.values()

        print "Top 10 users with the most answers:"
        sorted_users = sorted(users, key=lambda user: len(user.answer_ids), reverse=True)
        for usr in sorted_users[:10]:
            print usr

        print

        print "Top 10 users with the most accepted answers:"
        sorted_users = sorted(users, key=lambda user: user.good_answers, reverse=True)
        for usr in sorted_users[:10]:
            print usr.good_answer_str()

        print

if __name__ == "__main__":
    sf = ServerFault()
    sf.run()
