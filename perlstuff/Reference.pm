package Reference;
use Data::Dumper::Concise;
sub new {
    my $class = shift;
    my $self = {
        _name => shift
    };

    bless $self, $class;
    return $self;
}

sub DESTROY {
    print "    Reference::DESTROY called\n";
}


sub setName {
    my ($self, $name) = @_;

    $self->{_name} = $name if defined($name);
    return $self->{_name};
}

sub getName {
    my ($self) = @_;

    return $self->{_name};
}

sub show {
    my ($self) = @_;

    print "Name:  $self->{_name}\n";
}

sub scalar {
    my ($self) = @_;

    $str = $self->getName();

    $sref = \$str;
    $i_anon_ref = \25;
    $s_anon_ref = \"Molly";

    print "Scalar References:\n";
    print "\tNamed string reference:      '${$sref}', '$$sref' ($sref)\n";
    print "\tAnonymous string reference:  '${$s_anon_ref}', '$$s_anon_ref' ($s_anon_ref)\n";
    print "\tAnonymous int reference:     '${$i_anon_ref}', '$$i_anon_ref' ($i_anon_ref)\n"
}

sub pass_array {
    my $self = shift;
    my @arr_refs = @_;

    print("\tArray refs passed to subroutine:\n");
    my $i = 0;
    foreach $arr_ref (@arr_refs) {
        print "\t\tArray $i:\n";
        print Dumper($arr_ref);
        $i++;
    }
}

sub array {
    my ($self) = @_;

    @arr = ("Moe", "Larry", "Curly");

    $named_arr_ref = \@arr;
    $anon_arr_ref = ["Groucho", "Harpo", "Chico", "Zeppo"];
    @anon_arr_ref2 = \("Bud", "Lou");

    print "Array References:\n";
    print "\tNamed array reference:       '@{$named_arr_ref}', '@$named_arr_ref', '${$named_arr_ref}[0], $$named_arr_ref[1]' ($named_arr_ref)\n";
    print "\tAnonymous array reference:   '@{$anon_arr_ref}', '@$anon_arr_ref', '${$anon_arr_ref}[0], $$anon_arr_ref[1]' ($anon_arr_ref)\n";
    #print "\tAnonymous array reference 2: '@{@anon_arr_ref2}', '@@anon_arr_ref2', '${@anon_arr_ref2}[0], $@anon_arr_ref2[1]' (@anon_arr_ref2)\n";
    $self->pass_array($named_arr_ref, $anon_arr_ref);
}

sub pass_hash {
    my $self = shift;
    my @hash_refs = @_;

    print("\tHash refs passed to subroutine:\n");
    my $i = 0;
    foreach $hash_ref (@hash_refs) {
        print "\t\tHash $i:\n";
        print Dumper($hash_ref);
        $i++;
    }
}

sub hash_it {
    my ($self, $pass) = @_;

    %hash = ("Stooge A" => "Moe", "Stooge B" => "Larry", "Stooge C" => "Curly");

    $named_hash_ref = \%hash;
    $anon_hash_ref = {"Bro A" => "Groucho", "Bro B" => "Harpo", "Bro C" => "Chico", "Bro D" =>"Zeppo"};

    print "Hash References:\n";
    print "\tNamed hash reference keys:   '", keys %{$named_hash_ref}, "', '", keys %$named_hash_ref, "' ($named_hash_ref)\n", ;
    print "\tNamed hash reference values: '", values %{$named_hash_ref}, "', '", values %$named_hash_ref, "' ($named_hash_ref)\n", ;
    print "\tNamed hash, dumped:\n";
    print Dumper($named_hash_ref);
    print "\tAnonymous hash ref keys:     '", keys %{$anon_hash_ref}, "', '", keys %$anon_hash_ref, "' ($anon_hash_ref)\n";
    print "\tAnonymous hash ref values:   '", values %{$anon_hash_ref}, "', '", values %$anon_hash_ref, "' ($anon_hash_ref)\n";
    print "\tAnonymous hash, dumped:\n";
    print Dumper($anon_hash_ref);
    $self->pass_hash($named_hash_ref, $anon_hash_ref) if ($pass);
}

sub subroutine {
    my ($self) = @_;

    $named_sub_ref = \&hash_it;
    $anon_sub_ref = sub {print "Well $_[0], now look what you've gotten me into.\n";};

    print "Subroutine References:\n";
    print "\tNamed subroutine reference call 1:\n";
    &{$named_sub_ref}();
    print "\tNamed subroutine reference call 2:\n";
    &$named_sub_ref();
    print "\tAnonymous subroutine reference call 1:\n";
    &{$anon_sub_ref}("Stanley");
    print "\tAnonymous subroutine reference call 2:\n";
    &$anon_sub_ref("Bruce");
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
