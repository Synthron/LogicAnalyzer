import sigrokdecode as srd # type: ignore
from functools import reduce
from .tables import opcodes

def reduce_bus(bus):
    if 0xFF in bus:
        return None  # unassigned bus channels
    else:
        return reduce(lambda a, b: (a << 1) | b, reversed(bus))
    

def reduce_partial_bus(pins, bit_positions):
    """
    Construct an integer from partial bus bits.
    pins: dict {pin_number: bit_value}
    bit_positions: list of pin numbers corresponding to bit 0..n-1

    Missing bits default to 0.
    """
    val = 0
    for i, pin_num in enumerate(bit_positions):
        bit = pins.get(pin_num, 0)  # default missing pins to 0
        val |= (bit & 1) << i
    return val

class Row:
    ADDRBUS, DATABUS, INSTRUCTIONS = range(3)

class Pin:
    D0, D7 = 0, 7
    CLK, SYNC, RW = range(8,11)
    A0, A15 = 11, 26

class Ann:
    Addr, Data, Inst, Fetch, Operand1, Operand2, Read, Write = range(8)

class Cycles:
    Fetch, Op1, Op2, Read, Write = range(5)

class maps:
    cycle_to_name_map = {
        Cycles.Fetch: 'Fetch',
        Cycles.Op1:   'Op1',
        Cycles.Op2:   'Op2',
        Cycles.Read:  'Read',
        Cycles.Write: 'Write',
    }

    cycle_ann_map = {
        Cycles.Fetch: Ann.Fetch,
        Cycles.Op1: Ann.Operand1,
        Cycles.Op2: Ann.Operand2,
        Cycles.Read: Ann.Read,
        Cycles.Write: Ann.Write
    }

class Decoder(srd.Decoder):
    api_version = 3
    id       = 'wdc65c02'
    name     = 'wdc65C02'
    longname = 'WDC 65C02 CPU'
    desc     = 'WDC 65C02 microprocessor disassembly.'
    license  = 'gplv3+'
    inputs   = ['logic']
    outputs  = []
    tags     = ['Retro computing']
    channels = tuple({
            'id': 'd%d' % i,
            'name': 'D%d' % i,
            'desc': 'Data bus line %d' % i
            } for i in range(8)
    ) + (
        {'id': 'clk', 'name': 'CLK', 'desc': 'System Clock Signal'},
        {'id': 'sync', 'name': 'SYNC', 'desc': 'Machine cycle 1'},
        {'id': 'rw', 'name': 'RW', 'desc': 'Read/Write'},
    ) 
    optional_channels = tuple({
        'id': 'a%d' % i,
        'name': 'A%d' % i,
        'desc': 'Address bus line %d' % i
        } for i in range(16)
    )
    annotations = (
        ('addr', 'Memory Address'),
        ('data', 'Data Byte'),
        ('inst', 'Instructions'),
        ('fetch', 'Fetch'),
        ('op1', 'Operand'),
        ('op2', 'Operand2'),
        ('read', 'Read'),
        ('write', 'Write')
    )
    annotation_rows = (
        ('addrbus', 'Address bus', (Ann.Addr,)),
        ('databus', 'Data bus', (Ann.Data,)),
        ('insname', 'Instructions', (Ann.Inst,)),
        ('cycles' , 'Machine Cycles', (Ann.Fetch, Ann.Operand1, Ann.Operand2, Ann.Read, Ann.Write))
    )

    def reset(self):
        pass

    def start(self):
        #variable definition and initialization
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.bus_addr = None
        self.bus_data = None
        self.clk_block_ss = None
        self.instr_start = None
        self.instr_done = None
        self.sync_old = None
        self.cycle = None
        self.inst_flag = 0

        self.opcount  = 0
        self.cycle    = Cycles.Read
        self.opcode   = -1
        self.sync_old = 1

    def decode(self):
        #do it for all available samples.
        #while true will abort once no more samples are available
        while True:
            
            # Wait for falling clock edge
            # try catch to exit the while loop safely when no more transitions are found
            try:
                pins = self.wait({Pin.CLK : 'f'})
            except self.WaitException:
                break
            
            # start annotating the bus for the previously available cycle
            if self.clk_block_ss is not None:
                # Print Address Bus if decoding was successful
                if self.bus_addr is not None:
                    self.put(self.clk_block_ss, self.samplenum, self.out_ann, [Ann.Addr, [format(self.bus_addr, '04X')+'h']])
                # print Data Bus if decoding was successful
                if self.bus_data is not None:
                    self.put(self.clk_block_ss, self.samplenum, self.out_ann, [Ann.Data, [format(self.bus_data, '02X')+'h']])

                # Cycle Decoding
                if sync == 1 and self.inst_flag == 1:
                    self.cycle    = Cycles.Fetch
                    self.len      = opcodes.get(self.opcode, ('???', 1))[1]
                    self.opcount  = self.len - 1
                elif pin_rnw == 0:
                    self.cycle = Cycles.Write

                elif self.cycle == Cycles.Fetch and self.opcount > 0:
                    self.cycle = Cycles.Op1
                    self.opcount -= 1

                elif self.cycle == Cycles.Op1 and self.opcount > 0:
                    if (self.opcode == 0x20): # JSR is <opcode> <op1> <dummp stack rd> <stack wr> <stack wr> <op2>
                        self.cycle = Cycles.Read
                    else:
                        self.cycle = Cycles.Op2
                        self.opcount -= 1

                else:
                    if (self.opcode == 0x20): # JSR, see above
                        self.cycle = Cycles.Op2
                        self.opcount -= 1
                    else:
                        self.cycle = Cycles.Read

                # Increment the cycle number (used only to detect taken branches)
                self.put(self.clk_block_ss, self.samplenum, self.out_ann, [maps.cycle_ann_map[self.cycle], [maps.cycle_to_name_map[self.cycle]]])


            self.clk_block_ss = self.samplenum


            # Wait for rising clock edge
            # Data on the bus is valid during this time
            try:
                pins = self.wait({Pin.CLK : 'r'})
            except self.WaitException:
                break

            # read address and data on the bus and convert it into a single number
            self.bus_data = reduce_bus(pins[Pin.D0:Pin.D7+1])

            #rudimentary optional address bus decoding if all pins are available
            #doesn't crash decoder when pins are not declared
            try:
                self.bus_addr = reduce_bus(pins[Pin.A0:Pin.A15+1])
            except self.WaitException:
                self.bus_addr = None
                break
            

            # if previous instruction already known
            sync = pins[Pin.SYNC]
            pin_rnw   = pins[Pin.RW]
            if sync == 1 and self.sync_old != 1 and self.inst_flag == 1:

                mnemonic = opcodes.get(self.opcode, ('???', 1))[0]
                self.put(self.instr_start, self.clk_block_ss, self.out_ann, [Ann.Inst, [mnemonic]])
                self.inst_flag = 0
            #if no instruction before or last instruction done
            if sync == 1 and self.sync_old != 1 and self.inst_flag != 1:
                self.instr_start = self.clk_block_ss
                self.inst_flag = 1
                self.opcode = self.bus_data

            self.sync_old = sync

        pass
