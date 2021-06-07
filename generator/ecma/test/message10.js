var should = require('should');

describe('MAVLink 1.0 message registry', function() {

    beforeEach(function() {
        return new Promise( (beforePromiseResolve) => {
            let mavlinkPromise = import('../implementations/mavlink_common_v1.0/mavlink.js');
            mavlinkPromise.then( (mavlink) => {
                if( typeof window === 'undefined') {
                    global.mavlink = mavlink;
                }
                else {
                    window.mavlink = mavlink;
                }

                beforePromiseResolve();
            });
        });
    });

    it('defines constructors for every message', function() {
        mavlink.messages.GPS_RAW_INT.should.be.a.function;
    });

    it('assigns message properties, _format with int64 (q), gps_raw_int', function() {
        var m = new mavlink.messages.GPS_RAW_INT();
        m._format.should.equal("<QiiiHHHHBB");
        m.order_map.should.eql([0, 8, 1, 2, 3, 4, 5, 6, 7, 9]); // should.eql = shallow comparison
        m.crc_extra.should.equal(24);
        m._id.should.equal(mavlink.MAVLINK_MSG_ID.MAVLINK_MSG_ID_GPS_RAW_INT);
    });

    it('assigns message properties, heartbeat', function() {
        var m = new mavlink.messages.HEARTBEAT();
        m._format.should.equal("<IBBBBB");
        m.order_map.should.eql([1, 2, 3, 0, 4, 5]); // should.eql = shallow comparison
        m.crc_extra.should.equal(50);
        m._id.should.equal(mavlink.MAVLINK_MSG_ID.MAVLINK_MSG_ID_HEARTBEAT);
    });

});

describe('Complete MAVLink 1.0 packet', function() {

    beforeEach(function() {
        return new Promise( (beforePromiseResolve) => {
            let mavlinkPromise = import('../implementations/mavlink_common_v1.0/mavlink.js');
            mavlinkPromise.then( (mavlink) => {
                if( typeof window === 'undefined') {
                    global.mavlink = mavlink;
                }
                else {
                    window.mavlink = mavlink;
                }
                
                // MAV mock
                this.mav = new mavlink.MAVLink(null, 42, 150);

                beforePromiseResolve();
            });
        });
    });

    it('encode gps_raw_int', function() {

        // 0x75bcd15 = 123456789
        var gpsraw = new mavlink.messages.GPS_RAW_INT(
            time_usec=123456789n
            , fix_type=3
            , lat=47123456
            , lon=8123456
            , alt=50000
            , eph=6544
            , epv=4566
            , vel=1235
            , cog=1234
            , satellites_visible=9
        );

        this.mav.seq = 5;

        // Create a buffer that matches what the Python version of MAVLink creates
        var reference = Uint8Array.from([0xfe, 0x1e, 0x05, 0x2a, 0x96, 0x18, 0x15, 0xcd, 0x5b, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0xcf, 0x02, 0x40, 0xf4, 0x7b, 0x00, 0x50, 0xc3, 0x00, 0x00, 0x90, 0x19, 0xd6, 0x11, 0xd3, 0x04, 0xd2, 0x04, 0x03, 0x09, 0xee, 0x16]);
        Uint8Array.from(gpsraw.pack(this.mav)).should.eql(reference);

    });

    it('encode gps_raw_int with long integer', function() {

        // number ~2^60
        // 1152221500606846977 = 0xffd8359 9e3d1801
        var gpsraw = new mavlink.messages.GPS_RAW_INT(
            time_usec=1152221500606846977n
            , fix_type=3
            , lat=47123456
            , lon=8123456
            , alt=50000
            , eph=6544
            , epv=4566
            , vel=1235
            , cog=1234
            , satellites_visible=9
        );

        this.mav.seq = 5;
        
        // Create a buffer that matches what the Python version of MAVLink creates
        var reference = Uint8Array.from([0xfe, 0x1e, 0x05, 0x2a, 0x96, 0x18, 0x01, 0x18, 0x3d, 0x9e, 0x59, 0x83, 0xfd, 0x0f, 0x00, 0x0c, 0xcf, 0x02, 0x40, 0xf4, 0x7b, 0x00, 0x50, 0xc3, 0x00, 0x00, 0x90, 0x19, 0xd6, 0x11, 0xd3, 0x04, 0xd2, 0x04, 0x03, 0x09, 0x6c, 0xe8]);
        Uint8Array.from(gpsraw.pack(this.mav)).should.eql(reference);

    });

    it('encode heartbeat', function() {

        var heartbeat = new mavlink.messages.HEARTBEAT(
            type=5
            , autopilot=3
            , base_mode=45
            , custom_mode=68
            , system_status=13
            , mavlink_version=1
        );
        
        this.mav.seq = 7;

        // Create a buffer that matches what the Python version of MAVLink creates
        var reference = Uint8Array.from([0xfe, 0x09, 0x07, 0x2a, 0x96, 0x00, 0x44, 0x00, 0x00, 0x00, 0x05, 0x03, 0x2d, 0x0d, 0x01, 0xac, 0x9d]);
        Uint8Array.from(heartbeat.pack(this.mav)).should.eql(reference);

    });

    it('decode gps_raw_int with long integer', function() {

        // number ~2^60
        // 1152221500606846977 = 0xffd8359 9e3d1801

        // Create a buffer that matches what the Python version of MAVLink creates
        var reference = Uint8Array.from([0xfe, 0x1e, 0x05, 0x2a, 0x96, 0x18, 0x01, 0x18, 0x3d, 0x9e, 0x59, 0x83, 0xfd, 0x0f, 0x00, 0x0c, 0xcf, 0x02, 0x40, 0xf4, 0x7b, 0x00, 0x50, 0xc3, 0x00, 0x00, 0x90, 0x19, 0xd6, 0x11, 0xd3, 0x04, 0xd2, 0x04, 0x03, 0x09, 0x6c, 0xe8]);

        var m = new mavlink.MAVLink();

        var msg = m.parseBuffer(reference);

        // check header
        msg[0]._header.seq.should.eql(5);
        msg[0]._header.srcSystem.should.eql(42);
        msg[0]._header.srcComponent.should.eql(150);

        // check payload
        msg[0].time_usec.should.eql(1152221500606846977n);
        msg[0].fix_type.should.eql(3);
        msg[0].lat.should.eql(47123456);
        msg[0].lon.should.eql(8123456);
        msg[0].alt.should.eql(50000);
        msg[0].eph.should.eql(6544);
        msg[0].epv.should.eql(4566);
        msg[0].vel.should.eql(1235);
        msg[0].cog.should.eql(1234);
        msg[0].satellites_visible.should.eql(9);

    });


});

describe('MAVLink 1.0 header', function() {
    beforeEach(function() {
        return new Promise( (beforePromiseResolve) => {
            let mavlinkPromise = import('../implementations/mavlink_common_v1.0/mavlink.js');
            mavlinkPromise.then( (mavlink) => {
                if( typeof window === 'undefined') {
                    global.mavlink = mavlink;
                }
                else {
                    window.mavlink = mavlink;
                }
                
                this.h = new mavlink._testing_fixtures.MAVLinkHeader(mavlink.MAVLINK_MSG_ID.MAVLINK_MSG_ID_PARAM_REQUEST_LIST, 1, 2, 3, 4);

                beforePromiseResolve();
            });
        });        
    });

    it('Can pack itself', function() {
        this.h.pack().should.eql(Uint8Array.from([254, 1, 2, 3, 4, 21]));
    });

});

describe('MAVLink 1.0 message', function() {

    beforeEach(function() {
        return new Promise( (beforePromiseResolve) => {
            let mavlinkPromise = import('../implementations/mavlink_common_v1.0/mavlink.js');
            mavlinkPromise.then( (mavlink) => {
                if( typeof window === 'undefined') {
                    global.mavlink = mavlink;
                }
                else {
                    window.mavlink = mavlink;
                }

                // This is a heartbeat packet from a GCS to the APM.
                this.heartbeat = new mavlink.messages.HEARTBEAT(
                    mavlink.MAV_TYPE.MAV_TYPE_GCS, // 6
                    mavlink.MAV_AUTOPILOT.MAV_AUTOPILOT_INVALID, // 8
                    0, // base mode, mavlink10.MAV_MODE_FLAG_***
                    0, // custom mode
                    mavlink.MAV_STATE.MAV_STATE_STANDBY, // system status
                    3 // MAVLink version
                );

                this.mav = new mavlink.MAVLink();

                beforePromiseResolve();
            });
        });
    });

    it('has a set function to facilitate vivifying the object', function() {
        this.heartbeat.type.should.equal(mavlink.MAV_TYPE.MAV_TYPE_GCS);
        this.heartbeat.autopilot.should.equal(mavlink.MAV_AUTOPILOT.MAV_AUTOPILOT_INVALID);
        this.heartbeat.base_mode.should.equal(0);
        this.heartbeat.custom_mode.should.equal(0);
        this.heartbeat.system_status.should.equal(mavlink.MAV_STATE.MAV_STATE_STANDBY);
    });

    // TODO: the length below (9) should perhaps be instead 7.  See mavlink10.unpack().
    // might have to do with the length of the encoding (<I is 4 symbols in the array) 
    it('Can pack itself', function() {

        var packed = this.heartbeat.pack(this.mav);
        packed.should.eql(Uint8Array.from([254, 9, 0, 0, 0, mavlink.MAVLINK_MSG_ID.MAVLINK_MSG_ID_HEARTBEAT, // that bit is the header,
            // this is the payload, arranged in the order map specified in the protocol,
            // which differs from the constructor.
            0, 0, 0, 0, // custom bitfield -- length 4 (type=I)
            mavlink.MAV_TYPE.MAV_TYPE_GCS,
            mavlink.MAV_AUTOPILOT.MAV_AUTOPILOT_INVALID,
            0,
            mavlink.MAV_STATE.MAV_STATE_STANDBY,
            3,
            109, // CRC
            79 // CRC
            ]));

    });

    describe('decode 1.0 function', function() {

        beforeEach(function() {
            this.m = new mavlink.MAVLink();
        });

        // need to add tests for the header fields as well, specifying seq etc.
        it('Can decode itself', function() {

            var packed = this.heartbeat.pack(this.m);
            var message = this.m.decode(packed);

            // this.fieldnames = ['type', 'autopilot', 'base_mode', 'custom_mode', 'system_status', 'mavlink_version'];
            message.type.should.equal(mavlink.MAV_TYPE.MAV_TYPE_GCS);  // supposed to be 6
            message.autopilot.should.equal(mavlink.MAV_AUTOPILOT.MAV_AUTOPILOT_INVALID); // supposed to be 8
            message.base_mode.should.equal(0); // supposed to be 0
            message.custom_mode.should.equal(0);
            message.system_status.should.equal(mavlink.MAV_STATE.MAV_STATE_STANDBY); // supposed to be 3
            message.mavlink_version.should.equal(3); //?

        });

        it('throws an error if the message has a bad prefix', function() {
            var packed = Uint8Array.from([0, 3, 5, 7, 9, 11]); // bad data prefix in header (0, not 254)
            var m = this.m;
            (function() { m.decode(packed); }).should.throw('Invalid MAVLink prefix (0)');
        });

        it('throws an error if the message ID is not known', function() {
            var packed = Uint8Array.from([254, 1, 0, 3, 0, 200, 1, 0, 0]); // 200 = invalid ID
            var m = this.m;
            (function() { m.decode(packed); }).should.throw('Unknown MAVLink message ID (200)');
        });

        it('throws an error if the message length is invalid', function() {
            var packed = Uint8Array.from([254, 3, 257, 0, 0, 0, 0, 0]);
            var m = this.m;
            (function() { m.decode(packed); }).should.throw('Invalid MAVLink message length.  Got 0 expected 3, msgId=0');
        });

        it('throws an error if the CRC cannot be unpacked', function() {
            
        });

        it('throws an error if the CRC can not be decoded', function() {

        });

        it('throws an error if it is unable to unpack the payload', function() {

        });

        it('throws an error if it is unable to instantiate a MAVLink message object from the payload', function() {

        });

    });
});
