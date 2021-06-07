#!/usr/bin/env python3 
# 
# Node/javascript mavlink test maker!
#
# This is written to run with python3 only, and the tests it produces are for node / javascript
# It is mavlink1 and mavlink2 and multi-type aware
#
# Copyright David 'Buzz' Bussenschutt July 2020
# Released under GNU GPL version 3 or later
#
#  to run:  cd test
#            python3 make_tests.py > made_tests.js
#            cd - 
#           mocha test --grep 'from C'
#
# reads the output from modified C test commands, for example, for ardupilot + mavlink2:
# "./testmav2.0_ardupilotmega | grep '^fd' command and builds a bunch of .js tests for this test data
#
# In order to identify types that are 'Long' or need Array wrapping, which need special handling we build a little lookup table 
# from the autogenerated file:mavlink.tests.js" (which itself is made by mavgen_javascript.py )
#
# we label and number each of the tests in the output as well, so that its also easy to run individual tests with something like:
# mocha test --grep '1234'
# or we can run all of them with:
# mocha test --grep 'from C'
# or eg all the ardupilotmega tests against mavlink1:
# mocha test --grep 'using ardupilotmega/1.0'

import subprocess
import sys

# now tested and executes with this simple matrix of two mavtypes and two mav versions
cmddir = '../../../generator/C/test/posix/'
mavtypes = ['ardupilotmega','common']
versions = ['1.0','2.0']#['2.0']
cmds = []

#..so the C binding cmds executed/wrapped are: 'testmav1.0_ardupilotmega', 'testmav2.0_ardupilotmega', 'testmav1.0_common', 'testmav2.0_common'

#---------------------------------------------------------------------------------------


template1 = '''
  it('id${ID} encode and decode ${NAME} from C using ${MAVTYPE}/${VERSION} ${SIGNED}', function() {
        
        this.mav.seq = ${SEQ};
        this.mav.srcSystem=${SRCSYS};
        this.mav.srcComponent=${SRCCOMP};
'''

signing_extra_template = '''

        //-------- START codeblock only for signed packets----------------

        this.mav.seq = ${SEQ}-1;

        // relevant to how we pass-in the Long object/s to jspack, we'll assume the calling user is smart enough to know that. 
        var wrap_long = function (someLong) { 
            return [someLong.getLowBitsUnsigned(), someLong.getHighBitsUnsigned()]; 
        } 

        this.mav.signing.secret_key = Uint8Array.from([ 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42 ]) ; // matches secret key in testmav.c
        this.mav.signing.link_id = 0 ;    // 1 byte // matches link_id in testmav.c
        this.mav.signing.timestamp = ${TS}n;  // at most 48 bits , using a BigInt  - matches timestamp in testmav.c
        this.mav.signing.sign_outgoing = true; // todo false this

        var epoch_offset = 1420070400; 
        var long_timestamp = ${TS}n; 

        var target_system = 255;  // the python impl in mavproxy uses 255 here , so we do, it could be this.sysid 
        var target_component = 0; 
        var secret_key = this.mav.signing.secret_key ; 

        this.mav.send = function(mavmsg) {
            buf = mavmsg.pack(this); 
            // no actual send here
            this.seq = (this.seq + 1) % 256; 
            this.total_packets_sent +=1; 
            this.total_bytes_sent += buf.length; 
        } 

        var link_id =0; 
        var srcSystem=this.mav.srcSystem; 
        var srcComponent=this.mav.srcComponent; 
        stream_key = new Array(link_id,srcSystem,srcComponent).toString(); 
        this.mav.signing.stream_timestamps[stream_key] = ${TS}; 
        this.mav.signing.timestamp.should.eql(${TS}n); //ts before setup

        var setup_signing = new this.mavlink.messages.SETUP_SIGNING(target_system, target_component, secret_key, long_timestamp); 
        this.mav.send(setup_signing,this.sysid); 

        setup_signing.secret_key.should.eql(Uint8Array.from([ 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42 ]) ); 
        setup_signing.initial_timestamp.should.eql(${TS}n); 
        //this.mav.signing.timestamp.should.eql(new Buffer.from([0,0,0,0,0,${TS}])); 
        this.mav.signing.timestamp.should.eql(${TS}n+1n); // ts after setup 
        this.mav.signing.link_id.should.eql(0); 
        this.mav.signing.sign_outgoing.should.eql(true);

        //-------- END codeblock only for signed packets----------------
'''

template2 = '''

        var test_${NAME} = this.tests.test_${NAME}()[0]; // get the assembled test object with test data already set, override just the min we need to do this test

//---  you can uncomment any of these to change the test, but you'll need to change the reference buffer to the right result too       
//${FIELDS}
//--- 

        // Create a buffer that matches what the Python version of MAVLink creates
        var reference = Uint8Array.from([${BUFFER}]);

        this.mav.signing.timestamp = ${TS}n;// force ts to be correct, right before the pack() that matters

        var p = test_${NAME}.pack(this.mav);

 //       console.log(p); 
 //       p.forEach( x => {  process.stdout.write( x.toString() ); process.stdout.write(" ") } ); process.stdout.write("\\n"); 
 //       p.forEach( x => {  process.stdout.write( x.toString(16) ); process.stdout.write(" ") } ); process.stdout.write("\\n"); 

        test_${NAME}._header.seq.should.eql(${SEQ}); 
        test_${NAME}._header.srcSystem.should.eql(${SRCSYS}); 
        test_${NAME}._header.srcComponent.should.eql(${SRCCOMP}); 
        test_${NAME}._header.msgId.should.eql(test_${NAME}._id); 

        ${SIGNED}test_${NAME}._header.incompat_flags.should.eql(1); 
        ${UNSIGNED}test_${NAME}._header.incompat_flags.should.eql(0); 
        
        test_${NAME}._header.compat_flags.should.eql(0); 

        Uint8Array.from(p).should.eql(reference);
    });
'''

templatestart = '''
//
// (auto-generated by make_tests.py ), do not edit.
// generator by davidbuzz@gmail.com
//
// Copyright David 'Buzz' Bussenschutt July 2020
// Released under GNU GPL version 3 or later
//
// you can regenerate this file and its dependancies and run its tests, by executing the following:  "cd pymavlink/generator/javascript ; npm test"
// or see make_tests.py which created this.
//
should = require('should');

'''

templateheader = '''
//--------------------------------------------------------------------------------------------------------------------------------------------------------

describe('end-to-end node byte-level tests of ${MAVTYPE}/${VERSION} against C impl', function() {

    beforeEach(function() {
        return new Promise((beforePromiseResolve) => {
            let modulePromise = import('../implementations/mavlink_${MAVTYPE}_v${VERSION}/mavlink.js');// hardcoded here by make_tests.py generator
            let testsPromise = import('../implementations/mavlink_${MAVTYPE}_v${VERSION}/mavlink.tests.js');//// hardcoded here by make_tests.py generator
            Promise.all([modulePromise,testsPromise]).then( (values) => {
                this.mavlink = values[0];
                this.mav = new this.mavlink.MAVLink(null,42,150);
                this.tests = values[1];

                // be sure the test library is using the right version before we call into it
                this.tests.set_mav(this.mav);

                beforePromiseResolve();
                });
            });
    });'''

templatefooter = '''

});'''

#------------------------------------------------

def is_packet_and_field_in_long_list(pname,fname):
    global llines
    for l in llines:
        if ( pname+'.'+fname in l ) : 
            return (True, l)
    return (False, '')

testid = 1;

# for each of the 1.0,2.0 and common,ardupilotmega combos write tests
def do_make_output(mt,v,lines):
  global testid
  t = templateheader.replace('${MAVTYPE}',mt)
  t =              t.replace('${VERSION}',v)
  t =              t.replace('${VERS}',v.replace('.',''))
  print(t)

  last_line = ''
  for line in lines:
    if line.startswith('fd '): # mavlink2 start byte as human-readable hex, eg 'fd 08 7e 2a 0b e2 00 00 88 41 00 00 34 42 30 93 '
        last_line = '2.0'
        if v == 1: # if param 'v' requested mav1 data and we see mav2 data, ignore it
            continue
        hexdata = line.strip().replace(' ',', 0x')
        hexdata = '0x'+hexdata
        # ckeck if signing bit is set on this packet: 0xfd, 0x09, 0x01 <-- that 1
        signchar = hexdata[15]
        signint = int(signchar,16)
        signbit = signint % 2; # lowest bit to true/false

    if line.startswith('fe '): # mavlink1 start byte as human-readable hex, eg 'fe 08 7e 2a 0b e2 00 00 88 41 00 00 34 42 30 93 '
        last_line = '1.0'
        if v == 2: # if param 'v' requested mav2 data and we see mav1 data, ignore it
            continue
        hexdata = line.strip().replace(' ',', 0x')
        hexdata = '0x'+hexdata
        signbit = False

    if line.startswith('sysid:'): # packet details human-readable eg 'sysid:42 compid:11 seq:126 RPM { rpm1: 17.000000  rpm2: 45.000000  }'
        # skip parsing data if its not this parser
        if last_line != v:
            continue
        fields = line.split(' ') 
        sysid = fields[0].split(':')[1]
        compid = fields[1].split(':')[1]
        seq = fields[2].split(':')[1]

        # lines without sign_ts, the { is earlier
        if fields[4] == '{':
            sign_ts = '0'
            packetname = fields[3]
            more = fields[4:]
        else:
            sign_ts = fields[3].split(':')[1]
            packetname = fields[4]
            more = fields[5:]

        packetname = packetname.lower()

        arraystarted = False
        for i,x in enumerate(more):
            
            if x == '[':
                arraystarted = True
            if x == ']':
                arraystarted = False
                more[i] = '], \n            '
            if not arraystarted and x == '':
                more[i] = ',\n            '
        fixed = ''.join(more)
        fixed = fixed.replace(',]',']') # drop unneeded comma from end of arrays
        fixed = fixed.replace('{','');
        fixed = fixed.replace('}','');
        fixed = fixed.replace(':','=')   # move : to =
        import re
        fixed = re.sub(r'(\'.*?\')', '\\1,\n            ', fixed)

        # now iterate over them as parsed lines safely
        newlines = []
        for fieldline in fixed.split('\n'):
            if fieldline.strip() == '':
                continue
            # a little miniparser here to modify things after the = sign to insert our own test values, not the included ones, but leave
            # value wrapping and other surrounding casting functions as-is.
            ( field, value) = fieldline.split('='); 
            if not value.startswith('['):
                value = value.replace(',','')
                field = field.replace(' ','')
            else: # array
                value = value.split('[')[1].split(']')[0]; # stuff inside the brackets, but not the brackets
            (retval,match) = is_packet_and_field_in_long_list(packetname,field);
            if retval == True:                
                parts = match.split('=');
                after_equals = parts[1];
                before_semicolon = after_equals.split(';')[0]

                # determine old test value in the 'before_semicolon' line segment:
                # a little miniparser here to modify things after the = sign to insert our own test values, not the included ones, but leave
                # value wrapping and other surrounding casting functions as-is.
                if not before_semicolon.replace(' ','').startswith('['):
                    if '"' in before_semicolon:
                        oldvalue = before_semicolon.split('"')[1]; # stuff inside the ", but not the " 
                    elif 'Array' in before_semicolon:
                        oldvalue = before_semicolon.split('[')[1].split(']')[0]; # [1234]
                    else:   
                        oldvalue = before_semicolon; # unwrapped numbers etc
                else: # array
                    oldvalue = before_semicolon.split('[')[1].split(']')[0]; # stuff inside the brackets, but not the brackets                

                line_minus_data = before_semicolon.replace(oldvalue,value);
                newlines.append("      test_"+packetname+"."+field+'='+line_minus_data+';')
            else:
                newlines.append("      test_"+packetname+"."+field+'='+value+';')


        fixed = '\n//'.join(newlines)

        t = template1
        t = t.replace('${MAVTYPE}',mt)
        t = t.replace('${VERSION}',v)
        t = t.replace('${NAME}',packetname)
        t = t.replace('${ID}',str(testid))
        testid = testid+1
        t = t.replace('${SEQ}',seq)
        t = t.replace('${SRCSYS}',sysid)
        t = t.replace('${SRCCOMP}',compid)
        t = t.replace('${BUFFER}',hexdata)
        if signbit:
            t = t.replace('${SIGNED}','signed')
        else :
            t = t.replace('${SIGNED}','')
        print(t)

        if signbit:
            t = signing_extra_template
            t = t.replace('${SEQ}',seq)
            t = t.replace('${TS}',sign_ts)
            print(t)

        t = template2
        t = t.replace('${NAME}',packetname)
        t = t.replace('${SEQ}',seq)
        t = t.replace('${SRCSYS}',sysid)
        t = t.replace('${SRCCOMP}',compid)
        t = t.replace('${BUFFER}',hexdata)
        t = t.replace('${FIELDS}',fixed) 
        t = t.replace('${TS}',sign_ts)
        if signbit:
            t = t.replace('${SIGNED}','/*signed*/ ')
            t = t.replace('${UNSIGNED}','//unsigned ')
        else :
            t = t.replace('${SIGNED}','//signed ')
            t = t.replace('${UNSIGNED}','/*unsigned*/ ')
        print(t)

        print('//------------------------------------------------------')

  # append footer
  t = templatefooter.replace('${MAVTYPE}',mt)
  t =              t.replace('${VERSION}',v)
  t =              t.replace('${VERS}',v.replace('.',''))
  print(t)


#---------------------------------------------------------------------------------------

# example line from file:
#       test_actuator_output_status.time_usec =  Long.fromNumber(93372036854775807, true); // fieldtype: uint64_t  isarray: False 
llines = []
def make_long_lookup_table(mt,v):
    global llines
    _cmd = 'egrep "(wrap_long|new.*Array)" ../implementations/mavlink_'+mt+'_v'+v+'/mavlink.tests.js'; # relevant lines only
    _result = subprocess.run(_cmd, stdout=subprocess.PIPE, shell=True)
    _data = _result.stdout.decode('utf-8')
    llines = _data.split("\n")
    #return lines

#---------------------------------------------------------------------------------------

print(templatestart)

for mt in mavtypes:
    for v in versions:
        cmd = cmddir+'testmav'+v+'_'+mt
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = result.stdout.decode('utf-8')
        lines = data.split("\n")
        llines = []
        make_long_lookup_table(mt, v);
        do_make_output(mt,v,lines)


print("//output done")

sys.exit()

