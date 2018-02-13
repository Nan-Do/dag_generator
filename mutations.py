from itertools import chain
from random import shuffle, choice, randint
from string import ascii_lowercase, ascii_uppercase, digits

from graph import Position, GraphLink
from utils import DEBUG


class MutateGraph:
    """
    This class performs mutations to a graph
    """
    def __get_nodes_to_add(self, new_identifiers):
        """
        Generates a list of nodes ordered randomly that are not present in the
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

            # Update treelinks
            # Add the new link
            father = None
            link_index = 0
            new_treelinks = []
            for pos, link in enumerate(self.graph.treelinks):
                dest = link.dest
                if dest.level == level and dest.block == block:
                    if dest.position >= position:
                        if dest.position == position:
                            father = link.orig
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

        times -> How many relabelings we must perform.
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

        for _ in xrange(times):
            source_node = nodes.pop()
            dest_node = nodes.pop()

            self.mutations.append(("SWAP", source_node, dest_node))
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
        for _ in xrange(times):
            node_to_be_changed = nodes_to_be_changed.pop()
            node_to_change_to = nodes_to_add.pop()

            self.mutations.append(("RELABEL",
                                   node_to_be_changed,
                                   node_to_change_to))
            if DEBUG:
                print "Changing node:", node_to_be_changed, "for node", node_to_change_to

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
        SPACES = ' ' * 3
        s = ''
        print "Mutations:"
        for mutation in self.mutations:
            s = SPACES
            if mutation[0] == "DUPLICATE":
                to_duplicate = mutation[0]
                to_remove = mutation[1]

                s += "Duplicating node: {} Removing: {}".format(to_duplicate,
                                                                to_remove)
            elif mutation[0] == "ADD_NODE":
                block = mutation[1]
                node = mutation[2]
                position = mutation[3]

                s += "Adding node: {}, Block: {}, Position: {}".format(node,
                                                                       block,
                                                                       position)
            elif mutation[0] == "SWAP":
                source_node = mutation[1]
                dest_node = mutation[2]

                s += "Swapping nodes: {} with {}".format(source_node,
                                                         dest_node)
            elif mutation[0] == "RELABEL":
                node_to_be_changed = mutation[1]
                node_to_change_to = mutation[2]

                s += "Relabeling node: {}, {}".format(node_to_be_changed,
                                                      node_to_change_to)
            elif mutation[0] == "DELETE":
                orig_node = mutation[1]
                dest_node = mutation[2]

                s += "Removing link: {}, {}".format(orig_node,
                                                    dest_node)
            elif mutation[0] == "REORDER_PATH":
                nodes = mutation[1]
                reordered_branch = mutation[2]

                s += "Reordering path: {}, {}".format(nodes,
                                                      reordered_branch)
            elif mutation[0] == "REORDER_BLOCK":
                orig_block = mutation[1]
                ordered_block = mutation[2]

                s += "Reordering block: {}, {}".format(orig_block,
                                                       ordered_block)
            else:
                s += "UNKNOWN OPERATION: {}".format(SPACES,
                                                    mutation)

            print s

    def store_mutations_to_file(self, file_name="mutations"):
        file_name += ".txt"
        with open(file_name, 'w') as f:
            for mutation in self.mutations:
                opcode = mutation[0]
                operands = ':'.join(map(str, mutation[1:]))
                f.write(opcode + ":" + operands + "\n")

    def __init__(self, graph):
        self.mutations = []
        self.graph = graph
