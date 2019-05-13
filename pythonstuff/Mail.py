#!/usr/bin/python

from business.Employee import Employee
from business.Person import Person

mohammed = Employee("Mohammad", "Saleem", 23234345, "abcxyz", "Grand Poo Bah")
larry = Employee("Larry", "Fine", 8675309, "foofoo", "Master and Commander")

# Get first name which is set using constructor.
print "Before Setting, First Name is: " + mohammed.firstName

# Now Set first name using helper function.
mohammed.firstName = "Mohd."

# Now get first name set by helper function.
print "After Setting, First Name is: " + mohammed.firstName

print "Show the employee:";
print larry

# casting - no such thing?
print "Show the employee as a PERSON, dammit:"
just_larry = Person(larry.firstName, larry.lastName, larry.ssn)
print just_larry

print "Put Larry back in his suit:"
print larry
