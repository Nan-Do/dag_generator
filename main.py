import argparse
import sys

from copy import deepcopy

from graph import Graph, GraphConfig
from mutations import MutateGraph

if __name__ == '__main__':
    d = "Generate random acyclic directed graphs and produce mutations to " +\
        "it. The tool acts as a little virtual machine to produce and " +\
        "modify directed acyclic graphs"
    parser = argparse.ArgumentParser(description=d)

    parser.add_argument("--size", dest="size",
                        type=int,
                        default=25,
                        help="Choose the size of the graph (default 25)")

    parser.add_argument("--outdegree", dest="outdegree",
                        type=int,
                        default=3,
                        help="Choose the outdegree of the graph (default 3)")

    parser.add_argument("--depth", dest="depth",
                        type=int,
                        default=3,
                        help="Choose the depth of the graph (default 3)")

    parser.add_argument("--upper", dest="upper", action="store_true",
                        help="Use upper case instead lower case")

    parser.add_argument("--dot", dest="dot",
                        action="store_true",
                        help="Generate a dot file of the generated graph")

    parser.add_argument("--dag", dest="dag",
                        type=str,
                        default="none",
                        help="Specify the density of the dag, if not " +
                             "specified it will generate a tree",
                        choices=["none", "sparse", "medium", "dense"])

    parser.add_argument("--store-graph", dest="store_graph",
                        action="store_true",
                        help="Store the generated graph")

    parser.add_argument("--output-directory", dest="output_directory",
                        type=str,
                        help="Specify the directory for the generated files")

    parser.add_argument("--load-graph", dest="load_graph",
                        type=str,
                        help="Load the graph from a file")

    parser.add_argument("--swap", dest="swap",
                        type=int,
                        help="Mutation that swaps two nodes. (Repeated " +
                             "SWAP times)")

    parser.add_argument("--add", dest="add",
                        type=int,
                        help="Mutation that adds a node. (Repeated ADD times)")

    parser.add_argument("--relabel", dest="relabel",
                        type=int,
                        help="Mutation that relabels one node with a label " +
                             "from outside the domain. (Repeated RELABEL " +
                             "times)")

    parser.add_argument("--spine", dest="spine",
                        type=int,
                        help="Mutation that reorders a the nodes in a path " +
                             "from the root to the leafs. (Repeated REORDER " +
                             "times)")

    parser.add_argument("--reorder", dest="reorder",
                        type=int,
                        help="Mutation that reorders the descecndants of a " +
                             "given node. (Repeated REORDER times)")

    parser.add_argument("--redundancy", dest="redundancy",
                        type=int,
                        help="Mutation that adds redudancy to the graph by " +
                             "duplicating nodes. (Repeated REDUNDANCY times)")

    parser.add_argument("--delete", dest="delete",
                        type=int,
                        help="Mutation that deletes a branch. (Repeated " +
                             "DELETE times)")

    parser.add_argument("--summary", dest="summary", action="store_true",
                        help="Print a summary of the mutations")

    args = parser.parse_args()
    
    # Check there are no conflicts about how to generate the graph
    if (args.load_graph and (args.size or args.outdegree or args.depth or
                             args.dag)):
        print "Error: Specified to generate the graph randomly and also" +\
              " to load it from a file"
        sys.exit(0)

    load_graph = None
    if args.load_graph:
        load_graph = args.load_graph
        
    output_directory = '.'
    if args.output_directory:
        output_directory = args.output_directory

    mutate_graph = False
    if args.swap or args.add or args.relabel or args.spine or\
       args.reorder or args.redundancy or args.delete:
        mutate_graph = True

    use_lowercase = True
    gc = GraphConfig(True,
                     False,
                     args.size,
                     args.outdegree,
                     args.depth,
                     args.dag,
                     use_lowercase,
                     None,
                     output_directory)
    if args.load_graph:
        gc = GraphConfig(False, True, None, None, None,
                         None, False, args.load_graph,
                         output_directory)

    # Generate the first graph
    g1 = Graph(gc)

   # Create a copy of the graph to mutate
    if mutate_graph:
        g2 = deepcopy(g1)
        m = MutateGraph(g2)

    # Do the mutations
    if args.swap:
        m.swap_nodes(args.swap)

    if args.add:
        m.add_node(args.add)

    if args.relabel:
        m.relabel_node(args.relabel)

    if args.spine:
        m.reorder_path(args.spine)

    if args.reorder:
        m.reorder_block(args.reorder)

    if args.redundancy:
        m.redundancy(args.redundancy)

    if args.delete:
        m.delete_path(args.delete)

    if args.dot:
        g1.generate_dot()
        if mutate_graph:
            g2.generate_dot()

    if args.store_graph:
        g1.store_python_representation()
        g1.store_graph()
        if mutate_graph:
            g2.store_python_representation()
 
    if args.summary and mutate_graph:
        m.print_mutations_summary()
        m.store_mutations_to_file('mutations')

