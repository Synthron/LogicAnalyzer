import sigrokdecode as srd # type: ignore
from functools import reduce
from .tables import addr_mode_len_map, instr_table, AddrMode
import string

def reduce_bus(bus):
    if 0xFF in bus:
        return None  # unassigned bus channels
    else:
        return reduce(lambda a, b: (a << 1) | b, reversed(bus))

class Row:
    ADDRBUS, DATABUS, INSTRUCTIONS = range(3)

class Pin:
    D0, D7 = 0, 7
    CLK, SYNC, RW = range(8,11)
    A0, A15 = 11, 26

class Ann:
    Addr, Data, Inst, Fetch, Operand, Read, Write = range(7)

class Cycles:
    Fetch, Op1, Op2, Read, Write = range(5)

class opcodes:
    opcodes = {
        0x00: ( 'BRK',  2),
        0x01: ( 'ORA',  2),
        0x02: ( 'NOP',  2),
        0x03: ( 'NOP',  1),
        0x04: ( 'TSB',  2),
        0x05: ( 'ORA',  2),
        0x06: ( 'ASL',  2),
        0x07: ( 'RMB0', 2),
        0x08: ( 'PHP',  1),
        0x09: ( 'ORA',  2),
        0x0A: ( 'ASL',  1),
        0x0B: ( 'NOP',  1),
        0x0C: ( 'TSB',  3),
        0x0D: ( 'ORA',  3),
        0x0E: ( 'ASL',  3),
        0x0F: ( 'BBR0', 3),
        0x10: ( 'BPL',  2),
        0x11: ( 'ORA',  2),
        0x12: ( 'ORA',  2),
        0x13: ( 'NOP',  1),
        0x14: ( 'TRB',  2),
        0x15: ( 'ORA',  2),
        0x16: ( 'ASL',  2),
        0x17: ( 'RMB1', 2),
        0x18: ( 'CLC',  1),
        0x19: ( 'ORA',  3),
        0x1A: ( 'INC',  1),
        0x1B: ( 'NOP',  1),
        0x1C: ( 'TRB',  3),
        0x1D: ( 'ORA',  3),
        0x1E: ( 'ASL',  3),
        0x1F: ( 'BBR1', 3),
        0x20: ( 'JSR',  3),
        0x21: ( 'AND',  2),
        0x22: ( 'NOP',  2),
        0x23: ( 'NOP',  1),
        0x24: ( 'BIT',  2),
        0x25: ( 'AND',  2),
        0x26: ( 'ROL',  2),
        0x27: ( 'RMB2', 2),
        0x28: ( 'PLP',  1),
        0x29: ( 'AND',  2),
        0x2A: ( 'ROL',  1),
        0x2B: ( 'NOP',  1),
        0x2C: ( 'BIT',  3),
        0x2D: ( 'AND',  3),
        0x2E: ( 'ROL',  3),
        0x2F: ( 'BBR2', 3),
        0x30: ( 'BMI',  2),
        0x31: ( 'AND',  2),
        0x32: ( 'AND',  2),
        0x33: ( 'NOP',  1),
        0x34: ( 'BIT',  2),
        0x35: ( 'AND',  2),
        0x36: ( 'ROL',  2),
        0x37: ( 'RMB3', 2),
        0x38: ( 'SEC',  1),
        0x39: ( 'AND',  3),
        0x3A: ( 'DEC',  1),
        0x3B: ( 'NOP',  1),
        0x3C: ( 'BIT',  3),
        0x3D: ( 'AND',  3),
        0x3E: ( 'ROL',  3),
        0x3F: ( 'BBR3', 3),
        0x40: ( 'RTI',  1),
        0x41: ( 'EOR',  2),
        0x42: ( 'NOP',  2),
        0x43: ( 'NOP',  1),
        0x44: ( 'NOP',  2),
        0x45: ( 'EOR',  2),
        0x46: ( 'LSR',  2),
        0x47: ( 'RMB4', 2),
        0x48: ( 'PHA',  1),
        0x49: ( 'EOR',  2),
        0x4A: ( 'LSR',  1),
        0x4B: ( 'NOP',  1),
        0x4C: ( 'JMP',  3),
        0x4D: ( 'EOR',  3),
        0x4E: ( 'LSR',  3),
        0x4F: ( 'BBR4', 3),
        0x50: ( 'BVC',  2),
        0x51: ( 'EOR',  2),
        0x52: ( 'EOR',  2),
        0x53: ( 'NOP',  1),
        0x54: ( 'NOP',  2),
        0x55: ( 'EOR',  2),
        0x56: ( 'LSR',  2),
        0x57: ( 'RMB5', 2),
        0x58: ( 'CLI',  1),
        0x59: ( 'EOR',  3),
        0x5A: ( 'PHY',  1),
        0x5B: ( 'NOP',  1),
        0x5C: ( 'NOP',  3),
        0x5D: ( 'EOR',  3),
        0x5E: ( 'LSR',  3),
        0x5F: ( 'BBR5', 3),
        0x60: ( 'RTS',  1),
        0x61: ( 'ADC',  2),
        0x62: ( 'NOP',  2),
        0x63: ( 'NOP',  1),
        0x64: ( 'STZ',  2),
        0x65: ( 'ADC',  2),
        0x66: ( 'ROR',  2),
        0x67: ( 'RMB6', 2),
        0x68: ( 'PLA',  1),
        0x69: ( 'ADC',  2),
        0x6A: ( 'ROR',  1),
        0x6B: ( 'NOP',  1),
        0x6C: ( 'JMP',  3),
        0x6D: ( 'ADC',  3),
        0x6E: ( 'ROR',  3),
        0x6F: ( 'BBR6', 3),
        0x70: ( 'BVS',  2),
        0x71: ( 'ADC',  2),
        0x72: ( 'ADC',  2),
        0x73: ( 'NOP',  1),
        0x74: ( 'STZ',  2),
        0x75: ( 'ADC',  2),
        0x76: ( 'ROR',  2),
        0x77: ( 'RMB7', 2),
        0x78: ( 'SEI',  1),
        0x79: ( 'ADC',  3),
        0x7A: ( 'PLY',  1),
        0x7B: ( 'NOP',  1),
        0x7C: ( 'JMP',  3),
        0x7D: ( 'ADC',  3),
        0x7E: ( 'ROR',  3),
        0x7F: ( 'BBR7', 3),
        0x80: ( 'BRA',  2),
        0x81: ( 'STA',  2),
        0x82: ( 'NOP',  2),
        0x83: ( 'NOP',  1),
        0x84: ( 'STY',  2),
        0x85: ( 'STA',  2),
        0x86: ( 'STX',  2),
        0x87: ( 'SMB0', 2),
        0x88: ( 'DEY',  1),
        0x89: ( 'BIT',  2),
        0x8A: ( 'TXA',  1),
        0x8B: ( 'NOP',  1),
        0x8C: ( 'STY',  3),
        0x8D: ( 'STA',  3),
        0x8E: ( 'STX',  3),
        0x8F: ( 'BBS0', 3),
        0x90: ( 'BCC',  2),
        0x91: ( 'STA',  2),
        0x92: ( 'STA',  2),
        0x93: ( 'NOP',  1),
        0x94: ( 'STY',  2),
        0x95: ( 'STA',  2),
        0x96: ( 'STX',  2),
        0x97: ( 'SMB1', 2),
        0x98: ( 'TYA',  1),
        0x99: ( 'STA',  3),
        0x9A: ( 'TXS',  1),
        0x9B: ( 'NOP',  1),
        0x9C: ( 'STZ',  3),
        0x9D: ( 'STA',  3),
        0x9E: ( 'STZ',  3),
        0x9F: ( 'BBS1', 3),
        0xA0: ( 'LDY',  2),
        0xA1: ( 'LDA',  2),
        0xA2: ( 'LDX',  2),
        0xA3: ( 'NOP',  1),
        0xA4: ( 'LDY',  2),
        0xA5: ( 'LDA',  2),
        0xA6: ( 'LDX',  2),
        0xA7: ( 'SMB2', 2),
        0xA8: ( 'TAY',  1),
        0xA9: ( 'LDA',  2),
        0xAA: ( 'TAX',  1),
        0xAB: ( 'NOP',  1),
        0xAC: ( 'LDY',  3),
        0xAD: ( 'LDA',  3),
        0xAE: ( 'LDX',  3),
        0xAF: ( 'BBS2', 3),
        0xB0: ( 'BCS',  2),
        0xB1: ( 'LDA',  2),
        0xB2: ( 'LDA',  2),
        0xB3: ( 'NOP',  1),
        0xB4: ( 'LDY',  2),
        0xB5: ( 'LDA',  2),
        0xB6: ( 'LDX',  2),
        0xB7: ( 'SMB3', 2),
        0xB8: ( 'CLV',  1),
        0xB9: ( 'LDA',  3),
        0xBA: ( 'TSX',  1),
        0xBB: ( 'NOP',  1),
        0xBC: ( 'LDY',  3),
        0xBD: ( 'LDA',  3),
        0xBE: ( 'LDX',  3),
        0xBF: ( 'BBS3', 3),
        0xC0: ( 'CPY',  2),
        0xC1: ( 'CMP',  2),
        0xC2: ( 'NOP',  2),
        0xC3: ( 'NOP',  1),
        0xC4: ( 'CPY',  2),
        0xC5: ( 'CMP',  2),
        0xC6: ( 'DEC',  2),
        0xC7: ( 'SMB4', 2),
        0xC8: ( 'INY',  1),
        0xC9: ( 'CMP',  2),
        0xCA: ( 'DEX',  1),
        0xCB: ( 'WAI',  1),
        0xCC: ( 'CPY',  3),
        0xCD: ( 'CMP',  3),
        0xCE: ( 'DEC',  3),
        0xCF: ( 'BBS4', 3),
        0xD0: ( 'BNE',  2),
        0xD1: ( 'CMP',  2),
        0xD2: ( 'CMP',  2),
        0xD3: ( 'NOP',  1),
        0xD4: ( 'NOP',  2),
        0xD5: ( 'CMP',  2),
        0xD6: ( 'DEC',  2),
        0xD7: ( 'SMB5', 2),
        0xD8: ( 'CLD',  1),
        0xD9: ( 'CMP',  3),
        0xDA: ( 'PHX',  1),
        0xDB: ( 'STP',  1),
        0xDC: ( 'NOP',  3),
        0xDD: ( 'CMP',  3),
        0xDE: ( 'DEC',  3),
        0xDF: ( 'BBS5', 3),
        0xE0: ( 'CPX',  2),
        0xE1: ( 'SBC',  2),
        0xE2: ( 'NOP',  2),
        0xE3: ( 'NOP',  1),
        0xE4: ( 'CPX',  2),
        0xE5: ( 'SBC',  2),
        0xE6: ( 'INC',  2),
        0xE7: ( 'SMB6', 2),
        0xE8: ( 'INX',  1),
        0xE9: ( 'SBC',  2),
        0xEA: ( 'NOP',  1),
        0xEB: ( 'NOP',  1),
        0xEC: ( 'CPX',  3),
        0xED: ( 'SBC',  3),
        0xEE: ( 'INC',  3),
        0xEF: ( 'BBS6', 3),
        0xF0: ( 'BEQ',  2),
        0xF1: ( 'SBC',  2),
        0xF2: ( 'SBC',  2),
        0xF3: ( 'NOP',  1),
        0xF4: ( 'NOP',  2),
        0xF5: ( 'SBC',  2),
        0xF6: ( 'INC',  2),
        0xF7: ( 'SMB7', 2),
        0xF8: ( 'SED',  1),
        0xF9: ( 'SBC',  3),
        0xFA: ( 'PLX',  1),
        0xFB: ( 'NOP',  1),
        0xFC: ( 'NOP',  3),
        0xFD: ( 'SBC',  3),
        0xFE: ( 'INC',  3),
        0xFF: ( 'BBS7', 3),
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
    ) + tuple({
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
        ('op', 'Operand'),
        ('read', 'Read'),
        ('write', 'Write')
    )
    annotation_rows = (
        ('addrbus', 'Address bus', (Ann.Addr,)),
        ('databus', 'Data bus', (Ann.Data,)),
        ('insname', 'Instructions', (Ann.Inst,)),
        ('cycles' , 'Machine Cycles', (Ann.Fetch, Ann.Operand, Ann.Read, Ann.Write))
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
            self.clk_block_ss = self.samplenum


            # Wait for rising clock edge
            # Data on the bus is valid during this time
            try:
                pins = self.wait({Pin.CLK : 'r'})
            except self.WaitException:
                break

            # read address and data on the bus and convert it into a single number
            self.bus_addr = reduce_bus(pins[Pin.A0:Pin.A15+1])
            self.bus_data = reduce_bus(pins[Pin.D0:Pin.D7+1])

            # if previous instruction already known
            if Pin.SYNC is 1 and self.sync_old is not 1 and self.inst_flag is 1:

                self.put(self.instr_start, self.clk_block_ss, self.out_ann, [Ann.Inst, opcodes.opcodes[self.bus_data]])
                self.inst_flag = 0
            #if no instruction before or last instruction done
            if Pin.SYNC is 1 and self.sync_old is not 1 and self.inst_flag is not 1:
                self.instr_start = self.clk_block_ss
                self.inst_flag = 1
                self.opcode = self.bus_data

            self.sync_old = Pin.SYNC

           
        pass
