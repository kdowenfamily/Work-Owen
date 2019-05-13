#!/usr/bin/perl

use Employee;
use Person;
use Reference;

$mohammed = new Employee("Mohammad", "Saleem", 23234345, "abcxyz", "Grand Poo Bah");
$larry = new Employee("Larry", "Fine", 8675309, "foofoo", "Master and Commander");
$my_ref = new Reference( "Hey Now");

# Get first name which is set using constructor.
$firstName = $mohammed->getFirstName();

print "Before Setting First Name is : $firstName\n";

# Now Set first name using helper function.
$mohammed->setFirstName( "Mohd." );

# Now get first name set by helper function.
$firstName = $mohammed->getFirstName();
print "Before Setting First Name is : $firstName\n";

print "Show the employee:\n";
$larry->show();

# casting
print "Show the employee, as a PERSON, dammit:\n";
bless ($larry, Person);
$larry->show();

print "Re-hire Larry:\n";
bless ($larry, Employee);
$larry->show();

if (0) {
    # Now call a bogus property and see if it errors correctly
    print "Let's be mean and call an undefined property:\n";
    $bar = $mohammed->_noSuchProperty;

    # Now call a bogus method and see if it errors correctly
    print "Let's be mean and call an undefined method:\n";
    $foo = $mohammed->noSuchSubroutine();
}

# references
print "\nNow show some references:\n";
$my_ref->show();
$my_ref->scalar();
$my_ref->array();
$my_ref->hash_it(1);
$my_ref->subroutine();

# end
print "\nDone.\n";
