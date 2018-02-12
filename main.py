import argparse
from copy import deepcopy

from graph import Graph
from mutations import MutateGraph

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate random acyclic directed graphs")

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

    parser.add_argument("--image", dest="image",
                        type=str,
                        help="Generate an image of the generated graph")

    parser.add_argument("--dag", dest="dag",
                        type=str,
                        default="none",
                        help="Specify the density of the dag, if not specified it will generate a tree",
                        choices=["none", "sparse", "medium", "dense"])

    parser.add_argument("--swap", dest="swap",
                        type=int,
                        help="Mutation that swaps two nodes. (Repeated SWAP times)")

    parser.add_argument("--relabel", dest="relabel",
                        type=int,
                        help="Mutation that relabels one node with a label from outside the domain. (Repeated RELABEL times)")

    parser.add_argument("--spine", dest="spine",
                        type=int,
                        help="Mutation that reorders a the nodes in a path from the root to the leafs. (Repeated REORDER times)")

    parser.add_argument("--reorder", dest="reorder",
                        type=int,
                        help="Mutation that reorders the descecndants of a given node. (Repeated REORDER times)")

    parser.add_argument("--redundancy", dest="redundancy",
                        type=int,
                        help="Mutation that adds redudancy to the graph by duplicating nodes. (Repeated REDUNDANCY times)")

    parser.add_argument("--delete", dest="delete",
                        type=int,
                        help="Mutation that deletes a branch. (Repeated DELETE times)")

    parser.add_argument("--summary", dest="summary", action="store_true",
                        help="Print a summary of the mutations")

    args = parser.parse_args()

    mutate_graph = False
    if args.swap or args.relabel or args.spine or args.reorder or\
       args.redundancy or args.delete:
        mutate_graph = True

    # Generate the first graph
    g1 = Graph(args.size,
               args.outdegree,
               args.depth,
               args.dag)

    # Create a copy of the graph to mutate
    if mutate_graph:
        g2 = deepcopy(g1)
        m = MutateGraph(g2)

    # Do the mutations
    if args.swap:
        m.swap_nodes(args.swap)

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

    if args.image:
        g1.generate_dot(args.image)
        if mutate_graph:
            g2.generate_dot(args.image + '-mod')

    if args.summary and mutate_graph:
        m.print_mutations_summary()
