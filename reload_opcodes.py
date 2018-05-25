import ast

from copy import deepcopy


class ReloadOpcodes:
    def __find_block_position(self, block):
        for p1, level in enumerate(self.graph.treelevels):
            for p2, b in enumerate(level):
                if b == block:
                    return (p1, p2)

        return None

    def __apply_addition(self, block, node, index):
        position = self.__find_block_position(block)
        if position:
            level, block = position
            self.graph.treelevels[level][block].insert(index, node)

    def __apply_reordering(self, origin_block, destination_block):
        position = self.__find_block_position(origin_block)
        if position:
            level, block = position
            self.graph.treelevels[level][block] == destination_block

    def __process_opcodes(self):
        for operation in self.opcodes:
            opcode = operation[0]

            if opcode == 'REORDER_BLOCK':
                self.__apply_reordering(operation[1], operation[2])
            elif opcode == 'ADD_NODE':
                self.__apply_addition(operation[1], operation[2], int(operation[3]))

    def __init__(self, graph):
        self.graph = deepcopy(graph)
        self.opcodes = []
        with open('graph-{}-opcodes.txt'.format(graph.id), 'r') as f:
            for line in f:
                opcode = []
                temp_l = tuple(line[:-1].split(' '))
                opcode.append(temp_l[0])
                for x in temp_l[1:]:
                    try:
                        opcode.append(ast.literal_eval(x))
                    except ValueError:
                        opcode.append(x)
                self.opcodes.append(tuple(opcode))

        self.__process_opcodes()
