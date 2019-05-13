package Person;
sub new {
    my $class = shift;
    my $self = {
        _firstName => shift,
        _lastName  => shift,
        _ssn       => shift,
    };

    bless $self, $class;
    return $self;
}

sub DESTROY {
    print "    Person::DESTROY called\n";
}


sub setFirstName {
    my ($self, $firstName) = @_;

    $self->{_firstName} = $firstName if defined($firstName);
    return $self->{_firstName};
}

sub getFirstName {
    my ($self) = @_;

    return $self->{_firstName};
}

sub setLastName {
    my ($self, $lastName) = @_;

    $self->{_lastName} = $lastName if defined($lastName);
    return $self->{_lastName};
}

sub getLastName {
    my ($self) = @_;

    return $self->{_lastName};
}

sub setSSN {
    my ($self, $ssn) = @_;

    $self->{_ssn} = $ssn if defined($ssn);
    return $self->{_ssn};
}

sub getSSN {
    my ($self) = @_;

    return $self->{_ssn};
}

sub show {
    my ($self) = @_;

    print "First Name:  $self->{_firstName}\n";
    print "Last Name :  $self->{_lastName}\n";
    print "SSN:         $self->{_ssn}\n";
}

# This is a default that gets called whenever you try to call an 
# undefined method or property.
sub croak {
    my ($msg) = @_;

    print "$msg\n";
    exit(1);
}

sub AUTOLOAD {
   my ($self) = @_;

   my $class_type = ref ($self) || croak "'$self' is not an object";
   my $sub = $AUTOLOAD;
   $sub =~ s/.*://;
   unless (exists $self->{$sub}) {
      croak "'$sub' does not exist in object/class '$class_type'";
   }

   if (@_) {
      return $self->($name) = shift;
   }
   else {
      return $self->($name);
   }
}

1;
