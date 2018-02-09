from itertools import chain
from random import shuffle, choice, randint
from string import ascii_lowercase, ascii_uppercase, digits

from graph import Position
from utils import DEBUG

class MutateGraph:
    """
    This class perform mutations to a graph
    """
    def swap_nodes(self, times):
        nodes = list(self.graph.nodes)
        shuffle(nodes)

        treelevels = self.graph.treelevels

        if DEBUG:
            print "\nSwapping mutations:"

        if times > (len(nodes) / 2):
            print "Warning::Specfied more swappings than the highest number possible for the current graph"
            times = len(nodes) / 2

        for _ in xrange(times):
            source_node = nodes.pop()
            dest_node = nodes.pop()

            self.mutations.append(("Swap", source_node, dest_node))
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
        nodes = self.graph.nodes
        treelevels = self.graph.treelevels
        if DEBUG:
            print "\nRelabeling mutations:"

        if times > len(nodes):
            print 'Warning::Requesting more changes than nodes the graph contains'
            times = len(nodes)

        nodes_to_add = set(chain.from_iterable([list(ascii_lowercase),
                                                list(ascii_uppercase),
                                                list(digits)]))
        nodes_to_add.symmetric_difference_update(nodes)

        if len(nodes_to_add) == 0:
            last = max(nodes)
            nodes_to_add = set(xrange(last+1, last+1+times))

        nodes_to_add = list(nodes_to_add)
        shuffle(nodes_to_add)
        nodes_to_be_changed = list(nodes)
        shuffle(nodes_to_be_changed)

        for _ in xrange(times):
            node_to_be_changed = nodes_to_be_changed.pop()
            node_to_change_to = nodes_to_add.pop()

            self.mutations.append(("Relabel", node_to_be_changed, node_to_change_to))
            print "Changing node:", node_to_be_changed, "for node", node_to_change_to
            for level in treelevels:
                    for block in level:
                        if node_to_be_changed in block:
                            index = block.index(node_to_be_changed)
                            block[index] = node_to_change_to

    def delete_path(self, times, start_from_root=False):
        treelevels = self.graph.treelevels
        treelinks = self.graph.treelinks

        if not treelinks:
            print "No more branchs to delete"
        orig_link = choice(treelinks)
        if start_from_root:
            root = Position(0, 0, 0)
            orig_link = choice(filter(lambda x: x.orig == root,
                                      treelinks))

        frontier = [orig_link]
        print "Removing branch:"
        while frontier:
            link = frontier.pop()
            treelinks.remove(link)

            orig = link.orig
            dest = link.dest
            orig_node = treelevels[orig.level][orig.block][orig.position]
            dest_node = treelevels[dest.level][dest.block][dest.position]

            self.mutations.append(("Delete", orig_node, dest_node))
            print "Removing link from node ", orig_node, "to", dest_node

            # There is still a path that can reach the current dest node
            # no need to remove its descecndants
            if filter(lambda x: x.dest == dest, treelinks):
                continue

            # Get all the links that start on the dest node
            links = filter(lambda x: x.orig == dest, treelinks)

            frontier.extend(links)

    def reorder_path(self, start_from_root=True):
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
        self.mutations.append(('Reordering Path', nodes, reordered_branch))
        print "Reordering path:", nodes, "to", reordered_branch

        for node, p in zip(reordered_branch, positions):
            level, block, position = p
            treelevels[level][block][position] = node

    def reorder_block(self, times):
        treelevels = self.graph.treelevels

        for _ in xrange(times):
            level = randint(1, len(treelevels) - 1)
            block = randint(0, len(treelevels[level]) - 1)

            orig_block = list(treelevels[level][block])
            print "Reordering block", treelevels[level][block],
            shuffle(treelevels[level][block])
            print "reordered into ", treelevels[level][block]
            self.mutations.append(('Reorder Block', orig_block, block))

    def redundancy(self, times):
        treelevels = self.graph.treelevels

        for _ in xrange(times):
            nodes = chain.from_iterable(chain.from_iterable(treelevels))
            shuffle(nodes)
            to_duplicate = nodes[0]
            to_remove = nodes[1]

            print "Duplicating node:", to_duplicate, "Removing:", to_remove

            if len(to_duplicate) == 1:
                to_duplicate += '1'

            for level in treelevels:
                for block in level:
                    if to_remove in block:
                        index = block.index(to_remove)
                        block[index] = to_duplicate

    def __init__(self, graph):
        self.mutations = []
        self.graph = graph
