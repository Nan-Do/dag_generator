from itertools import chain
from random import shuffle, choice, randint
from string import ascii_lowercase, ascii_uppercase, digits

from graph import Position, GraphLink
from utils import DEBUG


class MutateGraph:
    """
    This class performs mutations to a graph
    """
    def __generate_file_name(self):
        """
        Generate a file name using the data of the graph being mutated

        Auxiliary function
        """
        file_name = self.graph.output_directory

        if file_name[-1] != '/':
            file_name += '/'

        file_name += 'graph-' + self.graph.id

        return file_name

    def __mutation_string_generator(self):
        """
        Generate a string representation of the mutation opcodes.

        Auxiliary function
        """
        for mutation in self.mutations:
            if mutation[0] == "DUPLICATE":
                to_duplicate = mutation[0]
                to_remove = mutation[1]

                yield "Duplicating node: {} Removing: {}".format(to_duplicate,
                                                                 to_remove)
            elif mutation[0] == "ADD_NODE":
                block = mutation[1]
                node = mutation[2]
                position = mutation[3]

                yield "Adding node: {}, Block: {}, Position: {}".format(node,
                                                                        block,
                                                                        position)
            elif mutation[0] == "SWAP_NODES":
                source_node = mutation[1]
                dest_node = mutation[2]

                yield "Swapping nodes: {} with {}".format(source_node,
                                                          dest_node)
            elif mutation[0] == "RELABEL":
                node_to_be_changed = mutation[1]
                node_to_change_to = mutation[2]

                yield "Relabeling node: {}, {}".format(node_to_be_changed,
                                                       node_to_change_to)
            elif mutation[0] == "DELETE":
                orig_node = mutation[1]
                dest_node = mutation[2]

                yield "Removing link: {}, {}".format(orig_node,
                                                     dest_node)
            elif mutation[0] == "REORDER_PATH":
                nodes = mutation[1]
                reordered_branch = mutation[2]

                yield "Reordering path: {}, {}".format(nodes,
                                                       reordered_branch)
            elif mutation[0] == "REORDER_BLOCK":
                orig_block = mutation[1]
                ordered_block = mutation[2]

                yield "Reordering block: {}, {}".format(orig_block,
                                                        ordered_block)
            else:
                yield "UNKNOWN OPERATION: {}".format(mutation)

    def __compute_mutations_score(self):
        """
        Compute the expected score for the applied mutations.
        """
        score = 0

        for m in self.mutations:
            if m[0] == 'ADD_NODE':
                score += 1
            if m[0] == 'DELETE':
                score -= 1

        return score

    def __get_nodes_to_add(self, new_identifiers):
        """
        Generate a list of nodes ordered randomly that are not present in the
        current graph.

        new_identifiers -> In case all the possible identifies are taken
                           specify how many need to be generated.
        """
        nodes = self.graph.nodes

        # Check which identifiers have been used
        nodes_to_add = set(chain.from_iterable([list(ascii_lowercase),
                                                list(ascii_uppercase),
                                                list(digits)]))
        nodes_to_add.symmetric_difference_update(nodes)

        # In case there are no identifiers available generate new ones.
        if len(nodes_to_add) == 0:
            last = max(nodes)
            nodes_to_add = set(xrange(last+1, last+1+new_identifiers))

        nodes_to_add = list(nodes_to_add)
        shuffle(nodes_to_add)

        return nodes_to_add

    def add_node(self, times):
        """
        Mutation that adds a node to the current graph

        times -> How many relabelings we must perform.
        """
        treelevels = self.graph.treelevels
        nodes_to_add = self.__get_nodes_to_add(times)

        for _ in xrange(times):
            node = nodes_to_add.pop()
            level = randint(1, len(treelevels) - 1)
            block = randint(0, len(treelevels[level]) - 1)
            position = randint(0, len(treelevels[level][block]) - 1)

            if DEBUG:
                print "  Adding node ", node, "to block",\
                      treelevels[level][block], "at position", position

            self.mutations.append(("ADD_NODE",
                                   list(treelevels[level][block]),
                                   node,
                                   position))
            treelevels[level][block].insert(position, node)
            self.graph.nodes += (node,)

            # Update treelinks
            # Add the new link
            father = None
            link_index = 0
            new_treelinks = []
            for pos, link in enumerate(self.graph.treelinks):
                dest = link.dest
                if dest.level == level and dest.block == block:
                    if dest.position >= position:
                        father = link.orig
                        if dest.position == position:
                            link_index = pos

                        new_link = GraphLink(father,
                                             Position(level,
                                                      block,
                                                      dest.position + 1))
                        new_treelinks.append(new_link)
                        continue

                new_treelinks.append(link)

            new_link = GraphLink(father,
                                 Position(level,
                                          block,
                                          position))
            new_treelinks.insert(link_index, new_link)
            self.graph.treelinks = new_treelinks

    def swap_nodes(self, times):
        """
        Mutation that swaps two nodes from the current graph.

        times -> How many swaps we must perform.
        """
        nodes = list(self.graph.nodes)
        shuffle(nodes)

        treelevels = self.graph.treelevels

        if DEBUG:
            print "\nSwapping mutations:"

        if times > (len(nodes) / 2):
            print "Warning::Specfied more swappings than the highest " +\
                  "number possible for the current graph"
            times = len(nodes) / 2

        for x in xrange(times):
            source_node = nodes[x]
            dest_node = nodes[x]

            self.mutations.append(("SWAP_NODES", source_node, dest_node))
            if DEBUG:
                print "  Swapping nodes ", source_node, dest_node

            for level in treelevels:
                for block in level:
                    if source_node in block and dest_node in block:
                        a = block.index(source_node)
                        b = block.index(dest_node)
                        block[a], block[b] = block[b], block[a]
                    elif source_node in block:
                        index = block.index(source_node)
                        block[index] = dest_node
                    elif dest_node in block:
                        index = block.index(dest_node)
                        block[index] = source_node

    def swap_links(self, times):
        """
        Mutation that swaps the to nodes that share a father-child relationship.

        times -> How many swaps we must perform.
        """
        link_positions = range(0, len(self.graph.treelinks))
        shuffle(link_positions)

        if times > len(link_positions):
            print "Warning::Specifier a higher number than the " +\
                  "maximum number of swappings"
            times = len(link_positions)

        for x in xrange(times):
            link_position = link_positions[x]
            
            orig, dest = self.graph.treelinks[link_position]
            source_node = self.graph.treelevels[orig.level][orig.block][orig.position]
            dest_node = self.graph.treelevels[dest.level][dest.block][dest.position]

            self.mutations.append(("SWAP_NODES", source_node, dest_node))
            if DEBUG:
                print "  Swapping nodes ", source_node, dest_node

            orig_block = self.graph.treelevels[orig.level][orig.block]
            dest_block = self.graph.treelevels[dest.level][dest.block]
            
            orig_block[orig.position], dest_block[dest.position] =\
                dest_block[dest.position], orig_block[orig.position]

    def relabel_node(self, times):
        """
        Mutation that relabels a node whitin the graph.

        times -> How many relabelings we must perform.

        The mutation occurs changing one of the node identifiers with an
        identifier that has not been used. If all the identifiers have been
        used new identifiers as numbers will be generated.
        """
        treelevels = self.graph.treelevels

        if DEBUG:
            print "\nRelabeling mutations:"

        if times > len(self.graph.nodes):
            print 'Warning::Requesting more changes than nodes the graph ' +\
                  'contains'
            times = len(self.graph.nodes)

        nodes_to_add = self.__get_nodes_to_add(times)
        nodes_to_be_changed = list(self.graph.nodes)
        shuffle(nodes_to_be_changed)

        # Perform the relabelings
        for x in xrange(times):
            node_to_be_changed = nodes_to_be_changed[x]
            node_to_change_to = nodes_to_add[x]

            self.mutations.append(("RELABEL",
                                   node_to_be_changed,
                                   node_to_change_to))
            if DEBUG:
                print "Changing node:", node_to_be_changed,\
                      "for node", node_to_change_to

            for level in treelevels:
                    for block in level:
                        if node_to_be_changed in block:
                            index = block.index(node_to_be_changed)
                            block[index] = node_to_change_to

    def delete_path(self, times, start_from_root=False):
        """
        Mutation that deletes a path on the graph.

        times -> How many paths to remove.
        start_from_root -> Does the path need to start from the root node?
        """
        treelevels = self.graph.treelevels
        treelinks = self.graph.treelinks

        if not treelinks:
            print "Warning::No more branchs to delete"
            return

        orig_link = choice(treelinks)
        if start_from_root:
            root = Position(0, 0, 0)
            orig_link = choice(filter(lambda x: x.orig == root,
                                      treelinks))

        frontier = [orig_link]

        if DEBUG:
            print "Removing branch:"

        while frontier:
            link = frontier.pop()
            treelinks.remove(link)

            orig = link.orig
            dest = link.dest
            orig_node = treelevels[orig.level][orig.block][orig.position]
            dest_node = treelevels[dest.level][dest.block][dest.position]

            self.mutations.append(("DELETE", orig_node, dest_node))
            if DEBUG:
                print "Removing link from node ", orig_node, "to", dest_node

            # There is still a path that can reach the current dest node
            # no need to remove its descecndants
            if filter(lambda x: x.dest == dest, treelinks):
                continue

            # Get all the links that start on the dest node
            links = filter(lambda x: x.orig == dest, treelinks)

            frontier.extend(links)

    def reorder_path(self, start_from_root=True):
        """
        Mutation that reorders a path on the graph.

        times -> How many paths to reorder.
        start_from_root -> Does the path need to start from the root node?
        """
        treelevels = self.graph.treelevels
        treelinks = self.graph.treelinks
        orig_link = choice(treelinks)

        if start_from_root:
            root = Position(0, 0, 0)
            orig_link = choice(filter(lambda x: x.orig == root,
                                      treelinks))

        orig_node = treelevels[orig_link.orig.level]\
                              [orig_link.orig.block]\
                              [orig_link.orig.position]
        nodes = []
        nodes.append(orig_node)

        positions = [orig_link.orig]

        if DEBUG:
            print "Reordering a path:"

        frontier = [orig_link]
        while frontier:
            link = frontier.pop()

            dest = link.dest
            dest_node = treelevels[dest.level][dest.block][dest.position]
            nodes.append(dest_node)
            positions.append(dest)

            # Get all the links that start on the dest node
            links = filter(lambda x: x.orig == dest, treelinks)

            if links:
                link = choice(links)
                frontier.append(link)

        reordered_branch = list(nodes)
        shuffle(reordered_branch)

        self.mutations.append(('REORDER_PATH',
                               list(nodes),
                               reordered_branch))
        if DEBUG:
            print "Reordering path:", nodes, "to", reordered_branch

        for node, p in zip(reordered_branch, positions):
            level, block, position = p
            treelevels[level][block][position] = node

    def reorder_block(self, times):
        """
        Mutation that reorders the children of a node.

        times -> How many blocks do we have to reorders.
        """
        treelevels = self.graph.treelevels

        for _ in xrange(times):
            level = randint(1, len(treelevels) - 1)
            block = randint(0, len(treelevels[level]) - 1)

            orig_block = list(treelevels[level][block])
            shuffle(treelevels[level][block])

            self.mutations.append(('REORDER_BLOCK',
                                   orig_block,
                                   list(treelevels[level][block])))
            if DEBUG:
                print "Reordering block", orig_block, "reordered into", treelevels[level][block]

    def redundancy(self, times):
        """
        Mutation that relabels the identifier of a node with another existing
        identifier of the graph.

        times -> How many nodes do we have to copy.
        """
        treelevels = self.graph.treelevels

        for _ in xrange(times):
            nodes = chain.from_iterable(chain.from_iterable(treelevels))
            shuffle(nodes)
            to_duplicate = nodes[0]
            to_remove = nodes[1]

            self.mutations.append(("DUPLICATE", to_duplicate, to_remove))
            if DEBUG:
                print "Duplicating node:", to_duplicate, "Removing:", to_remove

            if len(to_duplicate) == 1:
                to_duplicate += '1'

            for level in treelevels:
                for block in level:
                    if to_remove in block:
                        index = block.index(to_remove)
                        block[index] = to_duplicate

    def print_mutations_summary(self):
        """
        Show a summary of the applied mutations.
        """
        SPACES = ' ' * 3
        print "Mutations for graph " + self.graph.id + ":"
        for s in self.__mutation_string_generator():
            print SPACES + s

        print
        print SPACES + "Score:", str(self.__compute_mutations_score())

    def store_mutations_summary_to_file(self):
        """
        Write the summary of the generated mutations into a file
        """
        file_name = self.__generate_file_name()
        with open(file_name + '-mutations.txt', 'w') as f:
            for s in self.__mutation_string_generator():
                f.write(s)
                f.write('\n')
            f.write("Score: " + str(self.__compute_mutations_score()))
            f.write('\n')
    
    def store_mutation_opcodes_to_file(self, field_separator=' '):
        """
        Store the opcodes for the generated mutations

        field_separator -> the separator for the fields.
        """
        file_name = self.__generate_file_name()
        with open(file_name + '-opcodes.txt', 'w') as f:
            for mutation in self.mutations:
                opcode = mutation[0]
                operands = []
                for op in mutation[1:]:
                    # Preprocess lists to remove the spaces
                    # string.translate can also be used to achieve the
                    # same effect but it is less portable
                    if isinstance(op, list):
                        r = ','.join(map(lambda x: "'" + x + "'" if
                                         isinstance(x, str) else str(x),
                                         op))
                        r = '[' + r + ']'
                        operands.append(r)
                    else:
                        operands.append(str(op))
                # operands = field_separator.join(map(str, mutation[1:]))
                operands = field_separator.join(operands)
                f.write(opcode + field_separator + operands + "\n")

    def __init__(self, graph):
        self.mutations = []
        self.graph = graph
        self.graph.mutated = True
