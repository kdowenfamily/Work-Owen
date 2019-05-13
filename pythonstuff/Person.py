class Person(object):
    '''
    Base class for all employees.
    '''

    def __init__(self, first="", last="", ssn=None):
        self.__first = first
        self.__last = last
        self.__ssn = ssn

    @property
    def firstName(self):
        return self.__first

    @firstName.setter
    def firstName(self, first):
        self.__first = first

    @property
    def lastName(self):
        return self.__last

    @lastName.setter
    def lastName(self, last):
        self.__last = last

    @property
    def ssn(self):
        return self.__ssn

    @ssn.setter
    def ssn(self, ssn):
        self.__ssn = ssn


    def __str__(self):
        ret = "First Name:       " + str(self.__first) + "\n"
        ret += "Last Name:        " + str(self.__last) + "\n"
        ret += "Social Sec #:     " + str(self.__ssn) + "\n"

	return ret
