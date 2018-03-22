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

    parser.add_argument("--link-labels", dest="link_labels",
                        action="store_true",
                        help="Generate labels for the links of the generated" +
                             " graph")

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

    parser.add_argument("--swap-nodes", dest="swap_nodes",
                        type=int,
                        help="Mutation that swaps two nodes. (Repeated " +
                             "SWAP_NODES times)")

    parser.add_argument("--swap-link-nodes", dest="swap_link_nodes",
                        type=int,
                        help="Mutation that swaps a father and a child." +
                             " (Repeated SWAP_LINKS_NODES times)")

    parser.add_argument("--swap-link-labels", dest="swap_link_labels",
                        type=int,
                        help="Mutation that swaps the labels between two " +
                             " links (Repeated SWAP_LINKS_LABELS times)")

    parser.add_argument("--add", dest="add",
                        type=int,
                        help="Mutation that adds a node. (Repeated ADD times)")

    parser.add_argument("--rename-nodes", dest="rename_nodes",
                        type=int,
                        help="Mutation that renames a node with an non used " +
                             "identifier. (Repeated RENAME_NODE times)")

    parser.add_argument("--rename-links", dest="rename_links",
                        type=int,
                        help="Mutation that renames a link with another " +
                             "valid label. (Repeated RENAME_LINK times)")

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
    # if (args.load_graph and (args.size or args.outdegree or args.depth or
    #                          args.dag)):
    #     print "Error: Specified to generate the graph randomly and also" +\
    #           " to load it from a file"
    #     sys.exit(0)

    load_graph = None
    if args.load_graph:
        load_graph = args.load_graph
        
    output_directory = '.'
    if args.output_directory:
        output_directory = args.output_directory

    mutate_graph = False
    if args.swap_nodes or args.add or args.rename_nodes or args.spine or\
       args.reorder or args.redundancy or args.delete or args.rename_links or\
       args.swap_link_nodes or args.swap_link_labels:
        mutate_graph = True

    link_labels = False
    if args.link_labels:
        link_labels = True

    use_lowercase = True
    gc = GraphConfig(True,
                     False,
                     args.size,
                     args.outdegree,
                     args.depth,
                     args.dag,
                     use_lowercase,
                     link_labels,
                     None,
                     output_directory)
    if args.load_graph:
        gc = GraphConfig(False, True, None, None, None,
                         None, False, False, args.load_graph,
                         output_directory)

    # Generate the first graph
    g1 = Graph(gc)

    # Create a copy of the graph to mutate
    g2 = deepcopy(g1)
    m = MutateGraph(g2)

    # Do the mutations
    if args.swap_nodes:
        m.swap_nodes(args.swap_nodes)

    if args.swap_link_nodes:
        m.swap_link_nodes(args.swap_link_nodes)

    if args.add:
        m.add_node(args.add)

    if args.rename_nodes:
        m.rename_node(args.rename_nodes)

    if args.rename_links:
        m.rename_link_label(args.rename_links)

    if args.spine:
        m.reorder_path(args.spine)

    if args.reorder:
        m.reorder_block(args.reorder)

    if args.redundancy:
        m.redundancy(args.redundancy)

    if args.delete:
        m.delete_path(args.delete)

    if args.swap_link_labels:
        m.swap_link_labels(args.swap_link_labels)

    if args.dot:
        g1.generate_dot()
        if mutate_graph:
            g2.generate_dot()

    if args.summary:
        m.print_mutations_summary()
        m.store_mutation_opcodes_to_file()
        m.store_mutations_summary_to_file()

    if args.store_graph:
        g1.store_python_representation()
        g1.store_graph()
        g2.store_python_representation()


