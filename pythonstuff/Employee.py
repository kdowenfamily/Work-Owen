from Person import Person

class Employee(Person):
    '''
    Class for one employee.
    '''

    def __init__(self, first="", last="", ssn=None, id=None, title=""):
        super(Employee, self).__init__(first, last, ssn)

        self.__id = id
        self.__title = title

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, title):
        self.__title= title


    def __str__(self):
        ret = super(Employee, self).__str__()
        ret += "ID:       	  " + str(self.id) + "\n"
        ret += "Title:            " + self.title + "\n"

	return ret
