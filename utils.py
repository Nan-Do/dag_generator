DEBUG = True


def get_chunks(seq, size, step=1):
    """
    Split a sequence into chunks of different sizes specified by
    size.

    seq -> The sequence to split.
    size -> Size of the chunks
    step -> How much to move on the original list before generating
    the next chunk.

    Similar to partition in clojure, it returns a generator for the
    chunks.
    """
    for x in xrange(0, len(seq) - size + step, step):
        yield seq[x:x+size]


