package Employee;
use parent Person;
use strict;
#our @ISA = qw(Person);    # inherits from Person

# Override constructor
sub new {
    my ($class, $f, $l, $ssn, $id, $t) = @_;

    # Call the constructor of the parent class, Person.
    my $self = $class->SUPER::new( $f, $l, $ssn );

    # Add few more attributes
    $self->{_id}   = $id;
    $self->{_title} = $t;

    bless $self, $class;
    return $self;
}

sub DESTROY {
    my $self = shift;

    print "    Employee::DESTROY called\n";
    $self->SUPER::DESTROY();
}

# Override helper function
sub getFirstName {
    my($self) = @_;
    # This is child class function.
    print "This is child class helper function\n";
    return $self->{_firstName};
}

# Add more methods
sub setId {
    my ($self, $id) = @_;
    $self->{_id} = $id if defined($id);
    return $self->{_id};
}

sub getId {
    my($self) = @_;
    return $self->{_id};
}

sub setTitle {
    my ($self, $title) = @_;
    $self->{_title} = $title if defined($title);
    return $self->{_title};
}

sub getTitle {
    my($self) = @_;
    return $self->{_title};
}

sub show {
    my ($self) = @_;

    $self->SUPER::show();
    print "ID:          $self->{_id}\n";
    print "Title:       $self->{_title}\n";
}

1;
