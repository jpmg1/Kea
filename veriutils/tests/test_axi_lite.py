from unittest import TestCase
from veriutils import *
from myhdl import *

try:
    import Queue as queue
except ImportError:
    import queue

class TestAxiLiteMasterBFM(TestCase):
    ''' There should be an AXI Lite Bus Functional Model that implements
    a programmable AXI Lite protocol from the master side.
    '''

    def setUp(self):

        self.addr_width = 4
        self.data_width = 32

        self.wstrb_width = self.data_width//8

        self.responses = [0, 2, 3]

        self.clock = Signal(bool(0))
        self.reset = Signal(bool(0))
        self.axi_lite = AxiLiteMasterBFM()
        self.axi_lite_interface = AxiLiteInterface(
            self.data_width, self.addr_width)

        self.args = {'clock': self.clock}
        self.arg_types = {'clock': 'clock'}

    @block
    def SimpleAxiLiteWriteSlaveBFM(
        self, clock, reset, axi_lite_interface, addr_high_prob=0.05,
        addr_low_prob=0.2, data_high_prob=0.05, data_low_prob=0.2,
        resp_valid_prob=0.2):

        t_write_state = enum(
            'IDLE', 'ADDR_RECEIVED', 'DATA_RECEIVED', 'RESPOND')
        write_state = Signal(t_write_state.IDLE)

        @always(clock.posedge)
        def write():

            if reset:
                # Axi reset so drive control signals low and return to idle.
                axi_lite_interface.AWREADY.next = False
                axi_lite_interface.WREADY.next = False
                axi_lite_interface.BVALID.next = False
                write_state.next = t_write_state.IDLE

            else:
                if (not axi_lite_interface.AWREADY and
                    random.random() < addr_high_prob):
                    # Randomly set ready to receive address.
                    axi_lite_interface.AWREADY.next = (
                        True)
                elif (axi_lite_interface.AWREADY and
                    random.random() < addr_low_prob):
                    axi_lite_interface.AWREADY.next = (
                        False)

                if (not axi_lite_interface.WREADY and
                    random.random() < data_high_prob):
                    # Randomly set ready to receive data.
                    axi_lite_interface.WREADY.next = (
                        True)
                elif (axi_lite_interface.WREADY and
                      random.random() < data_low_prob):
                    axi_lite_interface.WREADY.next = (
                        False)

                if write_state == t_write_state.IDLE:
                    # Waiting to receive address and data.
                    if (axi_lite_interface.AWREADY and
                        axi_lite_interface.AWVALID and
                        axi_lite_interface.WREADY and
                        axi_lite_interface.WVALID):
                        # Received address and data from the master.
                        axi_lite_interface.AWREADY.next = (
                            False)
                        axi_lite_interface.WREADY.next = (
                            False)
                        write_state.next = t_write_state.RESPOND

                    elif (axi_lite_interface.AWREADY and
                          axi_lite_interface.AWVALID):
                        # Received address from the master.
                        axi_lite_interface.AWREADY.next = (
                            False)
                        write_state.next = t_write_state.ADDR_RECEIVED

                    elif (axi_lite_interface.WREADY and
                          axi_lite_interface.WVALID):
                        # Received data from the master.
                        axi_lite_interface.WREADY.next = (
                            False)
                        write_state.next = t_write_state.DATA_RECEIVED

                elif write_state == t_write_state.ADDR_RECEIVED:
                    if (axi_lite_interface.WREADY and
                        axi_lite_interface.WVALID):
                        # Received data from the master.
                        axi_lite_interface.WREADY.next = (
                            False)
                        write_state.next = t_write_state.RESPOND

                elif write_state == t_write_state.DATA_RECEIVED:
                    if (axi_lite_interface.AWREADY and
                        axi_lite_interface.AWVALID):
                        # Received address from the master.
                        axi_lite_interface.AWREADY.next = (
                            False)
                        write_state.next = t_write_state.RESPOND

                elif write_state == t_write_state.RESPOND:
                    if not axi_lite_interface.BVALID:
                        # Valid signal has not yet been set.
                        if random.random() < resp_valid_prob:
                            # Wait a random period before setting the valid
                            # signal.
                            axi_lite_interface.BVALID.next =(
                                True)
                            axi_lite_interface.BRESP.next =(
                                random.choice(self.responses))

                    elif (axi_lite_interface.BVALID and
                          axi_lite_interface.BREADY):
                        # Response has been received so set the valid signal
                        # low again.
                        axi_lite_interface.BVALID.next = (
                            False)
                        write_state.next = t_write_state.IDLE

        return write

    @block
    def SimpleAxiLiteReadSlaveBFM(
        self, clock, reset, axi_lite_interface, addr_high_prob=0.05,
        addr_low_prob=0.1):

        t_read_state = enum('IDLE', 'RESPOND')
        read_state = Signal(t_read_state.IDLE)

        @always(clock.posedge)
        def read():

            if reset:
                # Axi reset so drive control signals low and return to idle.
                axi_lite_interface.ARREADY.next = False
                axi_lite_interface.RVALID.next = False
                read_state.next = t_read_state.IDLE

            else:
                if (not axi_lite_interface.ARREADY and
                    random.random() < addr_high_prob):
                    # Randomly set ready to receive address.
                    axi_lite_interface.ARREADY.next = (
                        True)
                elif (axi_lite_interface.ARREADY and
                      random.random() < addr_low_prob):
                    axi_lite_interface.ARREADY.next = (
                        False)

                if read_state == t_read_state.IDLE:
                    if (axi_lite_interface.ARREADY and
                        axi_lite_interface.ARVALID):
                        # Received the read address so respond with the data.
                        axi_lite_interface.ARREADY.next = (
                            False)
                        axi_lite_interface.RVALID.next = True
                        axi_lite_interface.RDATA.next = (
                            random.randint(0, 2**self.data_width-1))
                        axi_lite_interface.RRESP.next =(
                                random.choice(self.responses))
                        read_state.next = t_read_state.RESPOND

                if read_state == t_read_state.RESPOND:
                    if (axi_lite_interface.RVALID and
                        axi_lite_interface.RREADY):
                        # The response has been received.
                        axi_lite_interface.RVALID.next = False
                        read_state.next = t_read_state.IDLE

        return read

    def test_reset(self):
        ''' On reset the Master should drive ARVALID, AWVALID and WVALID low.

        It may only next drive the valid signals one rising edge after the
        reset signal goes high.

        We do not care about the other signals.
        '''

        cycles = 4000

        @block
        def testbench(clock):
            master_bfm = self.axi_lite.model(
                clock, self.reset, self.axi_lite_interface)
            slave_write_bfm = self.SimpleAxiLiteWriteSlaveBFM(
                clock, self.reset, self.axi_lite_interface)
            slave_read_bfm = self.SimpleAxiLiteReadSlaveBFM(
                clock, self.reset, self.axi_lite_interface)

            reset_low_prob = 0.1
            reset_high_prob = 0.05
            add_write_transaction_prob = 0.05
            add_read_transaction_prob = 0.05

            t_check_state = enum('IDLE', 'CHECK_RESET')
            check_state = Signal(t_check_state.IDLE)

            @always(clock.posedge)
            def check():

                if not self.reset and (random.random() < reset_high_prob):
                    self.reset.next = True
                elif self.reset and (random.random() < reset_low_prob):
                    self.reset.next = False

                if random.random() < add_write_transaction_prob:
                    # At random times set up an axi lite write transaction
                    self.axi_lite.add_write_transaction(
                        write_address=random.randint(
                            0, 2**self.addr_width-1),
                        write_data=random.randint(0, 2**self.data_width-1),
                        write_strobes=random.randint(
                            0, 2**self.wstrb_width-1),
                        write_protection=random.randint(0, 2**len(
                            self.axi_lite_interface.AWPROT)-1),
                        address_delay=random.randint(0, 15),
                        data_delay=random.randint(0, 15),
                        response_ready_delay=random.randint(10, 25))

                if random.random() < add_read_transaction_prob:
                    # At random times set up an axi lite read transaction
                    self.axi_lite.add_read_transaction(
                        read_address=random.randint(0, 2**self.addr_width-1),
                        read_protection=random.randint(0, 2**len(
                            self.axi_lite_interface.ARPROT)-1),
                        address_delay=random.randint(0, 15),
                        data_delay=random.randint(0, 15))

                try:
                    # Try to remove any responses from the responses Queue.
                    # In this test we are not actually interested in the
                    # response but we want to prevent the queue from filling
                    # up
                    self.axi_lite.write_responses.get(False)
                except queue.Empty:
                    pass

                try:
                    # Try to remove any responses from the responses Queue.
                    # In this test we are not actually interested in the
                    # response but we want to prevent the queue from filling
                    # up
                    self.axi_lite.read_responses.get(False)
                except queue.Empty:
                    pass

                if check_state == t_check_state.IDLE:
                    if self.reset:
                        # Reset has been received so move onto the check_reset
                        # state.
                        check_state.next = t_check_state.CHECK_RESET

                if check_state == t_check_state.CHECK_RESET:
                    assert(
                        self.axi_lite_interface.ARVALID==False)
                    assert(
                        self.axi_lite_interface.AWVALID==False)
                    assert(
                        self.axi_lite_interface.WVALID==False)

                    if not self.reset:
                        # No longer being reset so return to IDLE
                        check_state.next = t_check_state.IDLE

            return check, master_bfm, slave_write_bfm, slave_read_bfm

        myhdl_cosimulation(
            cycles, None, testbench, self.args, self.arg_types)

    def test_valid(self):
        ''' Once VALID is asserted it must remain asserted until the handshake
        occurs, a rising clock edge at which VALID and READY are both
        asserted.
        '''

        cycles = 4000

        @block
        def testbench(clock):
            master_bfm = self.axi_lite.model(
                clock, self.reset, self.axi_lite_interface)
            slave_write_bfm = self.SimpleAxiLiteWriteSlaveBFM(
                clock, self.reset, self.axi_lite_interface)
            slave_read_bfm = self.SimpleAxiLiteReadSlaveBFM(
                clock, self.reset, self.axi_lite_interface)

            add_write_transaction_prob = 0.05
            add_read_transaction_prob = 0.05

            check_enable = {'awvalid': False,
                            'wvalid': False,
                            'arvalid': False}

            @always(clock.posedge)
            def check():

                if random.random() < add_write_transaction_prob:
                    # At random times set up an axi lite write transaction
                    self.axi_lite.add_write_transaction(
                        write_address=random.randint(
                            0, 2**self.addr_width-1),
                        write_data=random.randint(0, 2**self.data_width-1),
                        write_strobes=random.randint(
                            0, 2**self.wstrb_width-1),
                        write_protection=random.randint(0, 2**len(
                            self.axi_lite_interface.AWPROT)-1),
                        address_delay=random.randint(0, 15),
                        data_delay=random.randint(0, 15),
                        response_ready_delay=random.randint(10, 25))

                if random.random() < add_read_transaction_prob:
                    # At random times set up an axi lite read transaction
                    self.axi_lite.add_read_transaction(
                        read_address=random.randint(0, 2**self.addr_width-1),
                        read_protection=random.randint(0, 2**len(
                            self.axi_lite_interface.ARPROT)-1),
                        address_delay=random.randint(0, 15),
                        data_delay=random.randint(0, 15))

                try:
                    # Try to remove any responses from the responses Queue.
                    # In this test we are not actually interested in the
                    # response but we want to prevent the queue from filling
                    # up
                    self.axi_lite.write_responses.get(False)
                except queue.Empty:
                    pass

                if (self.axi_lite_interface.AWVALID and
                    self.axi_lite_interface.AWREADY):
                    # Handshake has occured do not need to check that AWVALID
                    # stays high.
                    check_enable['awvalid'] = False
                elif self.axi_lite_interface.AWVALID:
                    # Once AWVALID is set it should remain high until the
                    # handshake occurs
                    check_enable['awvalid'] = True

                if (self.axi_lite_interface.WVALID and
                    self.axi_lite_interface.WREADY):
                    # Handshake has occured do not need to check that WVALID
                    # stays high.
                    check_enable['wvalid'] = False
                elif self.axi_lite_interface.WVALID:
                    # Once WVALID is set it should remain high until the
                    # handshake occurs
                    check_enable['wvalid'] = True

                if (self.axi_lite_interface.ARVALID and
                    self.axi_lite_interface.ARREADY):
                    # Handshake has occured do not need to check that ARVALID
                    # stays high.
                    check_enable['arvalid'] = False
                elif self.axi_lite_interface.ARVALID:
                    # Once ARVALID is set it should remain high until the
                    # handshake occurs
                    check_enable['arvalid'] = True

                if check_enable['awvalid']:
                    assert(
                        self.axi_lite_interface.AWVALID == True)

                if check_enable['wvalid']:
                    assert(
                        self.axi_lite_interface.WVALID == True)

                if check_enable['arvalid']:
                    assert(
                        self.axi_lite_interface.ARVALID == True)

            return check, master_bfm, slave_write_bfm, slave_read_bfm

        myhdl_cosimulation(
            cycles, None, testbench, self.args, self.arg_types)

    def test_data_write(self):
        ''' The master BFM should send the requested Address and Protections
        in the address transaction.

        The master BFM should send the requested Data and Stobes in the data
        transaction.

        The master BFM should correctly receive the Response in the response
        transaction.
        '''

        cycles = 4000

        @block
        def testbench(clock):
            master_bfm = self.axi_lite.model(
                clock, self.reset, self.axi_lite_interface)
            slave_write_bfm = self.SimpleAxiLiteWriteSlaveBFM(
                clock, self.reset, self.axi_lite_interface)
            slave_read_bfm = self.SimpleAxiLiteReadSlaveBFM(
                clock, self.reset, self.axi_lite_interface)

            add_write_transaction_prob = 0.05

            t_check_state = enum(
                'IDLE', 'TRANSACTIONS', 'CHECK_RESPONSE')
            check_state = Signal(t_check_state.IDLE)

            expected = {'addr': 0,
                        'data': 0,
                        'strbs': 0,
                        'prot': 0,
                        'resp': 0,}

            control = {'addr_sent': False,
                       'data_sent': False,
                       'resp_sent': False,
                       'wr_resp_transaction': None,}

            @always(clock.posedge)
            def check():

                if check_state == t_check_state.IDLE:
                    if random.random() < add_write_transaction_prob:
                        # Create the random data that we will request from the
                        # BFM.
                        expected['addr'] = random.randint(
                            0, 2**self.addr_width-1)
                        expected['data'] = random.randint(
                            0, 2**self.data_width-1)
                        expected['strbs'] = random.randint(
                            0, 2**self.wstrb_width-1)
                        expected['prot'] = random.randint(0, 2**len(
                            self.axi_lite_interface.AWPROT)-1)

                        # Set up an axi lite write transaction
                        self.axi_lite.add_write_transaction(
                            write_address=expected['addr'],
                            write_data=expected['data'],
                            write_strobes=expected['strbs'],
                            write_protection=expected['prot'],
                            address_delay=random.randint(0, 15),
                            data_delay=random.randint(0, 15),
                            response_ready_delay=random.randint(10, 25))

                        control['addr_sent'] = False
                        control['data_sent'] = False
                        control['resp_sent'] = False

                        check_state.next = t_check_state.TRANSACTIONS

                elif check_state == t_check_state.TRANSACTIONS:
                    if self.axi_lite_interface.AWVALID:
                        # If valid is asserted, the requested address and
                        # protection should be output.
                        assert(
                            self.axi_lite_interface.AWADDR==
                            expected['addr'])
                        assert(
                            self.axi_lite_interface.AWPROT==
                            expected['prot'])
                        if self.axi_lite_interface.AWREADY:
                            # Handshake has occurred.
                            control['addr_sent'] = True

                    if self.axi_lite_interface.WVALID:
                        # If valid is asserted, the requested data and strobes
                        # should be output.
                        assert(
                            self.axi_lite_interface.WDATA==
                            expected['data'])
                        assert(
                            self.axi_lite_interface.WSTRB==
                            expected['strbs'])
                        if self.axi_lite_interface.WREADY:
                            # Handshake has occurred.
                            control['data_sent'] = True

                    if (self.axi_lite_interface.BVALID and
                        self.axi_lite_interface.BREADY):
                        # Record the response to check that the BFM receives
                        # and reports it correctly
                        expected['resp'] = (
                            self.axi_lite_interface.BRESP)
                        # Handshake has occurred.
                        control['resp_sent'] = True

                    if (control['addr_sent'] and
                        control['data_sent'] and
                        control['resp_sent']):
                        # All transactions have occured.
                        check_state.next = t_check_state.CHECK_RESPONSE

                elif check_state == t_check_state.CHECK_RESPONSE:
                    # Remove the response from the responses Queue and check
                    # it is correct.
                    try:
                        control['wr_resp_transaction'] = (
                            self.axi_lite.write_responses.get(True, timeout=1))
                    except queue.Empty:
                        raise Exception("Timeout")

                    assert(
                        control['wr_resp_transaction']['wr_resp']==(
                            expected['resp']))
                    check_state.next = t_check_state.IDLE

            return check, master_bfm, slave_write_bfm, slave_read_bfm

        myhdl_cosimulation(
            cycles, None, testbench, self.args, self.arg_types)

    def test_data_read(self):
        ''' The master BFM should send the requested Address and Protections
        in the address transaction.

        The master BFM should correctly receive the Data and Response in the
        response transaction.
        '''

        cycles = 4000

        @block
        def testbench(clock):
            master_bfm = self.axi_lite.model(
                clock, self.reset, self.axi_lite_interface)
            slave_write_bfm = self.SimpleAxiLiteWriteSlaveBFM(
                clock, self.reset, self.axi_lite_interface)
            slave_read_bfm = self.SimpleAxiLiteReadSlaveBFM(
                clock, self.reset, self.axi_lite_interface)

            add_read_transaction_prob = 0.05

            t_check_state = enum(
                'IDLE', 'TRANSACTIONS', 'CHECK_RESPONSE')
            check_state = Signal(t_check_state.IDLE)

            expected = {'addr': 0,
                        'prot': 0,
                        'data': 0,
                        'resp': 0,}

            control = {'addr_sent': False,
                       'data_sent': False,
                       'rd_data_transaction': None,}

            @always(clock.posedge)
            def check():

                if check_state == t_check_state.IDLE:
                    if random.random() < add_read_transaction_prob:
                        # Create the random data that we will request from the
                        # BFM.
                        expected['addr'] = random.randint(
                            0, 2**self.addr_width-1)
                        expected['prot'] = random.randint(0, 2**len(
                            self.axi_lite_interface.ARPROT)-1)

                        # At random times set up an axi lite read transaction
                        self.axi_lite.add_read_transaction(
                            read_address=expected['addr'],
                            read_protection=expected['prot'],
                            address_delay=random.randint(0, 15),
                            data_delay=random.randint(0, 15))

                        control['addr_sent'] = False
                        control['data_sent'] = False

                        check_state.next = t_check_state.TRANSACTIONS

                elif check_state == t_check_state.TRANSACTIONS:
                    if self.axi_lite_interface.ARVALID:
                        # If valid is asserted, the requested address and
                        # protection should be output.
                        assert(
                            self.axi_lite_interface.ARADDR==
                            expected['addr'])
                        assert(
                            self.axi_lite_interface.ARPROT==
                            expected['prot'])
                        if self.axi_lite_interface.ARREADY:
                            # Handshake has occurred.
                            control['addr_sent'] = True

                    if (self.axi_lite_interface.RVALID and
                        self.axi_lite_interface.RREADY):
                        # Record the response to check that the BFM receives
                        # and reports it correctly
                        expected['data'] = (
                            self.axi_lite_interface.RDATA)
                        expected['resp'] = (
                            self.axi_lite_interface.RRESP)
                        # Handshake has occurred.
                        control['data_sent'] = True

                    if (control['addr_sent'] and
                        control['data_sent']):
                        # All transactions have occured.
                        check_state.next = t_check_state.CHECK_RESPONSE

                elif check_state == t_check_state.CHECK_RESPONSE:
                    # Remove the response from the responses Queue and check
                    # it is correct.
                    try:
                        control['rd_data_transaction'] = (
                            self.axi_lite.read_responses.get(True, timeout=1))
                    except queue.Empty:
                        raise Exception("Timeout")

                    assert(control['rd_data_transaction']['rd_data']==(
                        expected['data']))
                    assert(control['rd_data_transaction']['rd_resp']==(
                        expected['resp']))
                    check_state.next = t_check_state.IDLE

            return check, master_bfm, slave_write_bfm, slave_read_bfm

        myhdl_cosimulation(
            cycles, None, testbench, self.args, self.arg_types)
