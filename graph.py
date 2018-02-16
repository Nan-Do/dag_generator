from collections import defaultdict, namedtuple
from itertools import chain
from random import choice, shuffle, normalvariate, randint
from string import ascii_lowercase, ascii_uppercase, digits

import sys
import ast

from utils import DEBUG, get_chunks, random_id_generator


GraphConfig = namedtuple("GraphConfig", ["populate_randomly",
                                         "from_file",
                                         "size",
                                         "outdegree",
                                         "depth",
                                         "dag_density",
                                         "use_lowercase",
                                         "file_name",
                                         "output_directory"])

"""
Datatypes to represent the links of the graph, a position is a tuple of three
element in which the first element represents the level of the graph, the
second element represents the  block inside the level and the third one the
position inside the block.
A GraphLink is a tuple of two Positions the first one being the origin of the
link and the second the end of the link.
"""
Position = namedtuple('Position', ['level', 'block', 'position'])
GraphLink = namedtuple('GraphLink', ['orig', 'dest'])


class Graph:
    def __find_root(self):
        """
        Find the root of the graph.

        In the original graph the root is stored at the firt element of the
        self.nodes tuple, but after the mutations this can not be warrantied
        so this auxiliary function finds the root for the python
        representation.
        """
        all_nodes = set()
        children = set()
        for link in self.treelinks:
            orig, dest = link
            orig_node = self.treelevels[orig.level][orig.block][orig.position]
            dest_node = self.treelevels[dest.level][dest.block][dest.position]
            
            all_nodes.add(orig_node)
            all_nodes.add(dest_node)
            children.add(dest_node)

        root = all_nodes.difference(children).pop()
        return root
            
    def __generate_file_name(self, ext, append_before_ext=''):
        """
        Generate a file name with extesion ext.

        It will take into account the output directory specified at the 
        construction of the graph.
        """
        file_name = self.output_directory

        if file_name[-1] != '/':
            file_name += '/'
        file_name += "graph-" + self.id

        if self.mutated:
            file_name += "-mod"

        if append_before_ext:
            file_name += append_before_ext

        file_name += '.' + ext

        return file_name

    def __generate_pool_nodes(self, size, lower=True):
        """
        Generate a pool of elements that will be used as a nodes for the graph.

        size -> The size of the pool.
        lower -> Use lower or upper case letters for the pool.

        Returns a list.
        """
        if lower:
            letters = list(ascii_lowercase)
        else:
            letters = list(ascii_uppercase)

        if size <= len(letters):
            return letters
        elif size <= len(letters) + len(digits):
            return letters + list(digits)
        else:
            return range(1, size)

    def __generate_nodelists(self, nodes, num_lists, average_size, dispersion=1):
        """
        Generate lists of nodes.

        nodes -> The pool from which we extract the nodes of the graph.
        num_lists -> The total number of lists to generate.
        average_size -> The average size of the lists to generate.
        dispersion -> The dispersion of the generated lists.

        Returns a list of lists.
        Average_size and dispersion are used to characterize a normal distribution.
        This version is better to honor the condition that given an average size
        all the nodes with descecndants will have at most average size
        descecndants.
        """
        result = []
        pool = [x for x in nodes]
        shuffle(pool)

        total = 0
        for _ in xrange(num_lists):
            l = []
            x = int(normalvariate(average_size, dispersion))
            if x == 0:
                x = 1
            total += x
            for _ in xrange(x):
                if len(pool):
                    l.append(pool.pop())
                else:
                    break
            if len(l):
                result.append(l)
        return result

    # Deprecated method
    def __generate_nodelists2(self, nodes, average_size, dispersion=1):
        """
        Generate lists of nodes.

        nodes -> The pool from which we extract the nodes of the graph.
        average_size -> The average size of the lists to generate.
        dispersion -> The dispersion of the generated lists.

        Returns a list of lists.
        Generates lists until it consumes the whole pool.
        Average_size and dispersion are used to characterize a normal distribution.
        """
        result = []
        pool = [x for x in nodes]
        shuffle(pool)

        total = 0
        while len(pool):
            l = []
            x = int(normalvariate(average_size, dispersion))
            if x == 0:
                x = 1
            total += x
            for _ in xrange(x):
                if len(pool):
                    l.append(pool.pop())
            if len(l):
                result.append(l)
        return result

    def __generate_treelevels(self, root, nodelists, depth):
        """
        Generate the levels of the the tree using the nodelists.

        root -> root of the tree.
        nodelists -> A list of lists containing nodes.
        depth -> The depth of the tree

        Return a list of lists.
        """
        res = [[[root]], [nodelists[0]]]

        if depth <= 2:
            depth = 3

        lists_per_level = (len(nodelists) - 1) / (depth - 2)
        if lists_per_level <= 0:
            print "Warning::The specified depth is too big"
            lists_per_level = 1

        return res + list(get_chunks(nodelists[1:],
                                     lists_per_level,
                                     lists_per_level))

    def __normalize_treelevels(self):
        """
        Normalize the treelevels so they can be used to generate the tree without
        problems.

        The normalized treelevels must fulfill the condition that at any given
        level the number of nodes of that level must be at least equal (or higher)
        than the number of blocks of the next level. With the exepction of the
        root.
        """
        root = self.treelevels.pop(0)

        while True:
            modified = False
            for x, y in get_chunks(self.treelevels, 2, 1):
                if len(list(chain.from_iterable(x))) < len(y):
                    modified = True
                    # Find the smallest block of y and move it
                    # to the previous level
                    position = 0
                    min_value = float('inf')
                    for pos, value in enumerate(map(len, y)):
                        if min_value < value:
                            position = pos

                    x.append(y[position])
                    y.pop(position)

            if not modified:
                break

        self.treelevels.insert(0, root)

    def __generate_treelinks(self):
        """
        Generate links for the current graph that create a tree.

        This function generates the tree_links that will populate
        the links of the grapg. The class works in an incremental
        fashion, first the links to create a graph are generated
        and then the tree is turned into a DAG.
        """
        tree_links = []

        # Process the root
        root = Position(0, 0, 0)
        for block, b in enumerate(self.treelevels[1]):
            for position, x in enumerate(b):
                dest = Position(1, block, position)
                tree_links.append(GraphLink(root, dest))

        for level, (x, y) in enumerate(get_chunks(self.treelevels[1:], 2),
                                       start=1):
            election_positions = []
            for block, b in enumerate(x):
                for position, _ in enumerate(b):
                    election_positions.append(Position(level, block, position))
            shuffle(election_positions)

            for dest_block, block in enumerate(y):
                if not election_positions:
                    print "Error::The tree levels are not normalized"
                    sys.exit(0)

                orig_position = election_positions.pop()
                for dest_position, node in enumerate(block):
                    dest_position = Position(level + 1,
                                             dest_block,
                                             dest_position)
                    tree_links.append(GraphLink(orig_position,
                                                dest_position))

        return tree_links

    def __generate_dag(self, num_of_links):
        """
        Generate the neccesary num_of_links to transform a tree into a dag.

        num_of_links -> The number of links to add to the tree.

        This method must be called after the __generate_links methods which
        is the one in charge to generate the required links to create a tree.
        After that function has been created this one adds num_of_links links to
        generate a DAG
        """
        total = 0
        while num_of_links > 0:
            total += 1
            if total == 100:
                print "Unable to generate a DAG using the current tree"
                return
            # Get the source node
            source_level = randint(0, len(self.treelevels) - 2)
            source_block = randint(0, len(self.treelevels[source_level]) - 1)
            source_position = randint(0, len(self.treelevels[source_level][source_block]) - 1)

            # Get the destination node
            dest_level = randint(source_level + 1, len(self.treelevels) - 1)
            dest_block = randint(0, len(self.treelevels[dest_level]) - 1)
            dest_position = randint(0, len(self.treelevels[dest_level][dest_block]) - 1)

            # if dest_level == source_level + 1:
            #     continue

            graph_link = GraphLink(Position(source_level,
                                            source_block,
                                            source_position),
                                   Position(dest_level,
                                            dest_block,
                                            dest_position))
            # Check that the link doestn't exist already
            if graph_link in self.treelinks:
                continue

            self.treelinks.append(graph_link)
            num_of_links -= 1

    def generate_dot(self):
        """
        Generate the dot representation for the graph and store it into a file
        """
        file_name = self.__generate_file_name('dot')

        with open(file_name, 'w') as f:
            f.write('strict digraph {\n')
            for link in self.treelinks:
                orig_position, dest_position = link

                level, block, position = orig_position
                orig_node = self.treelevels[level][block][position]

                level, block, position = dest_position
                dest_node = self.treelevels[level][block][position]

                f.write('\t{} -> {};\n'.format(orig_node,
                                               dest_node))
            f.write('}')

    def store_graph(self):
        """
        Store the representation of the graph into a file.

        This function stores a convinient representation of the graph
        so it can be reloaded later.
        """
        file_name = self.__generate_file_name('txt', '-representation')

        with open(file_name, "w") as f:
            f.write('Graph {\n')
            f.write('\tId: ')
            f.write(str(self.id))
            f.write('\n')
            f.write('\tNodes: ')
            f.write(str(self.nodes))
            f.write('\n')
            f.write('\tLevels: ')
            f.write(str(self.treelevels))
            f.write('\n')
            f.write('\tLinks: ')
            links_str = ';'.join(map(lambda x: '({},{},{})|({},{},{})'.format(x.orig.level,
                                                                              x.orig.block,
                                                                              x.orig.position,
                                                                              x.dest.level,
                                                                              x.dest.block,
                                                                              x.dest.position),
                                     self.treelinks))
            f.write(links_str)
            f.write('\n')
            f.write('}')

    def to_python_dict(self):
        """
        Generate a python dictionary representation for the graph

        Returns a default dict containing the representation of the graph
        as adjacency lists.
        """
        g = defaultdict(list)

        for (orig_position, dest_position) in self.treelinks:
            level, block, position = orig_position
            orig_node = self.treelevels[level][block][position]

            level, block, position = dest_position
            dest_node = self.treelevels[level][block][position]

            g[orig_node].append(dest_node)

            # Add the leafs
            for node in set(self.nodes).difference(g):
                g[node]

        return g

    def store_python_representation(self):
        """
        Store the graph as a python dictionary.
        """
        file_name = self.__generate_file_name('py')
        d = self.to_python_dict()

        with open(file_name, 'w') as f:
            f.write("root = '" + self.__find_root() + "'")
            f.write('\n')
            f.write('links = {\n')
            for k in d:
                f.write("\t '{}': {},\n".format(k, d[k]))
            f.write('\t}\n')

    def print_graph(self):
        print self.treelevels
        print self.treelinks

    def __load_from_file(self, file_name):
        """
        Constructor to load the graph from a file.
        """
        nodes = levels = links = g_id = None
        self.treelinks = list()

        with open(file_name, 'r') as f:
            f.readline()
            g_id = f.readline().split(':')[1].strip()
            nodes = f.readline().split(':')[1].strip()
            levels = f.readline().split(':')[1].strip()
            links = f.readline().split(':')[1].strip()

        self.id = int(g_id)
        self.nodes = ast.literal_eval(nodes)
        self.treelevels = ast.literal_eval(levels)
        for link in links.split(';'):
            orig, dest = link.split('|')
            orig = map(int, orig[1:-1].split(','))
            dest = map(int, dest[1:-1].split(','))
            l = GraphLink(Position(orig[0],
                                   orig[1],
                                   orig[2]),
                          Position(dest[0],
                                   dest[1],
                                   dest[2]))
            self.treelinks.append(l)

    def __populate_randomly(self, TreeConfig):
        """
        Constructor to build the graph using the 
        specified parameters.
        """
        # Check the TreeConfig
        size = TreeConfig.size
        outdegree = TreeConfig.outdegree
        depth = TreeConfig.depth
        dag_density = TreeConfig.dag_density
        use_lowercase = TreeConfig.use_lowercase

        pool_of_nodes = self.__generate_pool_nodes(size, use_lowercase)

        # Select the root
        root = choice(pool_of_nodes)
        pool_of_nodes.remove(root)

        # Stablish the number of lists for each graph
        num_of_lists = (size - 1) / outdegree

        lists_of_nodes = self.__generate_nodelists(pool_of_nodes,
                                                   num_of_lists,
                                                   outdegree)
        self.nodes = (root,) + tuple(chain.from_iterable(lists_of_nodes))
        if DEBUG:
            number_of_nodes = len(self.nodes)
            print "Number of nodes for the graph:", number_of_nodes, '/', size
            print

        self.treelevels = self.__generate_treelevels(root,
                                                     lists_of_nodes,
                                                     depth)

        if DEBUG:
            print "Generated Lists:"
            for pos, x in enumerate(self.treelevels):
                print '  ', pos, x
            print
        self.__normalize_treelevels()

        if DEBUG:
            print "Normalized Lists:"
            for pos, x in enumerate(self.treelevels):
                print '  ', pos, x
            print

        self.treelinks = self.__generate_treelinks()

        num_of_dag_links = 0
        if dag_density == "sparse":
            num_of_dag_links = len(self.treelevels) / 2
        elif dag_density == "medium":
            num_of_dag_links = len(self.treelevels)
        else:
            num_of_dag_links = len(self.treelevels) * 2

        if dag_density != "none":
            self.__generate_dag(num_of_dag_links)

    def __init__(self, GraphConfig):
        # Data to to represent the graph
        self.nodes = self.treelevels = self.treelinks = self.id = None
        self.output_directory = GraphConfig.output_directory
        # If you copy the graph (with deepcopy) to be mutated set this
        # variable to True to generate the filenames correctly
        self.mutated = False

        # Choose the way to build the graph
        if GraphConfig.populate_randomly:
            self.id = random_id_generator(4)
            self.__populate_randomly(GraphConfig)
        elif GraphConfig.from_file:
            self.__load_from_file(GraphConfig.file_name)
        else:
            raise ValueError("Unknown constructor method for the Graph")
