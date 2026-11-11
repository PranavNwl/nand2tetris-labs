import sys

COMP = {
 '0':'0101010','1':'0111111','-1':'0111010','D':'0001100','A':'0110000',
 '!D':'0001101','!A':'0110001','-D':'0001111','-A':'0110011',
 'D+1':'0011111','A+1':'0110111','D-1':'0001110','A-1':'0110010',
 'D+A':'0000010','D-A':'0010011','A-D':'0000111','D&A':'0000000','D|A':'0010101',
 'M':'1110000','!M':'1110001','-M':'1110011','M+1':'1110111','M-1':'1110010',
 'D+M':'1000010','D-M':'1010011','M-D':'1000111','D&M':'1000000','D|M':'1010101'}
DEST = {'':'000','M':'001','D':'010','MD':'011','A':'100','AM':'101','AD':'110','AMD':'111'}
JUMP = {'':'000','JGT':'001','JEQ':'010','JGE':'011','JLT':'100','JNE':'101','JLE':'110','JMP':'111'}


class AsmError(Exception):
    pass


def clean(line):
    return line.split('//')[0].replace(' ', '').strip()


def valid_symbol(sym):
    if not sym or sym[0].isdigit():
        return False
    return all(c.isalnum() or c in '_.$:' for c in sym)


def translate_c(l):
    if l.count('=') > 1 or l.count(';') > 1:
        raise AsmError('invalid instruction')
    dest, rest = l.split('=') if '=' in l else ('', l)
    comp, jump = rest.split(';') if ';' in rest else (rest, '')
    if comp not in COMP:
        raise AsmError(f"invalid instruction (unknown comp '{comp}')")
    if dest not in DEST:
        raise AsmError(f"invalid instruction (unknown dest '{dest}')")
    if jump not in JUMP:
        raise AsmError(f"invalid instruction (unknown jump '{jump}')")
    return '111' + COMP[comp] + DEST[dest] + JUMP[jump]


def assemble(path):
    symbols = {f'R{i}': i for i in range(16)}
    symbols.update({'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
                    'SCREEN': 16384, 'KBD': 24576})
    errors = []

    lines = [(n, clean(l)) for n, l in enumerate(open(path), start=1)]
    lines = [(n, l) for n, l in lines if l]

    # Pass 1: find labels
    code = []
    for n, l in lines:
        if l.startswith('('):
            name = l[1:-1]
            if not l.endswith(')') or not valid_symbol(name):
                errors.append(f"Line {n}: invalid label '{l}'")
            else:
                symbols[name] = len(code)
        else:
            code.append((n, l))

    # Pass 2: translate
    output = []
    next_var = 16
    for n, l in code:
        try:
            if l.startswith('@'):
                sym = l[1:]
                if sym.isdigit():
                    value = int(sym)
                    if value > 32767:
                        raise AsmError(f"invalid instruction (value {value} too large)")
                elif valid_symbol(sym):
                    if sym not in symbols:
                        symbols[sym] = next_var
                        next_var += 1
                    value = symbols[sym]
                else:
                    raise AsmError(f"invalid instruction (bad symbol '{sym}')")
                output.append('0' + format(value, '015b'))
            else:
                output.append(translate_c(l))
        except AsmError as e:
            errors.append(f"Line {n}: {e}")
    return output, errors


path = sys.argv[1]
output, errors = assemble(path)
if errors:
    for e in errors:
        print(e)
    print(f"{len(errors)} error(s). No .hack file written.")
    sys.exit(1)

out_path = path.replace('.asm', '.hack')
with open(out_path, 'w') as f:
    f.write('\n'.join(output) + '\n')
print('Wrote', out_path)