#! /usr/bin/perl -w

# set the version of this script
my $program = $0;
$program = `basename $program`;
chomp $program;
my $version = "v1.02";

## CHANGE QUEUE
# Add option to pass account+password on command line

## DESCRIPTION
# This script reads a CSV file containing a list of BIG-IPs and then
# performs Device and WAS discovery on each listed BIG-IP
# If a failure is encountered the script logs the error and continues
# discovery for the next BIG-IP on the list
#
# Uses the same CSV format as for Device bulk discover
# CSV file format:
# - with framework update: big_ip_adr,admin_user,admin_pw,true,root,root_pw
# - no framework update:   big_ip_adr,admin_user,admin_pw

use JSON; 	# a Perl library for parsing JSON - supports encode_json, decode_json, to_json, from_json
use Time::HiRes qw(gettimeofday);
#use strict;
#use warnings;

my $section_head = "##########################################################################";
my $table_head = "#---------------------------------------------------------------------";
my $overallStartTime = gettimeofday();

# log file
my $log = "bulkDiscovery.$$.log";
open (LOG, ">$log") || die "Unable to write the log file, '$log'\n";
&printAndLog(STDOUT, 1, "#\n# Program: $program  Version: $version\n");

# get input from the caller
use Getopt::Std;
my %usage = (
    "h" =>  "help",
    "c" =>  "Path to CSV file with all BIG-IP devices - REQUIRED",
    "q" =>  "BIG-IQ admin credentials in form admin:password - REQUIRED if not using default",
    "k" =>  "Keep the CSV file after this finishes (not recommended)",
    "v" =>  "Verbose screen output",
);
getopts('hc:q:vk');
if (defined $opt_h && $opt_h) {
    print "Discover multiple BIG-IP devices.\n";
    foreach my $opt (keys %usage) {
        print ("\t-$opt\t$usage{$opt}\n");
    }
    exit;
}

# See if we got the input we needed, bail with an error if we didn't
my $bailOut = 0;
if (!defined $opt_c) {
    &printAndLog(STDOUT, 1, "Please use -c to provide the path to the .csv file.\n");
    $bailOut = 1;
} elsif (!(-e $opt_c)) {
    &printAndLog(STDOUT, 1, "Could not find the .csv file, '$opt_c'.\n");
    &printAndLog(STDOUT, 1, "  Please use the -c option to provide a path to a valid .csv file.\n");
    $bailOut = 1;
}
if ($bailOut) {
    &gracefulExit(1);
}

# useful stuff for JSON
my $contType = "Content-Type: application/json";
my $bigiqCreds = "admin:admin";
if (defined $opt_q) {
	$bigiqCreds = $opt_q;
}

# ======================================================
# Import the .csv file and validate it.
# ======================================================
open (CSV, "$opt_c") || die "## ERROR: Unable to read the .csv file, '$opt_c'\n";
my @csvLns = <CSV>;
close CSV;
my $badln = "";
my $hasBadLn = 0;
my @bigips = ();
foreach my $ln (@csvLns) {
    chomp $ln;
    $ln =~ s/[\cM\cJ]+//g;    # some editors tack multiple such chars at the end of each line
    if ($ln =~ /^\s*([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),(.*)$/) {
        push (@bigips, "$1###$2###$3###$4###$5###$6");
    } elsif ($ln =~ /^\s*([^,]+),([^,]+),(.*)$/) {
        push (@bigips, "$1###$2###$3");
    } else {
        $badln = $ln;
        $hasBadLn = 1;
        last;
    }
}
if ($hasBadLn) {
    &printAndLog(STDERR, 1, "Bad line in '$opt_c':  '$badln'.\n");
    &printAndLog(STDERR, 1, "Required format for every line: '<ip-address>,<admin-username>,<admin-password>'\n");
    &printAndLog(STDERR, 1, "  <ip-address>,<admin-username>,<admin-password>\n");
    &printAndLog(STDERR, 1, "    or (if you want to update your framework, too)\n");
    &printAndLog(STDERR, 1, "  <ip-address>,<admin-username>,<admin-password>,true,root,<root-password>\n");
    &gracefulExit(1);
}

#======================================================
# Make sure the BIG-IQ API is available
# Check for available over timeout period (120 sec)
# Exit if not available during this period
#======================================================
my $timeout = 120;
my $perform_check4life = 1;
my $check4lifeStart = gettimeofday();

while($perform_check4life) {
	my $timestamp = getTimeStamp();
	my $check4life = "curl --connect-timeout 5 -s -u $bigiqCreds --insecure https://localhost/info/system";
	my $isAlive = &callCurl ($check4life, "verifying that the BIG-IQ is able to respond", $opt_v);
	
	# Check for API availability
	if ((defined $isAlive->{"available"}) && ($isAlive->{"available"} eq "true")) {
		&printAndLog(STDOUT, 1, "#\n# BIG-IQ UI is available:         $timestamp\n");
		$perform_check4life = 0;
	} else {
		&printAndLog(STDOUT, 1, "# BIG-IQ UI is not yet available: $timestamp\n");	
	}
	
	# Exit on timeout
	if ((gettimeofday() - $check4lifeStart) > $timeout) {
		&printAndLog(STDERR, 1, "## ERROR: The BIG-IQ UI is still not available.  Try again later...\n");
		&gracefulExit(1);
	}
	sleep 10;
}

#======================================================
# Perform Device discovery  
#======================================================
my %devError = ();
my $devStart = gettimeofday();
&printAndLog(STDOUT, 1, "#\n# $section_head\n");
&printAndLog(STDOUT, 1, "# DEVICE DISCOVERY\n");
my $timestamp = getTimeStamp();
&printAndLog(STDOUT, 1, "#\n# Start Device discovery:         $timestamp\n");
my $csvBase = `basename $opt_c`;
chomp $csvBase;
$tmpCsv = "/tmp/bulkImport.$csvBase";   
if ((defined $opt_k) && $opt_k) {
    # we want to keep the CSV file for testing
    # the device-import operation deletes this file, so make a copy
    `cp $opt_c $tmpCsv`;
} else {
    # move the file to a place where the bulk discovery can use it and delete it
    `mv $opt_c $tmpCsv`;
}


# Initialize Device status table
my %DeviceStatus;
$DeviceStatus{"all"}{"dev_previous"} = 0;
$DeviceStatus{"all"}{"dev_success"} = 0;
$DeviceStatus{"all"}{"dev_conflict"} = 0;
$DeviceStatus{"all"}{"dev_failure"} = 0;
$DeviceStatus{"all"}{"dev_n/a"} = 0;
$DeviceStatus{"all"}{"WAS_previous"} = 0;
$DeviceStatus{"all"}{"WAS_success"} = 0;
$DeviceStatus{"all"}{"WAS_conflict"} = 0;
$DeviceStatus{"all"}{"WAS_failure"} = 0;
$DeviceStatus{"all"}{"WAS_n/a"} = 0;

my $bulkDevDiscover = "curl -s -k -u $bigiqCreds -H \"$contType\" -X POST -d \'{\"groupReference\": {\"link\" : \"https://localhost/mgmt/shared/resolver/device-groups/cm-autodeploy-group-manager-autodeployment\"}, \"filePath\" : \"$tmpCsv\"}\' http://localhost:8100/mgmt/shared/device-discovery";
my $deviceDiscovery = &callCurl ($bulkDevDiscover, "discovering all BIG-IP devices from the Device module", $opt_v);
my $devLink = $deviceDiscovery->{"selfLink"};
my $deviceStat = &pollTask($bigiqCreds, $devLink, $opt_v);
if (defined $deviceStat->{"deviceStatesMap"}) {
    my $devBigIpMap = $deviceStat->{"deviceStatesMap"};
    foreach my $hash (@bigips) {
        my ($mip, $user, $pw, $fwUpg, $ruser, $rpwd) = split(/###/, $hash);
        my $status = $devBigIpMap->{$mip}->{"status"};
        if ($status eq "SKIPPED") {
			$DeviceStatus{$mip}{"device_discovery_status"} = "Previously discovered";
			$DeviceStatus{"all"}{"dev_previous"}++;
        } elsif ($status eq "FAILED") {
            $devError{$mip} = $devBigIpMap->{$mip}->{"error"};
			$DeviceStatus{$mip}{"device_discovery_status"} = "Failed discovery"; 			
			$DeviceStatus{"all"}{"dev_failure"}++;
		} else {
			$DeviceStatus{$mip}{"device_discovery_status"} = "Successful discovery";
			$DeviceStatus{"all"}{"dev_success"}++;			
        }
    }
}

# Print results for device discovery
foreach(@bigips) {
    my ($mip, $user, $pw, $fwUpg, $ruser, $rpwd) = split(/###/, $_);
	$string = sprintf "# %-15s   %-25s",$mip,$DeviceStatus{$mip}{"device_discovery_status"};
	&printAndLog(STDOUT, 1, "$string\n");
}

my $devEnd = gettimeofday();
my $et = sprintf("%-5.2f",$devEnd-$devStart);
$timestamp = getTimeStamp();
&printAndLog(STDOUT, 1, "# End device discovery:           $timestamp\n");
&printAndLog(STDOUT, 1, "#\n# Device discovery elapsed time:  $et seconds\n#\n");


#======================================================
# Find all the BIG-IPs that have already been discovered
# through Web Application Security.
#======================================================

&printAndLog(STDOUT, 1, "#\n# $section_head\n");
&printAndLog(STDOUT, 1, "# WEB APPLICATION SECURITY (WAS) DISCOVERY\n");
$timestamp = getTimeStamp();
my $wasStart = gettimeofday();
&printAndLog(STDOUT, 1, "#\n# Start WAS discovery:            $timestamp\n");

my @asmConflicts = my @asmExisting = my @asmFailed = my @asmSucceeded = my %hostname = my %asmError = my %asmStart = my %asmEnd = my %asmStartTS = my %asmEndTS = ();
my $devs = &callCurl ("curl -s -k -u $bigiqCreds -X GET http://localhost:8100/mgmt/shared/resolver/device-groups/cm-asm-allAsmDevices/devices", "Finding all ASM devices", $opt_v);
if (defined $devs->{"items"}) {
    my @allBigips =  @{$devs->{"items"}};
    foreach my $bigip (@allBigips) {
        push (@asmExisting, $bigip->{"address"});
        $hostname{$bigip->{"address"}} = $bigip->{"hostname"};
    }
}


#======================================================
# Go through the .csv file, attempt to discover each
# BIG-IP, and record the results.
#======================================================
my $ctbp = 1;
foreach my $bpString (@bigips) {
	my $wasStart = gettimeofday();

    # break down the parts of the line
    my ($bp, $uname, $pw, $fwUpg, $ruser, $rpwd) = split(/###/, $bpString);
    my $creds = "$uname:$pw";

	# WAS DISCOVERY CASE: Previously discovered
    if (defined $hostname{$bp}) {
		$DeviceStatus{$bp}{"WAS_discovery_status"} = "Previously discovered";
		$DeviceStatus{"all"}{"WAS_previous"}++;
		my $timestamp = getTimeStamp();
		my $et = gettimeofday() - $wasStart;		
		my $string = sprintf("# %-15s  %-21s  %s  %6.2f sec",$bp,$DeviceStatus{$bp}{"WAS_discovery_status"},$timestamp,$et);
		&printAndLog(STDOUT, 1, "$string\n");
        next;

	# WAS DISCOVERY CASE: Skipped discovery
	} elsif ($DeviceStatus{$bp}{"device_discovery_status"} eq "Failed discovery") {
		$DeviceStatus{$bp}{"WAS_discovery_status"} = "Skipped discovery";
		$DeviceStatus{"all"}{"WAS_n/a"}++;
		my $timestamp = getTimeStamp();
		my $et = gettimeofday() - $wasStart;	
		my $string = sprintf("# %-15s  %-21s  %s  %6.2f sec",$bp,$DeviceStatus{$bp}{"WAS_discovery_status"},$timestamp,$et);
		&printAndLog(STDOUT, 1, "$string\n");		
		next;
	}

    # TRY WAS DISCOVERY
    my $bpname = "DMABIG-IP$ctbp";
    $ctbp++;
    my $asmDiscover = "curl -s -k -u $bigiqCreds -H \"$contType\" -X POST -d \'{\"name\":\"$bpname\", \"deviceIp\": \"$bp\", \"createChildTasks\" : true, \"deviceUsername\": \"$uname\", \"devicePassword\": \"$pw\"}\' http://localhost:8100/mgmt/cm/asm/tasks/declare-mgmt-authority";
    my $dmaRes = &callCurl ($asmDiscover, "discovering $bpname for Web Application Security", $opt_v);
    my $dmaLink = $dmaRes->{"selfLink"};

    # poll the discovery-task URIs until they reach a conclusion
    my $dmastatus = &pollTask($bigiqCreds, $dmaLink, $opt_v);
	
	# DISCOVERY CONFLICT CASE: Remove device from WAS
    if ($dmastatus->{"currentStep"} =~ /PENDING_/) {
        # conflict(s)!
        &printAndLog(STDOUT, $opt_v, "'$bp' has conflicts.\n");

        # find the different configs and put the diffs in the log
        my @conflicts = @{$dmastatus->{"conflicts"}};
        my @conflictStrs = ();
        foreach my $conflict (@conflicts) {
            # show the versions that are different for this conflict
            my $fromRef = $conflict->{"fromReference"}{"link"};
            my $from = &callCurl("curl -s -k -u $bigiqCreds -X GET $fromRef", "show the 'from' (BIG-IQ working config)", $opt_v);
            my $toRef = $conflict->{"toReference"}{"link"};
            my $to = &callCurl("curl -s -k -u $bigiqCreds -X GET $toRef", "show the 'to' (BIG-IP discovered config)", $opt_v);
        }

        # delete the task
        my $deleteIt = "curl -s -k -u $bigiqCreds -H \"$contType\" -X DELETE $dmaLink";
        &callCurl ($deleteIt, "due to conflict, canceling $bpname discovery for Web Application Security", $opt_v);

        # RMA the device
        my $device = $dmastatus->{"deviceReference"}->{"link"};
        my $rmaIt = "curl -s -k -u $bigiqCreds -H \"$contType\" -X POST -d \'{\"name\" : \"RMA$bpname\", \"createChildTasks\" : true, \"deviceReference\" : {\"link\" : \"$device\"} }\' http://localhost:8100/mgmt/cm/asm/tasks/remove-mgmt-authority";
        my $rmaRes = &callCurl ($rmaIt, "Removing $bpname from Web Application Security due to conflict", $opt_v);
        my $rmaLink = $rmaRes->{"selfLink"};
        &pollTask($bigiqCreds, $rmaLink, $opt_v);

        # add this BIG-IP to the list of failures due to conflict
		$DeviceStatus{$bp}{"WAS_discovery_status"} = "Conflicted discovery";		
		$DeviceStatus{"all"}{"WAS_conflict"}++;
		
		my $timestamp = getTimeStamp();
		my $et = gettimeofday() - $wasStart;	
		my $string = sprintf("# %-15s  %-21s  %s  %6.2f sec",$bp,$DeviceStatus{$bp}{"WAS_discovery_status"},$timestamp,$et);		
		&printAndLog(STDOUT, 1, "$string\n");		

	# DISCOVERY FAILURE CASE: 	
    } elsif ($dmastatus->{"status"} =~ /^(CANCELED|FAILED|COMPLETED_WITH_ERRORS)/) {
		$DeviceStatus{$bp}{"WAS_discovery_status"} = "Failed discovery";
		$DeviceStatus{"all"}{"WAS_failure"}++;
        if (defined $dmastatus->{"errorMessage"}) {
            $DeviceStatus{$bp}{"WAS_discovery_error"} = $dmastatus->{"errorMessage"};
        }
		my $timestamp = getTimeStamp();
		my $et = gettimeofday() - $wasStart;	
		my $string = sprintf("# %-15s  %-21s  %s  %6.2f sec",$bp,$DeviceStatus{$bp}{"WAS_discovery_status"},$timestamp,$et);		
		&printAndLog(STDOUT, 1, "$string\n");
		
	# DISCOVERY SUCCESS CASE: 		
    } else {
		$DeviceStatus{$bp}{"WAS_discovery_status"} = "Successful discovery";
		$DeviceStatus{"all"}{"WAS_success"}++;		
        push(@asmSucceeded, $bp);
		
		my $timestamp = getTimeStamp();
		my $et = gettimeofday() - $wasStart;
		my $string = sprintf("# %-15s  %-21s  %s  %6.2f sec",$bp,$DeviceStatus{$bp}{"WAS_discovery_status"},$timestamp,$et);
		&printAndLog(STDOUT, 1, "$string\n");		
    }
}
my $wasEnd = gettimeofday();
$et = sprintf("%-5.2f",$wasEnd-$wasStart);
$timestamp = getTimeStamp();
&printAndLog(STDOUT, 1, "# End WAS discovery:              $timestamp\n");
&printAndLog(STDOUT, 1, "#\n# WAS discovery elapsed time:     $et seconds\n#\n");

&printAndLog(STDOUT, 1, "#\n# $section_head\n");
&printAndLog(STDOUT, 1, "# BULK DISCOVERY FINAL RESULTS\n#\n");
$string = sprintf "# %-15s   %-25s   %-25s",
		"IP Address",
		"Device Discovery",
		"WAS Discovery";
&printAndLog(STDOUT, 1, "$string\n");
&printAndLog(STDOUT, 1, "$table_head\n");		

foreach(@bigips) {
    my ($mip, $user, $pw, $fwUpg, $ruser, $rpwd) = split(/###/, $_);
	$string = sprintf "# %-15s   %-25s   %-25s",
		$mip,
		$DeviceStatus{$mip}{"device_discovery_status"},
		$DeviceStatus{$mip}{"WAS_discovery_status"};
	&printAndLog(STDOUT, 1, "$string\n");
}

$string = sprintf "#\n# %-15s  %8s  %8s  %8s  %8s  %8s",
		"Discover_Type",
		"Previous",
		"Success",
		"Conflict",
		"Failed",
		"Skipped";
&printAndLog(STDOUT, 1, "$string\n");		
&printAndLog(STDOUT, 1, "$table_head\n");		

$string = sprintf "# %-15s  %8s  %8s  %8s  %8s  %8s",
	"Device",
	$DeviceStatus{"all"}{"dev_previous"},
	$DeviceStatus{"all"}{"dev_success"},
	$DeviceStatus{"all"}{"dev_conflict"},
	$DeviceStatus{"all"}{"dev_failure"},
	$DeviceStatus{"all"}{"dev_n/a"};	
&printAndLog(STDOUT, 1, "$string\n");

$string = sprintf "# %-15s  %8s  %8s  %8s  %8s  %8s",
	"WAS",
	$DeviceStatus{"all"}{"WAS_previous"},
	$DeviceStatus{"all"}{"WAS_success"},
	$DeviceStatus{"all"}{"WAS_conflict"},
	$DeviceStatus{"all"}{"WAS_failure"},
	$DeviceStatus{"all"}{"WAS_n/a"};
&printAndLog(STDOUT, 1, "$string\n");	
	
my $overallEndTime = gettimeofday();
$et = sprintf("%5.2f",$overallEndTime-$overallStartTime);
&printAndLog(STDOUT, 1, "#\n# Overall elapsed time: $et seconds\n#\n");

#======================================================
# Finish up
#======================================================
&gracefulExit(0);


#======================================================
# A subroutine for making curl calls, pretty-printing the return for the caller, 
# and returning a pointer to the JSON.
#======================================================
sub callCurl {
    my ($call, $message, $printToo) = @_;

    &printAndLog(STDOUT, $printToo, "\n\n$message\n");
    &printAndLog(STDOUT, $printToo, "$call\n");
    my @json = `$call |json-format 2>&1`;
    my @showRet = ();
    foreach my $retln (@json) {
        next if ($retln =~ /^\s*OpenJDK/);     # error from json-format
        push (@showRet, $retln);
    }
    &printAndLog(STDOUT, $printToo, @showRet);

    my $json = join("", @showRet);
    my $jsonHash = &decode_json($json);

    return $jsonHash;
}


#======================================================
# A subroutine for polling a task until it reaches a conclusion.
# $creds are the admin credentials for the curl call
# $taskLink is the URI to the POSTed task
#======================================================
sub pollTask {
    my ($creds, $taskLink, $printToo) = @_;

    # keep asking for status and checking the answer until the answer is conclusive
    &printAndLog(STDOUT, $printToo, "Polling for completion of '$taskLink'\n");
    my ($taskjpath, $taskdpath, $result, $ct, $taskanswer) = ("", "", "", 1, "");
    my $ctCurly = 0;
    do {
        sleep 5;
        ($taskanswer) = &callCurl("curl -s -k -u $creds -X GET $taskLink", "Attempt $ct", $printToo);
        if ($taskanswer->{"status"} =~ /^(FINISHED|CANCELED|FAILED|COMPLETED(_WITH_ERRORS)?)/) {
            $result = $taskanswer->{"status"};
        }
        $ct++;
    } while ($result eq "");
    &printAndLog(STDOUT, $printToo, "Finished - '$taskLink' got a result of '$result'.\n");

    # return the JSON pointer
    return $taskanswer;
}


#======================================================
# A subroutine for both printing to whatever file is given
# and printing the same thing to a log file.
# This script does a lot, so it may be useful to keep a log.
#======================================================
sub printAndLog {
    my ($FILE, $printToo, @message) = @_;
    my $message = join("", @message);
    print $FILE $message if ($printToo);
    print LOG $message;
}


#======================================================
# Print the log file and then exit, so the user knows which log
# file to examine.
#======================================================
sub gracefulExit {
    my ($status) = @_;
	&printAndLog(STDOUT, 1, "# Discovery log file: $log\n");	
    close LOG;
    exit($status);
}


#======================================================
# Pretty-print the time.
#======================================================
sub getTimeStamp {
    my ($Second, $Minute, $Hour, $Day, $Month, $Year, $WeekDay, $DayOfYear, $IsDST) = localtime(time); 
    my $time_string = sprintf ("%02d/%02d/%02d %02d:%02d:%02d",$Month+1,$Day,$Year+1900,$Hour,$Minute,$Second);
    return ($time_string);
}
